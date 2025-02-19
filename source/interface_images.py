from PIL import ImageTk, Image

from containers import ContRecording
from image_processing import cvimage_to_tkimage, resize_image_to_fit, draw_gaze_circle
from video import Video


class InterfaceImages:
    image_raw:ImageTk.PhotoImage = None
    image_gazemapped:ImageTk.PhotoImage = None

    index_raw_current = -1
    frame_raw = None
    frame_raw_scaled = None
    frame_raw_scale_factor = 0

    reference_image = None
    reference_image_scaled = None
    reference_image_scale_factor = 0

    index = 0 # Current index in export data
    t = 0 # Percentage between current index and next index

    
    def __init__(self):
        self.timestamp_current = -1
        self.size_current = (-1, -1)
        self.active_recording:ContRecording = None
        self.video:Video
    

    def set_recording(self, recording:ContRecording):
        if (self.active_recording is not None):
            self.video.destroy()
        self.active_recording = recording
        self.video = Video(recording.paths['Video'])
        self.reference_image = recording.export.reference.image
        self.w, self.h = recording.export.reference_dimensions
        self.data = recording.export.data


    def get_images(self, timestamp:int, size:tuple[int, int]):
        if (timestamp < self.timestamp_current):
            self.index = 0
        timestamp_changed = timestamp != self.timestamp_current
        size_changed = size != self.size_current
        self.timestamp_current = timestamp
        self.size_current = size
        width, height = size[0] / 5, size[1]

        frame_raw_changed = False
        frame_raw_scaled_changed = False

        # Find moment in export
        if (timestamp_changed):
            while self.index < len(self.data) - 1:
                if self.data[self.index + 1]['Timestamp'] > timestamp:
                    break
                self.index += 1
            a = self.data[self.index]['Timestamp']
            b = self.data[self.index + 1]['Timestamp']
            self.t = max(min((timestamp - a) / (b - a), 1), 0)

        # Raw image
        index_raw = self.video.get_index_at_timestamp(timestamp)
        if (index_raw != self.index_raw_current):
            self.index_current = index_raw
            self.frame_raw = self.video.get_frame_at_index(index_raw)
            frame_raw_changed = True
        if (size_changed or frame_raw_changed):
            self.frame_raw_scaled, self.frame_raw_scale_factor = resize_image_to_fit(self.frame_raw, (width * 2, height))
            frame_raw_scaled_changed = True
        if (frame_raw_scaled_changed or timestamp_changed):
            position = self.get_export_position('Interpolated Gaze X', 'Interpolated Gaze Y')
            modify_position = lambda p: (p[0] * self.frame_raw_scale_factor, p[1] * self.frame_raw_scale_factor)
            frame_raw_final = self.copy_image_with_circle(self.frame_raw_scaled, position, modify_position)
            self.image_raw = cvimage_to_tkimage(frame_raw_final)

        # Gazemapped image
        if (size_changed):
            self.reference_image_scaled, _ = resize_image_to_fit(self.reference_image, (width, height))
            self.reference_image_height, self.reference_image_width = self.reference_image_scaled.shape[:2]
        if (timestamp_changed or size_changed):
            position = self.get_export_position('Mapped Gaze X', 'Mapped Gaze Y')
            modify_position = lambda p: (p[0] / self.w * self.reference_image_width, p[1] / self.h * self.reference_image_height)
            reference_image_final = self.copy_image_with_circle(self.reference_image_scaled, position, modify_position)
            self.image_gazemapped = cvimage_to_tkimage(reference_image_final)

        return (self.image_raw, self.image_gazemapped)
    

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
    

    def copy_image_with_circle(self, img, position, modify_position):
        img_with_circle = img.copy()
        if (position[0] is not None and position[1] is not None):
            x, y = modify_position(position)
            draw_gaze_circle(img_with_circle, (x, y))
        return img_with_circle
        