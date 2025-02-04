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