import cv2
import numpy as np


def sort_corners(corners): # Sort points in clockwise order, starting top-left
    corners = np.array(corners, dtype=np.float32)
    centroid = np.mean(corners, axis=0)
    return sorted(corners, key=lambda p: np.arctan2(p[1] - centroid[1], p[0] - centroid[0]))


def is_convex_quadrilateral(corners): # Computes quadrilateral convexity using cross product
    for i in range(4):
        p1, p2, p3 = corners[i], corners[(i+1) % 4], corners[(i+2) % 4]
        v1 = p2 - p1
        v2 = p3 - p2
        cross_product = np.cross(v1, v2)
        if cross_product < 0:  # Negative means an internal angle > 180 degrees
            return False
    return True


def compute_perspective_mapping(corners, field_dimensions) -> np.ndarray:
    width, height = field_dimensions

    # Destination (rectified) plane coordinates
    rectified_corners = np.array([
        [0, 0],
        [width, 0],
        [width, height],
        [0, height]
    ], dtype=np.float32)

    # Compute the homography matrix
    return cv2.getPerspectiveTransform(np.array(corners, dtype=np.float32), rectified_corners)


def perspective_mapping_inverse(H:np.ndarray) -> np.ndarray:
    return np.linalg.inv(H)


def perspective_map(H:np.ndarray, pt) -> tuple[float, float]:
    src_pt = np.array([[pt]], dtype=np.float32)
    dst_pt = cv2.perspectiveTransform(src_pt, H)
    return tuple(dst_pt[0, 0])