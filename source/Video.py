import cv2


class Video:
    def __init__(self, path):
        self.cap = cv2.VideoCapture(path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
    

    def get_index_at_timestamp(self, timestamp:int):
        index = int((timestamp / 1000) * self.fps)
        return min(index, self.frame_count - 1)
    

    def get_frame_at_index(self, index:int):
        if (not self.cap.isOpened()):
            return None
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, index)
        success, frame = self.cap.read()
        return frame if success else None
    

    def destroy(self):
        self.cap.release()