import cv2
import numpy as np


MAX_DIMENSIONS = (800, 800)


def resize_image_to_fit(img:np.ndarray, max_size:tuple[int, int]=MAX_DIMENSIONS):
    height, width = img.shape[:2]
    max_width, max_height = max_size
    max_width = max(max_width, 1)
    max_height = max(max_height, 1)
    if width <= max_width and height <= max_height: # Don't scale if size already fits
        return img, 1.0
    scale_factor = min(max_width / width, max_height / height)
    new_size = (int(width * scale_factor), int(height * scale_factor))
    new_img = cv2.resize(img, new_size, interpolation=cv2.INTER_AREA) # Scale
    return new_img, scale_factor


def draw_gaze_circle(img:np.ndarray, position:tuple[float, float]): 
    height, width = img.shape[:2]
    x, y = tuple(map(int, position))
    if x >= 0 and x < width and y >= 0 and y < height:
        cv2.circle(img, (x, y), 25, (0, 255, 255), 2, cv2.LINE_AA)


def draw_line(img:np.ndarray, pos1:tuple[float, float], pos2:tuple[float, float], thickness:int=2):
    pt1 = tuple(map(int, pos1))
    pt2 = tuple(map(int, pos2))
    cv2.line(img, pt1, pt2, (0, 255, 255), thickness, cv2.LINE_AA)


def draw_polygon(img:np.ndarray, points:list[tuple[float, float]]):
    for i in range(len(points)):
            pos1 = points[i]
            pos2 = points[(i + 1) % len(points)]
            draw_line(img, pos1, pos2)


def draw_perspective_grid(img:np.ndarray, H_inv:np.ndarray, scale_factor, field_dimensions):
    from homography import perspective_map
    width, height = field_dimensions
    def mp(pt):
         pt_scaled = (pt[0] * width, pt[1] * height)
         return scale_position(perspective_map(H_inv, pt_scaled), scale_factor)

    corners = [mp((0, 0)), mp((1, 0)), mp((1, 1)), mp((0, 1))]
    draw_polygon(img, corners)
    for i in np.arange(0.1, 1.0, 0.1):
        pos1, pos2, pos3, pos4 = mp((0, i)), mp((1, i)), mp((i, 0)), mp((i, 1))
        draw_line(img, pos1, pos2, 1)
        draw_line(img, pos3, pos4, 1)


def scale_position(pos:tuple[float, float], scale_factor:float) -> tuple[float, float]:
        return tuple(map(lambda x: x * scale_factor, pos))


def set_brightness(img:np.ndarray, factor:float) -> np.ndarray:
    return np.clip((img.astype(np.float32) * factor), 0, 255).astype(np.uint8)