import csv
import os
import cv2
import re
import numpy as np
from pathlib import Path
from containers import ContRecording, ContGazemap


DIR_RECORDINGS = Path('data/recordings')
DIR_REFERENCE = Path('data/reference')
SENSOR_NAME = 'Pupil_Invisible_Glasses'


def gather_references() -> dict[str, np.ndarray]:
    references = {}
    paths = (entry.path for entry in os.scandir(DIR_REFERENCE) if entry.name.endswith(('.jpg', '.png')))
    for file in paths:
        image = cv2.imread(file)
        references[Path(file).stem] = image
    return references


def gather_data() -> list[ContRecording]:
    recordings = []
    recording_dirs = [entry.name for entry in os.scandir(DIR_RECORDINGS) if entry.is_dir()]
    for dir in recording_dirs:
        dir_path = (DIR_RECORDINGS / dir)
        paths = {'Directory': dir_path}

        # Locate relevant files from recording
        paths['Gazemap'] = next((entry.path for entry in os.scandir(dir_path) if entry.name.endswith('.csv')), "")
        paths['Video'] = next((entry.path for entry in os.scandir(dir_path) if entry.name.endswith('.mp4')), "")

        # Create recording container
        recordings.append(ContRecording(paths))
    return recordings


def import_csv_gazemap(path) -> ContGazemap:
    container = ContGazemap()
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
        for key in container.info.keys(): # Fill only the keys present in ContGazemap
            container.info[key] = csv_info[key]
        
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
            container.reference = reference
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
            if container.reference != '': # Gaze mapping headers handled separately
                container_row['Mapped Gaze X'] = line[str_x] if int(line[str_x]) >= 0 else ''
                container_row['Mapped Gaze Y'] = line[str_y] if int(line[str_y]) >= 0 else ''
            container.data.append(container_row)
    return container


def display_video_raw(path, gazemap:ContGazemap):
    cap = cv2.VideoCapture(path)
    csv_timestamp = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Scale down if needed
        frame, scale_factor = resize_frame_to_fit(frame, (700, 700))

        # Draw gaze dot
        video_timestamp = cap.get(cv2.CAP_PROP_POS_MSEC)
        while (int(gazemap.data[csv_timestamp + 1]['Timestamp']) <= video_timestamp):
            csv_timestamp += 1
        try:
            gaze_x = float(gazemap.data[csv_timestamp]['Interpolated Gaze X'])
            gaze_y = float(gazemap.data[csv_timestamp]['Interpolated Gaze Y'])
            gaze_position = (gaze_x * scale_factor, gaze_y * scale_factor)
            draw_gaze_dot(frame, gaze_position)
        except:
            pass

        # Show frame
        cv2.imshow("Video", frame)
        
        # Advance and close video
        cv2.waitKey(20)
        if cv2.getWindowProperty("Video", cv2.WND_PROP_VISIBLE) < 1:
            break

    cap.release()
    cv2.destroyAllWindows()


def display_video_gaze_mapped(references:dict[str, np.ndarray], gazemap:ContGazemap):
    if gazemap.reference not in references:
        print('Error: Gazemap did not reference an image or the image was not found')
        return
    reference = references[gazemap.reference]
    height, width = reference.shape[:2]
    data_width, data_height = gazemap.reference_dimensions
    ms_per_frame = 100
    video_timestamp = 0
    csv_timestamp = 0
    
    while True:
        frame, scale_factor = resize_frame_to_fit(reference.copy(), (700, 700))

        # Draw gaze dot
        while (int(gazemap.data[csv_timestamp + 1]['Timestamp']) <= video_timestamp):
            csv_timestamp += 1
        try:
            mapped_gaze_x = int(gazemap.data[csv_timestamp]['Mapped Gaze X']) / data_width * width
            mapped_gaze_y = int(gazemap.data[csv_timestamp]['Mapped Gaze Y']) / data_height * height
            gaze_position = (mapped_gaze_x * scale_factor, mapped_gaze_y * scale_factor)
            draw_gaze_dot(frame, gaze_position)
        except:
            pass

        # Show frame
        cv2.imshow("Video", frame)

        # Advance and close
        video_timestamp += ms_per_frame
        cv2.waitKey(20)
        if cv2.getWindowProperty("Video", cv2.WND_PROP_VISIBLE) < 1:
            break
    
    cv2.destroyAllWindows()


def resize_frame_to_fit(frame, max_size):
    height, width = frame.shape[:2]
    max_width, max_height = max_size
    if width <= max_width and height <= max_height: # Don't scale if size already fits
        return frame, 1.0
    scale_factor = min(max_width / width, max_height / height)
    new_size = (int(width * scale_factor), int(height * scale_factor))
    new_frame = cv2.resize(frame, new_size, interpolation=cv2.INTER_AREA) # Scale
    return new_frame, scale_factor

def draw_gaze_dot(frame, position:tuple[float, float]):
    height, width = frame.shape[:2]
    x, y = tuple(map(int, position))
    if x >= 0 and x < width and y >= 0 and y < height:
        cv2.circle(frame, (x, y), 20, (0, 255, 255), 2, cv2.FILLED)