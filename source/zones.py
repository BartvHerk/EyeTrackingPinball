import math
import cv2
import numpy as np

from homography import perspective_map, perspective_mapping_inverse

def point_in_polygon(pt, polygon):
    contour = np.array(polygon, dtype=np.int32)
    return cv2.pointPolygonTest(contour, tuple(pt), False) >= 0

# 0 = in polygon, >0 = outside polygon
def distance_to_polygon(pt, polygon_px, H):
    polygon = polygon_px_to_cm(polygon_px, H)

    contour = np.array(polygon, dtype=np.int32)
    dist = cv2.pointPolygonTest(contour, tuple(pt), True)

    # Set distance inside to 0
    if dist > 0:
        dist = 0
    # Convert distance outside to positive
    if dist < 0:
        dist = -dist
    return dist

def polygon_px_to_cm(polygon_px, H):
    polygon_cm = []
    for pt in polygon_px:
        pt_cm = perspective_map(H, pt)
        polygon_cm.append(pt_cm)
    return polygon_cm