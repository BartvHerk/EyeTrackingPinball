import cv2
import numpy as np

def point_in_polygon(pt, polygon):
    contour = np.array(polygon, dtype=np.int32)
    return cv2.pointPolygonTest(contour, tuple(pt), False) >= 0