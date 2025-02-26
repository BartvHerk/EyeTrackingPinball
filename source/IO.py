import csv
import json
import os
import cv2
import re
import numpy as np

from pathlib import Path
from containers import ContReference, ContRecording, ContExport
from processing import process_data


SENSOR_NAME = 'Pupil_Invisible_Glasses'
DIR_RECORDINGS = Path('data/recordings')
DIR_REFERENCE = Path('data/reference')
FILE_SPECIFICATIONS = Path('data/specifications.json')
FILE_SETTINGS = Path('data/settings.json')
FILE_FIELD_IMAGE = Path('data/field.png')
DEFAULT_SETTINGS = {
    "show_plane": True
}


def load_specifications():
    with open(FILE_SPECIFICATIONS, 'r') as json_file:
        specifications = json.load(json_file)
        return specifications
    

def save_specifications(specifications):
    with open(FILE_SPECIFICATIONS, 'w') as json_file:
        json.dump(specifications, json_file, indent=2)


def load_settings():
    if not os.path.exists(FILE_SETTINGS):
        save_settings(DEFAULT_SETTINGS)
    with open(FILE_SETTINGS, 'r') as json_file:
        settings = json.load(json_file)
        return settings


def save_settings(settings):
    with open(FILE_SETTINGS, 'w') as json_file:
        json.dump(settings, json_file, indent=2)


def import_references() -> dict[str, ContReference]:
    references = {}
    paths = (entry.path for entry in os.scandir(DIR_REFERENCE) if entry.name.endswith(('.jpg', '.png')))
    reference_points = load_reference_points()
    for file in paths:
        path = Path(file)
        name = path.stem
        points = None
        if (name in reference_points):
            points = list(map(tuple, reference_points[name]))
        image = cv2.imread(file)
        references[name] = ContReference(name, path, image, points)
    return references


def load_reference_points() -> np.ndarray:
    try:
        with open(DIR_REFERENCE / 'reference_points.json', 'r') as json_file:
            reference_points = json.load(json_file)
            return reference_points
    except:
        return {}


def save_reference_points(reference:ContReference):
    reference_points = load_reference_points()
    reference_points[reference.name] = reference.points
    with open(DIR_REFERENCE / 'reference_points.json', 'w') as json_file:
        json.dump(reference_points, json_file, indent=2)


def import_image_field():
    image_field = cv2.imread(FILE_FIELD_IMAGE)
    return image_field


def import_recordings() -> list[ContRecording]:
    recordings = []
    recording_dirs = [entry.name for entry in os.scandir(DIR_RECORDINGS) if entry.is_dir()]
    for dir in recording_dirs:
        dir_path = (DIR_RECORDINGS / dir)
        paths = {'Directory': dir_path}

        # Locate relevant files from recording
        paths['Export'] = next((entry.path for entry in os.scandir(dir_path) if entry.name.endswith('.csv')), "")
        paths['Video'] = next((entry.path for entry in os.scandir(dir_path) if entry.name.endswith('.mp4')), "")

        # Create recording container
        recordings.append(ContRecording(paths))
    return recordings


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
            if reference in references:
                container.reference = references[reference]
            str_x = f'{reference}_Gaze_X'
            str_y = f'{reference}_Gaze_Y'
        except:
            pass

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