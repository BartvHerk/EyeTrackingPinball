import numpy as np


class ContReference:
    def __init__(self, name, path, image, points):
        self.name = name
        self.path = path
        self.image = image
        self.points = points
        self._H = None
        self.H_computed = False
    

    @property
    def H(self) -> np.ndarray:
        if not self.H_computed:
            from homography import compute_perspective_mapping
            from resources import Resources
            resources = Resources()
            self._H = compute_perspective_mapping(self.points, resources.field_dimensions)
            self.H_computed = True
        return self._H


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
    def __init__(self, paths): # Only these info keys will be imported
        self.paths = paths
        self._export = None
    

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