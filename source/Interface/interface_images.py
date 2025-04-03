from PIL import ImageTk
import cv2
import numpy as np

from containers import ContRecording
from image_processing import cvimage_to_tkimage, resize_image_to_fit, draw_gaze_circle
from video import Video
from resources import Resources
from homography import perspective_map


class InterfaceImages:
    image_raw:ImageTk.PhotoImage = None
    image_gazemapped:ImageTk.PhotoImage = None
    image_perspective:ImageTk.PhotoImage = None
    image_static:ImageTk.PhotoImage = None

    index_raw_current = -1
    frame_raw = None
    frame_raw_scaled = None
    frame_raw_scale_factor = 0

    reference_image = None
    reference_image_scaled = None
    reference_image_scale_factor = 0

    field_image = None

    index_static_current = -1
    frame_static = None
    frame_static_scaled = None
    frame_static_scale_factor = 0

    index = 0 # Current index in export data
    t = 0 # Percentage between current index and next index
    start_time_video_raw = 0
    start_time_video_static = 0

    
    def __init__(self):
        self.timestamp_current = -1
        self.size_current = (-1, -1)
        self.active_recording:ContRecording = None
        self.videoWorld:Video
        self.videoField:Video
        self.resources = Resources()
    

    def set_recording(self, recording:ContRecording, resources:Resources):
        self.timestamp_current = -1
        self.index = 0
        self.index_static_current = -1
        self.size_current = (-1, -1)
        if (self.active_recording is not None):
            self.videoWorld.destroy()
        self.active_recording = recording
        self.videoWorld = Video(recording.paths['VideoWorld'])
        self.videoField = Video(recording.paths['VideoField'], 1)
        self.reference_image = recording.export.reference.image
        self.w, self.h = recording.export.reference_dimensions
        self.field = resources.fields[recording.export.reference.field]
        self.field_image = self.field.image
        self.image_static = None
        self.data = recording.export.data
        self.calculate_aspect()


    def get_images(self, timestamp:int, size:tuple[int, int]):
        if (timestamp < self.timestamp_current):
            self.index = 0
        timestamp_changed = timestamp != self.timestamp_current
        size_changed = size != self.size_current
        self.timestamp_current = timestamp
        self.size_current = size

        frame_raw_changed = False
        frame_raw_scaled_changed = False
        frame_static_changed = False
        frame_static_scaled_changed = False

        # Set size
        if (size_changed):
            self.set_scale_from_aspect()

        # Find moment in export
        timestamp_raw = timestamp + self.start_time_video_raw
        if (timestamp_changed):
            while self.index < len(self.data) - 1:
                if self.data[self.index + 1]['Timestamp'] > timestamp_raw:
                    break
                self.index += 1
            self.index = min(self.index, len(self.data) - 2)
            a = self.data[self.index]['Timestamp']
            b = self.data[self.index + 1]['Timestamp']
            self.t = max(min((timestamp_raw - a) / (b - a), 1), 0)

        # Raw video image
        index_raw = self.videoWorld.get_index_at_timestamp(timestamp_raw)
        if (index_raw != self.index_raw_current):
            self.index_raw_current = index_raw
            self.frame_raw = self.videoWorld.get_frame_at_index(index_raw)
            frame_raw_changed = True
        if (size_changed or frame_raw_changed):
            self.frame_raw_scaled, self.frame_raw_scale_factor = resize_image_to_fit(self.frame_raw, (self.scale * self.raw_aspect, self.scale))
            frame_raw_scaled_changed = True
        if (frame_raw_scaled_changed or timestamp_changed):
            position = self.get_export_position('Interpolated Gaze X', 'Interpolated Gaze Y')
            modify_position = lambda p: (p[0] * self.frame_raw_scale_factor, p[1] * self.frame_raw_scale_factor)
            frame_raw_final = self.add_gaze_circle(self.frame_raw_scaled.copy(), position, modify_position)
            self.image_raw = cvimage_to_tkimage(frame_raw_final)

        # Gazemapped image
        if (size_changed):
            self.reference_image_scaled, _ = resize_image_to_fit(self.reference_image, (self.scale, self.scale))
            self.reference_image_height, self.reference_image_width = self.reference_image_scaled.shape[:2]
        if (timestamp_changed or size_changed):
            position = self.get_export_position('Mapped Gaze X', 'Mapped Gaze Y')
            modify_position = lambda p: (p[0] / self.w * self.reference_image_width, p[1] / self.h * self.reference_image_height)
            reference_image_final = self.add_gaze_circle(self.reference_image_scaled.copy(), position, modify_position)
            self.image_gazemapped = cvimage_to_tkimage(reference_image_final)

        # Static video image
        if self.videoField.ok:
            index_static = self.videoField.get_index_at_timestamp(timestamp + self.start_time_video_static)
            if (index_static != self.index_static_current):
                self.index_static_current = index_static
                self.frame_static = self.videoField.get_frame_at_index(index_static)
                frame_static_changed = True
            if (size_changed or frame_static_changed):
                self.frame_static_scaled, self.frame_static_scale_factor = resize_image_to_fit(self.frame_static, (self.scale * self.static_aspect, self.scale))
                frame_static_scaled_changed = True
            if (frame_static_scaled_changed or timestamp_changed):
                # TODO: Add ball locations
                self.image_static = cvimage_to_tkimage(self.frame_static_scaled)
        
        # Perspective image
        if (timestamp_changed or size_changed):
            field_image_scaled, self.field_image_scale_factor = resize_image_to_fit(self.field_image, (self.scale, self.scale))
            position = self.get_export_position('Perspective Gaze X', 'Perspective Gaze Y')
            field_image_final = self.add_gaze_circle(field_image_scaled, position, self.map_to_field)
            self.image_perspective = cvimage_to_tkimage(field_image_final)

        return (self.image_raw, self.image_gazemapped, self.image_perspective, self.image_static)
    

    def calculate_aspect(self):
        g_height, g_width = self.reference_image.shape[:2]
        p_height, p_width = self.field_image.shape[:2]

        self.raw_aspect = self.videoWorld.width / self.videoWorld.height
        self.gazemapped_aspect = g_width / g_height
        self.perspective_aspect = p_width / p_height
        if self.videoField.ok:
            self.static_aspect = self.videoField.width / self.videoField.height
        else:
            self.static_aspect = 0

        self.width_aspect = self.raw_aspect + self.gazemapped_aspect + self.perspective_aspect + self.static_aspect
    

    def set_scale_from_aspect(self):
        width, height = self.size_current[0], self.size_current[1]
        self.scale = min(width / self.width_aspect, height)
    
    
    def map_to_field(self, p):
        p_mapped = perspective_map(self.field.H_inv_field, p)
        return tuple(map(lambda x: x * self.field_image_scale_factor, p_mapped))
    

    def get_export_position(self, x_param, y_param):
        a_x = self.data[self.index][x_param]
        a_y = self.data[self.index][y_param]
        b_x = self.data[self.index + 1][x_param]
        b_y = self.data[self.index + 1][y_param]
        if (b_x is None or b_y is None or self.t == 0):
            return (a_x, a_y)
        if (a_x is None or a_y is None or self.t == 1):
            return (b_x, b_y)
        return (a_x + (b_x - a_x) * self.t, a_y + (b_y - a_y) * self.t)
    

    def add_gaze_circle(self, img:np.ndarray, position, modify_position):
        img_with_circle = img.copy()
        if (position[0] is not None and position[1] is not None):
            x, y = modify_position(position)
            draw_gaze_circle(img_with_circle, (x, y))
        return img_with_circle