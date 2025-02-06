from pathlib import Path

class ContRecording:
    def __init__(self, paths): # Only these info keys will be imported
        self.paths = paths
    
    @property
    def is_complete(self) -> bool:
        for path in self.paths.values():
            if path == "":
                return False
        return True
    
    def __repr__(self) -> str:
        return f"{type(self).__name__}(dir={self.paths['Directory'].stem}, complete={self.is_complete})"


class ContGazemap:
    data_headers = [ # Only these data keys will be imported
        'Timestamp',
        'Gaze X',
        'Gaze Y'
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