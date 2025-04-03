import numpy as np


class ContReference:
    def __init__(self, name, path, image, points, field):
        self.name = name
        self.path = path
        self.image = image
        self.points = points
        self.field = field
        self._H = None
        self.H_computed = False
    

    @property
    def H(self) -> np.ndarray:
        if not self.H_computed:
            from homography import compute_perspective_mapping
            from resources import Resources
            resources = Resources()
            self._H = compute_perspective_mapping(self.points, resources.fields[self.field].field_dimensions)
            self.H_computed = True
        return self._H


    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self.name})"


class ContField:
    def __init__(self, name, path, image, points, cms_per_pixel):
        self.name = name
        self.path = path
        self.image = image
        self.points = points
        self.cms_per_pixel = cms_per_pixel
        self._H_inv_field = None
        self.H_computed = False
    

    @property
    def field_dimensions(self) -> tuple[float, float]:
        p1, p2 = self.points
        return abs(p1[0] - p2[0]) * self.cms_per_pixel, abs(p1[1] - p2[1]) * self.cms_per_pixel

    @property
    def H_inv_field(self) -> np.ndarray:
        if not self.H_computed:
            from homography import sort_corners, compute_perspective_mapping, perspective_mapping_inverse
            p1, p2 = self.points
            points = [p1, (p2[0], p1[1]), p2, (p1[0], p2[1])]
            points = sort_corners(points)
            H = compute_perspective_mapping(points, self.field_dimensions)
            try:
                self._H_inv_field = perspective_mapping_inverse(H)
            except:
                print("Error: Couldn't invert field homography matrix")
            self.H_computed = True
        return self._H_inv_field


    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self.name})"


class ContExport:
    reference:ContReference = None
    reference_dimensions = (0, 0)
    data_headers = [ # Only these data keys will be imported
        'Timestamp',
        'Gaze X',
        'Gaze Y',
        'Interpolated Gaze X',
        'Interpolated Gaze Y',
        'Mapped Gaze X',
        'Mapped Gaze Y'
    ]
    

    def __init__(self): # Only these info keys will be imported
        self.info = {
            'Study name':'',
            'Respondent Name':'',
            'Respondent Age':'',
            'Respondent Gender':'',
            'Recording time':''
        }
        self.data = []

    
    def __repr__(self) -> str:
        return f"{type(self).__name__}(respondent={self.info['Respondent Name']})"


class ContRecording:
    def __init__(self, paths:dict): # Only these info keys will be imported
        self.paths = paths
        self._export = None
        self._metadata = {}
        self.loaded_metadata = False
    

    @property
    def metadata(self) -> dict[str, any]:
        if not self.loaded_metadata:
            from IO import import_recording_metadata
            self._metadata = import_recording_metadata(self)
            self.loaded_metadata = True
        return self._metadata


    @property
    def is_complete(self) -> bool:
        for path in self.paths.values():
            if path == "":
                return False
        return True
    

    @property
    def export(self) -> ContExport:
        if self._export is None:
            self.generate_export()
        return self._export
    

    def generate_export(self):
        from IO import import_export_csv
        from resources import Resources
        resources = Resources()
        self._export = import_export_csv(self.paths['Export'], resources.references)

    
    def __repr__(self) -> str:
        return f"{type(self).__name__}(dir={self.paths['Directory'].stem}, complete={self.is_complete})"