from IO import load_specifications, load_settings, save_settings, import_references, import_recordings
from containers import ContReference


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

            # Import resources
            self.specifications = load_specifications()
            self.settings = load_settings()
            self.field_dimensions = float(self.specifications['field']['width']), float(self.specifications['field']['height'])
            self.references = import_references()
            self.recordings = import_recordings()
    

    def save_settings_changes(self):
        save_settings(self.settings)
    

    def on_homography_matrix_update(self, reference:ContReference):
        for recording in self.recordings:
            if recording._export is None:
                continue
            if recording.export.reference == reference:
                recording.generate_export()