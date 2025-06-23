import csv
import json
import os
import random
import cv2
import re
import numpy as np


from pathlib import Path
from containers import ContReference, ContField, ContRecording, ContExport
from processing import process_data, remove_low_confidence


SENSOR_NAME = 'Pupil_Invisible_Glasses'
DIR_RECORDINGS = Path('data/recordings')
DIR_REFERENCE = Path('data/reference')
DIR_FIELDS = Path('data/fields')
FILE_SETTINGS = Path('data/settings.json')
FILE_FIELD_IMAGE = Path('data/fields/field_jurassic_park.png')
DIR_DATASET = Path('data/dataset')
DEFAULT_SETTINGS = {
    "show_plane": True
}

TRACKING_DATA_CONFIDENCE = 0.3


def load_settings():
    if not os.path.exists(FILE_SETTINGS):
        save_settings(DEFAULT_SETTINGS)
    with open(FILE_SETTINGS, 'r') as json_file:
        settings = json.load(json_file)
        return settings


def save_settings(settings):
    with open(FILE_SETTINGS, 'w') as json_file:
        json.dump(settings, json_file, indent=2)


def load_dictionary(path:Path):
    try:
        with open(path, 'r') as json_file:
            return json.load(json_file)
    except:
        return {}


def save_dictionary_entry(key, value, path:Path):
    dict = load_dictionary(path)
    dict[key] = value
    with open(path, 'w') as json_file:
        json.dump(dict, json_file, indent=2)


def import_references() -> dict[str, ContReference]:
    references = {}
    paths = (entry.path for entry in os.scandir(DIR_REFERENCE) if entry.name.endswith(('.jpg', '.png')))
    reference_points = load_dictionary(DIR_REFERENCE / 'reference_points.json')
    for file in paths:
        path = Path(file)
        name = path.stem
        field = ""
        points = None
        if (name in reference_points):
            field = reference_points[name]["field"]
            try:
                points = list(map(tuple, reference_points[name]["points"]))
            except:
                pass
        image = cv2.imread(file)
        references[name] = ContReference(name, path, image, points, field)
    return references


def save_reference(reference:ContReference):
    obj = {"field": reference.field}
    try:
        obj["points"] = list(map(lambda t: tuple(map(round, t)), reference.points.copy()))
    except:
        pass
    save_dictionary_entry(reference.name, obj, DIR_REFERENCE / 'reference_points.json')


def import_fields() -> dict[str, ContField]:
    fields = {}
    paths = (entry.path for entry in os.scandir(DIR_FIELDS) if entry.name.endswith(('.jpg', '.png')))
    field_points = load_dictionary(DIR_FIELDS / 'field_points.json')
    for file in paths:
        path = Path(file)
        name = path.stem
        cms_per_pixel = 0.1
        points = None
        if (name in field_points):
            cms_per_pixel = float(field_points[name]["cms_per_pixel"])
            points = list(map(tuple, field_points[name]["points"]))
        image = cv2.imread(file)
        fields[name] = ContField(name, path, image, points, cms_per_pixel)
    return fields


def save_field(field:ContField):
    obj = {"cms_per_pixel": field.cms_per_pixel, "points": list(map(lambda t: tuple(map(round, t)), field.points.copy()))}
    save_dictionary_entry(field.name, obj, DIR_FIELDS / 'field_points.json')


def import_recordings() -> list[ContRecording]:
    recordings = []
    recording_dirs = [entry.name for entry in os.scandir(DIR_RECORDINGS) if entry.is_dir()]
    for dir in recording_dirs:
        dir_path = (DIR_RECORDINGS / dir)
        paths = {'Directory': dir_path}

        # Locate relevant files from recording
        paths['Export'] = next((entry.path for entry in os.scandir(dir_path) if entry.name.endswith('.csv')), "")
        paths['Metadata'] = dir_path / 'metadata.json'
        metadata = load_dictionary(paths['Metadata'])
        path_world = metadata.get('video_world', "World")
        path_field = metadata.get('video_field', "Field")
        paths['VideoWorld'] = next((entry.path for entry in os.scandir(dir_path) if entry.name == f"{path_world}.mp4"), "")
        paths['VideoField'] = next((entry.path for entry in os.scandir(dir_path) if entry.name == f"{path_field}.mp4"), "")
        path_tracking_data_raw = next((entry.path for entry in os.scandir(dir_path) if entry.name == "tracking_data.txt"), "")
        path_tracking_data_name = metadata.get('post_processed_tracking', "")
        path_tracking_data = next((entry.path for entry in os.scandir(dir_path) if entry.name == f"{path_tracking_data_name}.txt"), "")
        tracking_data_raw = remove_low_confidence(load_tracking_data(path_tracking_data_raw), TRACKING_DATA_CONFIDENCE)
        tracking_data = load_tracking_data(path_tracking_data) if path_tracking_data else {}

        # Create recording container
        recordings.append(ContRecording(paths, metadata, tracking_data_raw, tracking_data))
    recordings.sort(key=lambda recording: sorting_key(recording.paths['Directory']))
    return recordings


