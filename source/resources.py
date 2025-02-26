import numpy as np
from IO import import_image_field, load_specifications, load_settings, save_settings, import_references, import_recordings, save_specifications


class Resources:
    _instance = None


    def __new__(cls, *args, **kwargs): # Singleton
        if cls._instance is None:
            cls._instance = super(Resources, cls).__new__(cls)
            cls._instance.__initialized = False
        return cls._instance


    def __init__(self):
        if not self.__initialized:
            self.__initialized = True
            self._H_inv_field = None

            # Import resources
            self.specifications = load_specifications()
            self.settings = load_settings()
            self.references = import_references()
            self.recordings = import_recordings()
            self.image_field = import_image_field()
    

    @property
    def field_points(self) -> list[tuple[int, int]]:
        p1 = int(self.specifications['field']['points'][0][0]), int(self.specifications['field']['points'][0][1])
        p2 = int(self.specifications['field']['points'][1][0]), int(self.specifications['field']['points'][1][1])
        return [p1, p2]


    @property
    def field_dimensions(self) -> tuple[float, float]:
        p1, p2 = self.field_points[0], self.field_points[1]
        return (abs(p1[0] - p2[0]) * self.field_scale, abs(p1[1] - p2[1]) * self.field_scale)
    

    @property
    def field_scale(self) -> float:
        return float(self.specifications['field']['cms_per_pixel'])


    @property
    def H_inv_field(self) -> np.ndarray:
        if self._H_inv_field is None:
            from homography import sort_corners, compute_perspective_mapping, perspective_mapping_inverse
            p1, p2 = self.field_points
            points = [p1, (p2[0], p1[1]), p2, (p1[0], p2[1])]
            points = sort_corners(points)
            H = compute_perspective_mapping(points, self.field_dimensions)
            try:
                self._H_inv_field = perspective_mapping_inverse(H)
            except:
                pass
        return self._H_inv_field
    

    def save_settings_changes(self):
        save_settings(self.settings)
    

    def save_specifications_changes(self):
        save_specifications(self.specifications)
    

    def recalculate_exports(self):
        for recording in self.recordings:
            recording._export = None