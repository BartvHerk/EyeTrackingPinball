import math
import numpy as np
import tkinter as tk
from tkinter import ttk

from containers import ContRecording
from IO import save_stats_entry
from resources import Resources
from interface.interface_custom import create_toplevel, ready_toplevel
from video import Video


VEL_BIN_EDGES = np.linspace(0, 200, num=201) # 200 bins
FLIPPER_BIN_EDGES = np.linspace(0, 150, num=301) # 200 bins
FLIPPER_POS = [23, 97]


def generate_stats(recording:ContRecording):
    resources = Resources()
    participant = recording.metadata.get('participant', None)
    task_key = recording.metadata.get('task_key', "norm")
    if participant is None:
        print("Error: Recording not linked to participant")
        return

    export = recording.export
    data = export.data
    print(f"Generating stats for {participant}, {task_key}... ", end='', flush=True)

    # Timing
    videoWorld = Video(recording.paths['VideoWorld'])
    videoField = Video(recording.paths['VideoField'])
    start_world = recording.metadata.get('start_world', 0)
    start_field = recording.metadata.get('start_field', 0)
    timestamp_to_field = lambda timestamp: timestamp_to_frame(timestamp, start_field, videoField.fps)
    duration = int(min(videoWorld.duration - start_world, videoField.duration - start_field))

    # Stat counter
    condition_counter = {}

    # Iterate through recording
    frame_count = int(duration / 1000 * videoField.fps)
    export_index = 0
    for i in range(frame_count):
        timestamp = (i / frame_count) * duration
        
        # Get field condition
        frame_field = timestamp_to_field(timestamp)
        condition = recording.conditions[frame_field]['condition']
        has_detection = recording.conditions[frame_field]['has_detection']

        # Find moment in export
        timestamp_export = timestamp + start_world
        while export_index < len(data) - 1:
            if data[export_index + 1]['Timestamp'] > timestamp_export:
                break
            export_index += 1
        export_index = min(export_index, len(data) - 2)
        a = data[export_index]['Timestamp']
        b = data[export_index + 1]['Timestamp']
        t = max(min((timestamp_export - a) / (b - a), 1), 0)

        # Increment counters
        if condition_counter.get(condition, None) is None:
            condition_counter[condition] = {'Gaze Velocity': [], 'Flipper Distance': []}
        
        velocity = export.get_val('Gaze Velocity', export_index, t)
        if velocity is not None:
            condition_counter[condition]['Gaze Velocity'].append(velocity)
        gaze_x = export.get_val('Perspective Gaze X', export_index, t)
        gaze_y = export.get_val('Perspective Gaze Y', export_index, t)
        if gaze_x is not None and gaze_y is not None:
            flipper_distance = math.dist(FLIPPER_POS, [gaze_x, gaze_y])
            condition_counter[condition]['Flipper Distance'].append(flipper_distance)

    # Generate recording stats
    counts_vel_default, _ = np.histogram(condition_counter['Single ball']['Gaze Velocity'], bins=VEL_BIN_EDGES)
    counts_vel_multiball, _ = np.histogram(condition_counter['Multiball']['Gaze Velocity'], bins=VEL_BIN_EDGES)
    counts_vel_default_normalized = counts_vel_default / counts_vel_default.sum()
    counts_vel_multiball_normalized = counts_vel_multiball / counts_vel_multiball.sum()

    counts_flip_default, _ = np.histogram(condition_counter['Single ball']['Flipper Distance'], bins=FLIPPER_BIN_EDGES)
    counts_flip_multiball, _ = np.histogram(condition_counter['Multiball']['Flipper Distance'], bins=FLIPPER_BIN_EDGES)
    counts_flip_default_normalized = counts_flip_default / counts_flip_default.sum()
    counts_flip_multiball_normalized = counts_flip_multiball / counts_flip_multiball.sum()

    stats = {
        'vel_hist_default': counts_vel_default_normalized.tolist(),
        'vel_hist_multiball': counts_vel_multiball_normalized.tolist(),
        'flip_hist_default': counts_flip_default_normalized.tolist(),
        'flip_hist_multiball': counts_flip_multiball_normalized.tolist()
    }

    # Generate survey stats
    participant_survey = []
    for p in resources.participants:
        if p['Name'] == participant:
            participant_survey = p
            break
    
    high_first = True if participant_survey["High_First"] == "Yes" else False
    TLX_1_properties = ["Mental demand 1_1", "Physical demand 1_1", "Temporal demand 1_1", "Performance 1_1", "Effort 1_1", "Frustration 1_1"]
    TLX_2_properties = ["Q23_1", "Q24_1", "Q25_1", "Q26_1", "Q27_1", "Q28_1"]
    TLX_1_values, TLX_2_values = [], []
    for TLX_property in TLX_1_properties:
        TLX_1_values.append(get_survey_value(participant_survey, TLX_property, 0))
    TLX_1_average = np.mean(TLX_1_values)
    for TLX_property in TLX_2_properties:
        TLX_2_values.append(get_survey_value(participant_survey, TLX_property, 0))
    TLX_2_average = np.mean(TLX_2_values)
    TLX_High, TLX_Norm = (TLX_1_average, TLX_2_average) if high_first else (TLX_2_average, TLX_1_average)

    global_stats = {
        'TLX_High': TLX_High,
        'TLX_Norm': TLX_Norm
    }

    # Free memory
    videoWorld.destroy()
    videoField.destroy()

    # Save stats
    save_stats_entry(participant, task_key, stats, global_stats)
    print("Done")


def timestamp_to_frame(timestamp, start, fps):
    return int((timestamp + start) / 1000 * fps)


def get_survey_value(participant_survey:dict, key:str, default):
    try:
        return int(participant_survey[key])
    except:
        return default