from PIL import ImageTk, Image

from containers import ContRecording
from image_processing import cvimage_to_tkimage, resize_image_to_fit
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


    def get_images(self, timestamp:int, size:tuple[int, int]):
        timestamp_changed = timestamp != self.timestamp_current
        size_changed = size != self.size_current
        self.timestamp_current = timestamp
        self.size_current = size
        width, height = size[0] / 5, size[1]

        frame_raw_changed = False
        frame_raw_scaled_changed = False

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
            self.image_raw = cvimage_to_tkimage(self.frame_raw_scaled)


        # Gazemapped image
        if (size_changed):
            self.reference_image_scaled, self.reference_image_scale_factor = resize_image_to_fit(self.reference_image, (width, height))
        if (timestamp_changed or size_changed):
            self.image_gazemapped = cvimage_to_tkimage(self.reference_image_scaled)

        return (self.image_raw, self.image_gazemapped)