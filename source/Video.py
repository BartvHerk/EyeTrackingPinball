import cv2


class Video:
    def __init__(self, path, rotate=0): # 1 = 90, -1 = -90, 2 = 180
        self.ok = False
        if path == "":
            return
        self.cap = cv2.VideoCapture(path)
        self.ok = self.cap.isOpened()
        if not self.ok:
            return
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frame_duration = 1000 / self.fps
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = (self.frame_count / self.fps) * 1000
        flip_aspect = rotate % 2 == 1
        w, h = cv2.CAP_PROP_FRAME_WIDTH, cv2.CAP_PROP_FRAME_HEIGHT
        if flip_aspect:
            w, h = h, w
        self.width = int(self.cap.get(w))
        self.height = int(self.cap.get(h))
        match rotate:
            case 1:
                self.rotation = cv2.ROTATE_90_COUNTERCLOCKWISE
            case -1:
                self.rotation = cv2.ROTATE_90_CLOCKWISE
            case 2:
                self.rotation = cv2.ROTATE_180
            case _:
                self.rotation = None
    

    def get_index_at_timestamp(self, timestamp:int):
        index = int((timestamp / 1000) * self.fps)
        return min(index, self.frame_count - 1)
    

    def get_frame_at_index(self, index:int):
        if (not self.ok):
            return None
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, index)
        success, frame = self.cap.read()
        if self.rotation is not None:
            frame = cv2.rotate(frame, self.rotation)
        return frame if success else None
    

    def destroy(self):
        self.cap.release()