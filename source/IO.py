import csv
import os
import cv2
from pathlib import Path
from containers import ContRecording, ContGazemap


DIR_RECORDINGS = Path('data/recordings')


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

        def jump_section(reader, title:str):
            while True:
                if title in next(reader)[0]:
                    return

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

        # Data
        jump_section(csv_reader, '#DATA')
        headers = next(csv_reader)
        dict_reader = csv.DictReader(csv_file, fieldnames=headers)
        for line in dict_reader:
            if (line['SlideEvent'] != ''): # Skip event rows
                continue
            container_row = {}
            for key in container.data_headers:
                container_row[key] = line[key]
            container.data.append(container_row)
    return container


def display_video_with_gazemap(path, gazemap:ContGazemap):
    cap = cv2.VideoCapture(path)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Draw gazemap dot
        video_timestamp = cap.get(cv2.CAP_PROP_POS_MSEC)
        csv_timestamp = 0
        while (int(gazemap.data[csv_timestamp + 1]['Timestamp']) <= video_timestamp):
            csv_timestamp += 1
        try:
            gaze_x = int(float(gazemap.data[csv_timestamp]['Interpolated Gaze X']))
            gaze_y = int(float(gazemap.data[csv_timestamp]['Interpolated Gaze Y']))
            gaze_position = (gaze_x, gaze_y)
            cv2.circle(frame, gaze_position, 15, (0, 255, 255), 2, cv2.FILLED)
        except:
            pass

        # Show frame
        cv2.imshow("Video", frame)
        
        # Advance and close video
        cv2.waitKey(28)
        if cv2.getWindowProperty("Video", cv2.WND_PROP_VISIBLE) < 1:
            break

    cap.release()
    cv2.destroyAllWindows()