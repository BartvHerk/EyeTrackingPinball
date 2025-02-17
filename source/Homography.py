import cv2
import numpy as np
import itertools
from IO import save_perspective_matrix
from OpenCV import resize_image_to_fit, set_brightness, draw_polygon, draw_perspective_grid, scale_position
from containers import ContReference


def set_perspective_mapping(reference:ContReference, field_dimensions:tuple[float, float]) -> bool:
    # Compute
    H = set_corner_points(reference.image, field_dimensions)
    if H is None:
        return False
    H_inv = perspective_mapping_inverse(H)
    
    # Set
    reference.H = H
    reference.H_inv = H_inv

    # Save
    save_perspective_matrix(reference)


def set_corner_points(reference_image:np.ndarray, field_dimensions:tuple[float, float]) -> np.ndarray:
    corners = []
    current = (0, 0)
    scaled_reference, scale_factor = resize_image_to_fit(reference_image.copy())
    scaled_reference = set_brightness(scaled_reference, 0.9)

    complete = False
    H: np.ndarray
    H_inv: np.ndarray

    def corners_inclusive() -> list[tuple[float, float]]: # Corners including cursor location
        return list(itertools.chain(corners, [current]))[:4]


    def mouse_callback(event, x, y, flags, param):
        nonlocal current, complete, H, H_inv
        if event == cv2.EVENT_LBUTTONDOWN:
            if (len(corners) < 4):
                corners.append((x / scale_factor, y / scale_factor))
        if event == cv2.EVENT_MOUSEMOVE:
            current = (x / scale_factor, y / scale_factor)
            if len(corners_inclusive()) == 4:
                positions = sort_corners(corners_inclusive())
                convex = is_convex_quadrilateral(positions)
                if convex:
                    H = compute_perspective_mapping(positions, field_dimensions)
                    try:
                        H_inv = perspective_mapping_inverse(H)
                        complete = True
                    except:
                        complete = False
                else:
                    complete = False
    
    cv2.namedWindow('Set corners')
    cv2.setMouseCallback('Set corners', mouse_callback)

    while True:
        frame = scaled_reference.copy()

        # Draw path
        if not complete:
            positions = list(map(lambda p: scale_position(p, scale_factor), corners_inclusive()))
            draw_polygon(frame, positions)
        
        # Result frame
        else:
            draw_perspective_grid(frame, H_inv, scale_factor, field_dimensions)

        # Show frame
        cv2.imshow('Set corners', frame)

        # Advance and close
        cv2.waitKey(5)
        if cv2.getWindowProperty('Set corners', cv2.WND_PROP_VISIBLE) < 1:
            break
        if len(corners) == 4:
            cv2.waitKey(400)
            break
    
    cv2.destroyAllWindows()
    return H if len(corners) == 4 else None


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