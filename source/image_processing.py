import math
import cv2
import numpy as np
from PIL import ImageTk, Image
from resources import Resources


GRID_CELL_SIZE = 10
IN = 8
OUT = 25
COLORS = [(223, 255, 0), (255, 191, 0), (255, 127, 80),
          (222, 49, 99), (159, 226, 191), (64, 224, 208),
          (100, 149, 237), (204, 204, 255), (255, 255, 255),
          (239, 136, 190), (176, 176, 176), (63, 72, 204),
          (163, 73, 164), (176, 97, 49), (34, 177, 76)]


def cvimage_to_tkimage(img:np.ndarray):
    rgb_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(rgb_image)
    return ImageTk.PhotoImage(image=image)


def resize_image_to_fit(img:np.ndarray, max_size:tuple[int, int]=None):
    resources = Resources()
    if max_size is None:
         max_size = resources.root.winfo_screenwidth() * 0.7, resources.root.winfo_screenheight() * 0.7
    height, width = img.shape[:2]
    max_width, max_height = max_size
    if width <= max_width and height <= max_height: # Don't scale if size already fits
        return img.copy(), 1.0
    scale_factor = min(max_width / width, max_height / height)
    new_size = (max(int(width * scale_factor), 1), max(int(height * scale_factor), 1))
    new_img = cv2.resize(img, new_size, interpolation=cv2.INTER_AREA) # Scale
    return new_img, scale_factor


def draw_circle(img:np.ndarray, position:tuple[float, float], radius:int, color:tuple[int, int, int], outline:bool=False): 
    height, width = img.shape[:2]
    x, y = tuple(map(int, position))
    if x >= 0 and x < width and y >= 0 and y < height:
        if outline:
            cv2.circle(img, (x, y), radius, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.circle(img, (x, y), radius, color, 2, cv2.LINE_AA)


def draw_gaze_circle(img:np.ndarray, position:tuple[float, float]):
    draw_circle(img, position, 25, (0, 255, 255), True)


def draw_crosshair(img:np.ndarray, position:tuple[float, float], color:tuple[int, int, int], scale:int=1):
     x, y = tuple(map(int, position))
     r, g, b = color
     draw_line_outline(img, (x + IN * scale, y + IN * scale), (x + OUT * scale, y + OUT * scale), 4 * scale, (b, g, r), 2 * scale)
     draw_line_outline(img, (x + IN * scale, y - IN * scale), (x + OUT * scale, y - OUT * scale), 4 * scale, (b, g, r), 2 * scale)
     draw_line_outline(img, (x - IN * scale, y - IN * scale), (x - OUT * scale, y - OUT * scale), 4 * scale, (b, g, r), 2 * scale)
     draw_line_outline(img, (x - IN * scale, y + IN * scale), (x - OUT * scale, y + OUT * scale), 4 * scale, (b, g, r), 2 * scale)


def draw_line(img:np.ndarray, pos1:tuple[float, float], pos2:tuple[float, float], thickness:int=2, color:tuple[int, int, int]=(0, 255, 255)):
    pt1 = tuple(map(int, pos1))
    pt2 = tuple(map(int, pos2))
    cv2.line(img, pt1, pt2, color, thickness, cv2.LINE_AA)


def draw_line_outline(img:np.ndarray, pos1:tuple[float, float], pos2:tuple[float, float], thickness:int=2, color:tuple[int, int, int]=(0, 255, 255), outline:int=2):
     draw_line(img, pos1, pos2, thickness + outline, (0, 0, 0))
     draw_line(img, pos1, pos2, thickness, color)


def draw_polygon(img:np.ndarray, points:list[tuple[float, float]], thickness:int=2):
    for i in range(len(points)):
            pos1 = points[i]
            pos2 = points[(i + 1) % len(points)]
            draw_line(img, pos1, pos2, thickness)


def draw_perspective_grid(img:np.ndarray, H_inv:np.ndarray, scale_factor, field_dimensions):
    from homography import perspective_map
    width, height = field_dimensions
    cuts_w, cuts_h = math.floor(width / GRID_CELL_SIZE), math.floor(height / GRID_CELL_SIZE)
    def mp(pt):
         return scale_position(perspective_map(H_inv, pt), scale_factor)

    corners = [mp((0, 0)), mp((width, 0)), mp((width, height)), mp((0, height))]
    draw_polygon(img, corners)
    for i in range(1, cuts_w + 1):
         pos1, pos2 = mp((i * GRID_CELL_SIZE, 0)), mp((i * GRID_CELL_SIZE, height))
         draw_line(img, pos1, pos2, 1)
    for i in range(1, cuts_h + 1):
         pos1, pos2 = mp((0, i * GRID_CELL_SIZE)), mp((width, i * GRID_CELL_SIZE))
         draw_line(img, pos1, pos2, 1)


def scale_position(pos:tuple[float, float], scale_factor:float) -> tuple[float, float]:
        return tuple(map(lambda x: x * scale_factor, pos))