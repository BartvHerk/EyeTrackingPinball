import math
import numpy as np

from containers import ContRecording
from IO import save_csv, save_stats_entry, import_stats
from resources import Resources
from pursuit import get_pursuit_data
from video import Video


VEL_BIN_EDGES = np.linspace(0, 200, num=201) # 200 bins
FLIPPER_BIN_EDGES = np.linspace(0, 150, num=151)
BALL_BIN_EDGES = np.linspace(0, 150, num=151)
FIX_BIN_EDGES = np.linspace(0, 300, num=301)
SAC_BIN_EDGES = np.linspace(0, 200, num=201)
PUR_BIN_EDGES = np.linspace(0, 1.5, num=301)
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
    field_width, field_height = resources.fields[export.reference.field].field_dimensions
    print(f"Generating stats for {participant}, {task_key}... ", end='', flush=True)

    # Timing
    videoWorld = Video(recording.paths['VideoWorld'])
    videoField = Video(recording.paths['VideoField'])
    start_world = recording.metadata.get('start_world', 0)
    start_field = recording.metadata.get('start_field', 0)
    timestamp_to_field = lambda timestamp: timestamp_to_frame(timestamp, start_field, videoField.fps)
    duration = int(min(videoWorld.duration - start_world, videoField.duration - start_field))

    # Stat counter and pursuit data
    condition_counter = {}
    pursuit_data = get_pursuit_data(recording.tracking_data)

    # Iterate through recording
    frame_count = int(duration / 1000 * videoField.fps)
    export_index = 0
    fixation_index, saccade_index = -1, -1
    for i in range(frame_count):
        timestamp = (i / frame_count) * duration
        
        # Get field condition and detections
        frame_field = timestamp_to_field(timestamp)
        condition = recording.conditions[frame_field]['condition']
        detections = recording.tracking_data.get(frame_field, [])

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
        if condition not in condition_counter:
            condition_counter[condition] = {
                'Frames': 0, # Frames spent in this condition
                'Frames Looking': 0, # Frames spent looking at field
                'Gaze Velocity': [],
                'Flipper Distance': [],
                'Fixation Duration': [],
                'Saccade Duration': [],
                'Pursuit Duration': [],
                'Ball Distance': []
            }
        condition_counter[condition]['Frames'] += 1
        
        # Velocity
        velocity = export.get_val('Gaze Velocity', export_index, t)
        if velocity is not None:
            condition_counter[condition]['Gaze Velocity'].append(velocity)
        
        # Flipper distance + looking at field
        gaze_x = export.get_val('Perspective Gaze X', export_index, t)
        gaze_y = export.get_val('Perspective Gaze Y', export_index, t)
        if gaze_x is not None and gaze_y is not None:
            flipper_distance = math.dist(FLIPPER_POS, [gaze_x, gaze_y])
            condition_counter[condition]['Flipper Distance'].append(flipper_distance)
            if gaze_x >= 0 and gaze_x <= field_width and gaze_y >= 0 and gaze_y <= field_height:
                condition_counter[condition]['Frames Looking'] += 1
        
        # Ball-flipper distance
        for detection in detections:
            distance = math.dist(FLIPPER_POS, [detection['cx'], detection['cy']])
            condition_counter[condition]['Ball Distance'].append(distance)

        # Fixations
        fixation_index_export = export.get_val('Fixation Index', export_index, 0)
        if fixation_index_export is not None:
            if fixation_index_export > fixation_index:
                fixation_index = fixation_index_export
                fixation_duration = export.get_val('Fixation Duration', export_index, 0)
                condition_counter[condition]['Fixation Duration'].append(fixation_duration)
        
        # Saccades
        saccade_index_export = export.get_val('Saccade Index', export_index, 0)
        if saccade_index_export is not None:
            if saccade_index_export > saccade_index:
                saccade_index = saccade_index_export
                saccade_duration = export.get_val('Saccade Duration', export_index, 0)
                condition_counter[condition]['Saccade Duration'].append(saccade_duration)
        
        # Pursuits
        pursuit_current = pursuit_data.get(frame_field, None)
        if pursuit_current is not None:
            condition_counter[condition]['Pursuit Duration'].append(pursuit_current[0] * videoField.frame_duration / 1000)

    # Generate recording stats
    frame_duration = 1 / videoField.fps
    time_default = condition_counter['Single ball']['Frames'] * frame_duration
    time_multiball = condition_counter['Multiball']['Frames'] * frame_duration
    percent_looking_default = condition_counter['Single ball']['Frames Looking'] / condition_counter['Single ball']['Frames']
    percent_looking_multiball = condition_counter['Multiball']['Frames Looking'] / condition_counter['Multiball']['Frames']

    # Velocity
    counts_vel_default, _ = np.histogram(condition_counter['Single ball']['Gaze Velocity'], bins=VEL_BIN_EDGES)
    counts_vel_multiball, _ = np.histogram(condition_counter['Multiball']['Gaze Velocity'], bins=VEL_BIN_EDGES)
    counts_vel_default_normalized = counts_vel_default / counts_vel_default.sum()
    counts_vel_multiball_normalized = counts_vel_multiball / counts_vel_multiball.sum()
    mean_vel_default = np.mean(histogram_to_counts_edges(counts_vel_default_normalized, VEL_BIN_EDGES))
    mean_vel_multiball = np.mean(histogram_to_counts_edges(counts_vel_multiball_normalized, VEL_BIN_EDGES))

    #print(f"Fix: {sorted(condition_counter['Single ball']['Fixation Duration'], reverse=True)[:10]}")
    #print(f"Sac: {sorted(condition_counter['Single ball']['Saccade Duration'], reverse=True)[:10]}")
    #print(f"Pur: {sorted(condition_counter['Single ball']['Pursuit Duration'], reverse=True)[:10]}")
    # TODO: USE AGAIN -------------------------------------------------

    # Flipper distance
    counts_flip_default, _ = np.histogram(condition_counter['Single ball']['Flipper Distance'], bins=FLIPPER_BIN_EDGES)
    counts_flip_multiball, _ = np.histogram(condition_counter['Multiball']['Flipper Distance'], bins=FLIPPER_BIN_EDGES)
    counts_flip_default_normalized = counts_flip_default / counts_flip_default.sum()
    counts_flip_multiball_normalized = counts_flip_multiball / counts_flip_multiball.sum()
    mean_flip_default = np.mean(histogram_to_counts_edges(counts_flip_default_normalized, FLIPPER_BIN_EDGES))
    mean_flip_multiball = np.mean(histogram_to_counts_edges(counts_flip_multiball_normalized, FLIPPER_BIN_EDGES))

    # Ball distance
    counts_ball_default, _ = np.histogram(condition_counter['Single ball']['Ball Distance'], bins=BALL_BIN_EDGES)
    counts_ball_multiball, _ = np.histogram(condition_counter['Multiball']['Ball Distance'], bins=BALL_BIN_EDGES)
    counts_ball_default_normalized = counts_ball_default / counts_ball_default.sum()
    counts_ball_multiball_normalized = counts_ball_multiball / counts_ball_multiball.sum()
    mean_ball_default = np.mean(histogram_to_counts_edges(counts_ball_default_normalized, BALL_BIN_EDGES))
    mean_ball_multiball = np.mean(histogram_to_counts_edges(counts_ball_multiball_normalized, BALL_BIN_EDGES))

    # Fixations
    fixations_per_second_default = len(condition_counter['Single ball']['Fixation Duration']) / time_default
    fixations_per_second_multiball = len(condition_counter['Multiball']['Fixation Duration']) / time_multiball
    counts_fixations_default, _ = np.histogram(condition_counter['Single ball']['Fixation Duration'], bins=FIX_BIN_EDGES)
    counts_fixations_multiball, _ = np.histogram(condition_counter['Multiball']['Fixation Duration'], bins=FIX_BIN_EDGES)
    counts_fixations_default_normalized = counts_fixations_default / counts_fixations_default.sum()
    counts_fixations_multiball_normalized = counts_fixations_multiball / counts_fixations_multiball.sum()
    mean_fix_default = np.mean(histogram_to_counts_edges(counts_fixations_default_normalized, FIX_BIN_EDGES))
    mean_fix_multiball = np.mean(histogram_to_counts_edges(counts_fixations_multiball_normalized, FIX_BIN_EDGES))

    # Saccades
    saccades_per_second_default = len(condition_counter['Single ball']['Saccade Duration']) / time_default
    saccades_per_second_multiball = len(condition_counter['Multiball']['Saccade Duration']) / time_multiball
    counts_saccades_default, _ = np.histogram(condition_counter['Single ball']['Saccade Duration'], bins=SAC_BIN_EDGES)
    counts_saccades_multiball, _ = np.histogram(condition_counter['Multiball']['Saccade Duration'], bins=SAC_BIN_EDGES)
    counts_saccades_default_normalized = counts_saccades_default / counts_saccades_default.sum()
    counts_saccades_multiball_normalized = counts_saccades_multiball / counts_saccades_multiball.sum()
    mean_sac_default = np.mean(histogram_to_counts_edges(counts_saccades_default_normalized, SAC_BIN_EDGES))
    mean_sac_multiball = np.mean(histogram_to_counts_edges(counts_saccades_multiball_normalized, SAC_BIN_EDGES))

    # Pursuits
    pursuits_per_second_default = len(condition_counter['Single ball']['Pursuit Duration']) / time_default
    pursuits_per_second_multiball = len(condition_counter['Multiball']['Pursuit Duration']) / time_multiball
    counts_pursuits_default, _ = np.histogram(condition_counter['Single ball']['Pursuit Duration'], bins=PUR_BIN_EDGES)
    counts_pursuits_multiball, _ = np.histogram(condition_counter['Multiball']['Pursuit Duration'], bins=PUR_BIN_EDGES)
    counts_pursuits_default_normalized = counts_pursuits_default / counts_pursuits_default.sum()
    counts_pursuits_multiball_normalized = counts_pursuits_multiball / counts_pursuits_multiball.sum()
    mean_pur_default = np.mean(histogram_to_counts_edges(counts_pursuits_default_normalized, PUR_BIN_EDGES))
    mean_pur_multiball = np.mean(histogram_to_counts_edges(counts_pursuits_multiball_normalized, PUR_BIN_EDGES))

    stats = {
        'time_total': duration / 1000,
        'time_default': time_default,
        'time_multiball': time_multiball,
        'vel_hist_default': counts_vel_default_normalized.tolist(),
        'vel_hist_multiball': counts_vel_multiball_normalized.tolist(),
        'vel_mean_default': mean_vel_default,
        'vel_mean_multiball': mean_vel_multiball,
        'flip_hist_default': counts_flip_default_normalized.tolist(),
        'flip_hist_multiball': counts_flip_multiball_normalized.tolist(),
        'flip_mean_default': mean_flip_default,
        'flip_mean_multiball': mean_flip_multiball,
        'fix_per_second_default' : fixations_per_second_default,
        'fix_per_second_multiball': fixations_per_second_multiball,
        'fix_hist_default': counts_fixations_default_normalized.tolist(),
        'fix_hist_multiball': counts_fixations_multiball_normalized.tolist(),
        'fix_mean_default': mean_fix_default,
        'fix_mean_multiball': mean_fix_multiball,
        'sac_per_second_default': saccades_per_second_default,
        'sac_per_second_multiball': saccades_per_second_multiball,
        'sac_hist_default': counts_saccades_default_normalized.tolist(),
        'sac_hist_multiball': counts_saccades_multiball_normalized.tolist(),
        'sac_mean_default': mean_sac_default,
        'sac_mean_multiball': mean_sac_multiball,
        'percent_looking_default': percent_looking_default,
        'percent_looking_multiball': percent_looking_multiball,
        'pur_per_second_default': pursuits_per_second_default,
        'pur_per_second_multiball': pursuits_per_second_multiball,
        'pur_hist_default': counts_pursuits_default_normalized.tolist(),
        'pur_hist_multiball': counts_pursuits_multiball_normalized.tolist(),
        'pur_mean_default': mean_pur_default,
        'pur_mean_multiball': mean_pur_multiball,
        'ball_hist_default': counts_ball_default_normalized.tolist(),
        'ball_hist_multiball': counts_ball_multiball_normalized.tolist(),
        'ball_mean_default': mean_ball_default,
        'ball_mean_multiball': mean_ball_multiball
    }

    # Generate survey stats
    participant_survey = []
    for p in resources.participants:
        if p['Name'] == participant:
            participant_survey = p
            break
    
    # NASA-TLX
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

    # Other values
    mistakes = get_survey_value(participant_survey, "Mistakes", 0)
    reflexes = get_survey_value(participant_survey, "Reflexes_1", 0)
    experience_pinball = get_survey_value(participant_survey, "Pinball experience_1", 0)
    prescription = "Yes" if participant_survey.get("Prescription", "") else "No"
    age = get_survey_value(participant_survey, "Age_1", 0)

    global_stats = {
        'TLX_High': TLX_High,
        'TLX_Norm': TLX_Norm,
        'TLX_First': TLX_1_average,
        'TLX_Second': TLX_2_average,
        'Mistakes': mistakes,
        'Reflexes': reflexes,
        'Exp_Pinball': experience_pinball,
        'Glasses': prescription,
        'Age': age
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


def histogram_to_counts_edges(histogram, bin_edges):
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    return histogram_to_counts_centers(histogram, bin_centers)

def histogram_to_counts_centers(histogram, bin_centers):
    hist = np.array(histogram)
    scaled_counts = (hist * 1000).astype(int) # Scale up
    raw_data = np.repeat(bin_centers, scaled_counts)
    return raw_data


def export_stats():
    stats = import_stats()

    # NASA-TLX
    TLX_data = []
    for i, participant in enumerate(stats):
        TLX_data.append([i, "Norm", stats[participant]['global']['TLX_Norm']])
        TLX_data.append([i, "High", stats[participant]['global']['TLX_High']])
    save_csv("stats_TLX.csv", ['Participant', 'Session', 'TLX'], TLX_data)

    # Alt
    TLX_data = []
    for i, participant in enumerate(stats):
        TLX_data.append([i, stats[participant]['global']['TLX_Norm'], stats[participant]['global']['TLX_High']])
    save_csv("stats_TLX_alt.csv", ['Participant', 'Norm', 'High'], TLX_data)

    # Four conditions
    task_keys = ["norm", "high"]
    conditions = ["default", "multiball"]

    values = [
        "percent_looking_", # Look %
        "vel_mean_", # Velocity mean
        "flip_mean_", # Flipper distance mean
        "fix_mean_", # Fixations mean
        "fix_per_second_", # Fixations per second
        "sac_mean_", # Saccades mean
        "sac_per_second_", # Saccades per second
        "pur_mean_", # Pursuits mean
        "pur_per_second_", # Pursuits per second
        "ball_mean_" # Ball distance mean
    ]

    data = []
    for i, participant in enumerate(stats):
        reflexes = stats[participant]["global"]["Reflexes"]
        reflexes_group = "Fast" if reflexes >= 4 else "Slow"
        experience = stats[participant]["global"]["Exp_Pinball"]
        experience_group = "High" if experience >= 2 else "Low"
        glasses = stats[participant]["global"]["Glasses"]
        for condition in conditions:
            for task_key in task_keys:
                condition_name = "Single ball" if condition == "default" else "Multiball"
                entry = [i, task_key.capitalize(), condition_name, experience_group, reflexes_group, glasses]

                # Values
                for value in values:
                    entry.append(stats[participant][task_key][value + condition])

                data.append(entry)
    
    # print means
    for value in values:
        means, medians = [], []
        for condition in conditions:
            for task_key in task_keys:
                data_points = []
                for participant in stats:
                    data_points.append(stats[participant][task_key][value + condition])
                means.append(np.mean(data_points))
                medians.append(np.median(data_points))
        means_str = [str(mean) for mean in means]
        medians_str = [str(median) for median in medians]
        print(f"{value} means:\n{' '.join(means_str)}\n{value} medians:\n{' '.join(medians_str)}\n")
    
    # Export
    value_headers = [
        "Look %",
        "Velocity mean",
        "Flipper dist mean",
        "Fixations mean",
        "Fixations per second",
        "Saccades mean",
        "Saccades per second",
        "Pursuits mean",
        "Pursuits per second",
        "Ball dist mean"
    ]
    save_csv("stats_conditions.csv", ['Participant', 'Session', 'Ball #', 'Experience', 'Reflexes', 'Glasses'] + value_headers, data)
    print(f"Exported stats for {len(stats)} participants")