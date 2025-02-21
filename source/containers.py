import numpy as np


class ContReference:
    H:np.ndarray = None
    H_inv:np.ndarray = None


    def __init__(self, name, path, image, H):
        from homography import perspective_mapping_inverse
        self.name = name
        self.path = path
        self.image = image
        if H is not None:
            self.H = H
            self.H_inv = perspective_mapping_inverse(H)
    

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
            from IO import import_export_csv
            from resources import Resources
            resources = Resources()
            self._export = import_export_csv(self.paths['Export'], resources.references)
        return self._export

    
    def __repr__(self) -> str:
        return f"{type(self).__name__}(dir={self.paths['Directory'].stem}, complete={self.is_complete})"