# Used to sort filenames
def sorting_key(s):
    path = Path(s)
    file = path.stem
    match = re.match(r'(\d+)', file)
    if match:
        return (0, int(match.group(1)))
    return (1, s)


def save_recording_metadata(recording:ContRecording):
    with open(recording.paths['Metadata'], 'w') as json_file:
        json.dump(recording.metadata, json_file, indent=2)


def import_export_csv(path, references:dict[str, ContReference]) -> ContExport:
    container = ContExport()
    with open(path, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)

        def jump_section(reader, title:str) -> list[str]:
            line = []
            while True:
                line = next(reader)
                if title in line[0]:
                    return line

        # Info
        jump_section(csv_reader, '#INFO')
        csv_info = {}
        while True:
            line = next(csv_reader)
            if line[0] == '#':
                break
            csv_info[line[0].replace('#','')] = line[1]
        for key in container.info.keys(): # Fill only the keys present in ContExport
            container.info[key] = csv_info[key]
        container.info['Recording time'] = container.info['Recording time'].split(' ')[1]
        
        # Metadata
        line = jump_section(csv_reader, '#Group')
        index = 1
        try:
            while line[index] != 'Mapped Gaze':
                index += 1
            line = jump_section(csv_reader, '#Resolution Reference Image')
            numbers = re.findall(r"\d+", line[index])
            width, height = map(int, numbers)
            container.reference_dimensions = (width, height)
            line = jump_section(csv_reader, '#Channel identifier')
            match = re.search(fr"{SENSOR_NAME}_(.*?)_Mapped_Gaze_X", line[index])
            reference = match.group(1) if match else ''
            for key in references:
                if (reference.lower() == key.lower()):
                    container.reference = references[key]
                    reference = container.reference.name
            str_x = f'{reference}_Gaze_X'
            str_y = f'{reference}_Gaze_Y'
        except:
            print("Error: Couldn't load gaze mapped datapoints")

        # Data
        jump_section(csv_reader, '#DATA')
        headers = next(csv_reader)
        dict_reader = csv.DictReader(csv_file, fieldnames=headers)
        for line in dict_reader:
            if (line['SlideEvent'] != ''): # Skip event rows
                continue
            container_row = {}
            for key in container.data_headers: # Default headers
                container_row[key] = line.get(key, '')
            try: # Gaze mapping headers handled separately
                container_row['Mapped Gaze X'] = line[str_x] if int(line[str_x]) >= 0 else ''
                container_row['Mapped Gaze Y'] = line[str_y] if int(line[str_y]) >= 0 else ''
            except:
                container_row['Mapped Gaze X'] = ''
                container_row['Mapped Gaze Y'] = ''
            container.data.append(container_row)
    process_data(container)
    return container


def save_tracking_data(path, tracking_data):
    with open(path, "w") as f:
        for frame_idx in sorted(tracking_data.keys()):
            detections:list[dict] = tracking_data[frame_idx]
            f.write(f"{frame_idx} {len(detections)}\n")
            for det in detections:
                f.write(" ".join(str(x) for x in det.values()) + "\n")


def load_tracking_data(path):
    detections_by_frame = {}
    if os.path.exists(path):
        with open(path, "r") as f:
            while True:
                header = f.readline()
                if not header:
                    break  # End of file
                frame_index, num_detections = map(int, header.strip().split())
                detections = []
                for _ in range(num_detections):
                    line = f.readline()
                    parts = line.strip().split()
                    detection = {
                        'track_id': int(parts[0]),
                        'confidence': float(parts[1]),
                        'cx': float(parts[2]),
                        'cy': float(parts[3]),
                        'radius': float(parts[4])
                    }
                    detections.append(detection)
                detections_by_frame[frame_index] = detections
    return detections_by_frame


def load_dataset_frames_for_recording(recording:ContRecording) -> list[int]:
    name = recording.paths['Directory'].stem

    # Get paths
    dir_train = DIR_DATASET / "labels/train"
    dir_val = DIR_DATASET / "labels/val"
    paths_train, paths_val = [], []
    if os.path.exists(dir_train):
        paths_train = list(entry.path for entry in os.scandir(dir_train) if entry.name.endswith(('.txt')))
    if os.path.exists(dir_val):
        paths_val = list(entry.path for entry in os.scandir(dir_val) if entry.name.endswith(('.txt')))
    
    # Get frames
    frames = []
    for path in (paths_train + paths_val):
        filename:str = Path(path).stem
        try:
            frame_nr = (int)(filename.replace(name + "_", ''))
            frames.append(frame_nr)
        except:
            pass
    return frames


def save_dataset_frame_for_recording(recording:ContRecording, index:int, img:np.ndarray, text:str):
    # Decide if training or validation data
    data = "train" if random.random() < 0.8 else "val"
    file_image = DIR_DATASET / f"images/{data}/{recording.paths['Directory'].stem}_{index}.png"
    file_label = DIR_DATASET / f"labels/{data}/{recording.paths['Directory'].stem}_{index}.txt"
    os.makedirs(os.path.dirname(file_image), exist_ok=True)
    os.makedirs(os.path.dirname(file_label), exist_ok=True)
    cv2.imwrite(file_image, img)
    with open(file_label, "w") as file:
        file.write(text)