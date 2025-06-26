import copy
import math
import statistics
import numpy as np
from collections import defaultdict
from scipy.interpolate import CubicSpline, interp1d
import bisect

from containers import ContExport, ContRecording
from homography import perspective_map
from video import Video


MAX_GAP_DURATION = 100
VELOCITY_FRAME_WINDOW = 4
PURSUIT_SCORE_DIST = 30
PURSUIT_VEL_THRESHOLD = 50


def process_data(export:ContExport):
    convert_to_numerics(export)
    interpolate_mapped_gaze_gaps(export)
    generate_perspective_mapped_data(export)
    generate_perspective_mapped_velocity(export)


def convert_to_numerics(export:ContExport):
    for row in export.data:
        row['Timestamp'] = int(row['Timestamp']) # Timestamp can always convert
        row['Gaze X'] = convert(row['Gaze X'], int)
        row['Gaze Y'] = convert(row['Gaze Y'], int)
        row['Interpolated Gaze X'] = convert(row['Interpolated Gaze X'], float)
        row['Interpolated Gaze Y'] = convert(row['Interpolated Gaze Y'], float)
        row['Mapped Gaze X'] = convert(row['Mapped Gaze X'], int)
        row['Mapped Gaze Y'] = convert(row['Mapped Gaze Y'], int)
        row['Gaze Velocity'] = convert(row['Gaze Velocity'], float)
        row['Fixation Index'] = convert(row['Fixation Index'], int)
        row['Fixation Duration'] = convert(row['Fixation Duration'], float)
        row['Saccade Index'] = convert(row['Saccade Index'], int)
        row['Saccade Duration'] = convert(row['Saccade Duration'], float)


def convert(value: str, type):
    try:
        return type(value)
    except:
        return None


def interpolate_mapped_gaze_gaps(export:ContExport):
    i_last = next((i for i, x in enumerate(export.data) if (lambda x: has_mapped_gaze(x))(x)), len(export.data))
    i = i_last + 1
    while i < len(export.data):
        if has_mapped_gaze(export.data[i]):
            gap_length = i - i_last - 1
            gap_duration = export.data[i]['Timestamp'] - export.data[i_last]['Timestamp']
            if (gap_duration <= MAX_GAP_DURATION):
                for g in range(gap_length):
                    step = i_last + 1 + g
                    t = (export.data[step]['Timestamp'] - export.data[i_last]['Timestamp']) / (export.data[i]['Timestamp'] - export.data[i_last]['Timestamp'])
                    x = np.interp(t, [0, 1], [export.data[i_last]['Mapped Gaze X'], export.data[i]['Mapped Gaze X']])
                    y = np.interp(t, [0, 1], [export.data[i_last]['Mapped Gaze Y'], export.data[i]['Mapped Gaze Y']])
                    export.data[step]['Mapped Gaze X'] = x
                    export.data[step]['Mapped Gaze Y'] = y
            i_last = i
        i += 1


def generate_perspective_mapped_data(export:ContExport):
    from homography import perspective_map
    H = export.reference.H
    reference_image_height, reference_image_width = export.reference.image.shape[:2]
    x_scale = (reference_image_width / export.reference_dimensions[0])
    y_scale = (reference_image_height / export.reference_dimensions[1])
    for row in export.data:
        x, y = None, None
        if has_mapped_gaze(row):
            x, y = perspective_map(H, (row['Mapped Gaze X'] * x_scale, row['Mapped Gaze Y'] * y_scale))
        row['Perspective Gaze X'] = x
        row['Perspective Gaze Y'] = y


def generate_perspective_mapped_velocity(export:ContExport):
    data = export.data
    n = len(data)
    
    # Precompute valid velocity pairs
    velocity_pairs = []
    for i in range(n - 1):
        v = None
        curr = data[i]
        next_ = data[i + 1]
        if (curr['Perspective Gaze X'] is not None and next_['Perspective Gaze X'] is not None and
            curr['Perspective Gaze Y'] is not None and next_['Perspective Gaze Y'] is not None):
            dt = (next_['Timestamp'] - curr['Timestamp']) / 1000.0
            if dt > 0:
                dx = (next_['Perspective Gaze X'] - curr['Perspective Gaze X']) / dt
                dy = (next_['Perspective Gaze Y'] - curr['Perspective Gaze Y']) / dt
                v = (dx, dy)
        velocity_pairs.append(v)

    # Compute average velocity using surrounding valid velocity pairs
    for i in range(n):
        sum_dx = 0.0
        sum_dy = 0.0
        count = 0
        for offset in range(-VELOCITY_FRAME_WINDOW, VELOCITY_FRAME_WINDOW):
            j = i + offset
            if 0 <= j < n - 1:
                v = velocity_pairs[j]
                if v is not None:
                    sum_dx += v[0]
                    sum_dy += v[1]
                    count += 1
        if count > 0:
            data[i]['Gaze Velocity X'] = sum_dx / count
            data[i]['Gaze Velocity Y'] = sum_dy / count
        else:
            data[i]['Gaze Velocity X'] = None
            data[i]['Gaze Velocity Y'] = None


def has_mapped_gaze(row) -> bool:
    return (row['Mapped Gaze X'] is not None) and (row['Mapped Gaze Y'] is not None)


def process_tracking_data(tracking_data, recording:ContRecording):
    if not tracking_data:
        return tracking_data
    
    tracking_data = perspective_map_tracking(tracking_data, recording.H)
    tracking_data = split_tracks(tracking_data, 10)
    tracking_data = interpolate_missing_frames(tracking_data, 20)
    tracking_data = remove_duplicate_detections(tracking_data)
    tracking_data = add_velocities_to_tracking_data(tracking_data, 60)
    tracking_data = generate_pursuit_scores(tracking_data, recording)
    tracking_data = determine_best_pursuit(tracking_data)
    tracking_data = smooth_pursuit_scores(tracking_data)
    
    # print("Postprocessing...")
    # tracking_data = interpolate_missing_frames(tracking_data, 5) # Interpolate gaps of at most five frames
    # tracking_data = merge_lost_tracks(tracking_data, 5, 20) # Merge detections with different IDs if they belong to the same object
    # tracking_data = interpolate_missing_frames(tracking_data, 10) # Interpolate again now that merges have occured
    # print("Finished postprocessing")

    return tracking_data


def split_tracks(tracking_data, max_gap):
    from collections import defaultdict
    print("Splitting tracks... ", end='', flush=True)

    # Collect track_ids and group detections
    used_ids = set()
    for detections in tracking_data.values():
        for det in detections:
            used_ids.add(det['track_id'])
    track_detections = defaultdict(list)
    for frame_idx, detections in tracking_data.items():
        for det in detections:
            track_detections[det['track_id']].append((frame_idx, det))
    for det_list in track_detections.values():
        det_list.sort(key=lambda x: x[0])

    # Process each track
    next_unused_id = max(used_ids) + 1 if used_ids else 0
    new_tracking_data = defaultdict(list)
    for old_id, dets in track_detections.items():
        current_id = old_id
        last_frame = None
        for frame_idx, det in dets:
            if last_frame is not None and frame_idx - last_frame > max_gap:
                current_id = next_unused_id
                # print(f"Split: original ID {old_id} → new ID {current_id} at frame {frame_idx} (gap: {frame_idx - last_frame})")
                next_unused_id += 1
            det['track_id'] = current_id
            new_tracking_data[frame_idx].append(det)
            last_frame = frame_idx

    print("Done")
    return new_tracking_data


def remove_low_confidence(tracking_data, threshold):
    filtered_data = {}

    for frame_idx, detections in tracking_data.items():
        # Filter detections for this frame
        filtered_detections = [det for det in detections if det['confidence'] >= threshold]
        if filtered_detections:
            filtered_data[frame_idx] = filtered_detections

    return filtered_data


def interpolate_missing_frames(tracking_data, max_gap_frames):
    from collections import defaultdict
    print("Interpolating gaps... ", end='', flush=True)

    # Gather all detections by track_id
    tracks = defaultdict(list)
    for frame_idx, detections in tracking_data.items():
        for det in detections:
            tracks[det['track_id']].append((frame_idx, det))

    # Start with a shallow copy of the original tracking data
    output_data = {frame_idx: list(dets) for frame_idx, dets in tracking_data.items()}

    for track_id, detections in tracks.items():
        # Sort detections for this track by frame index
        detections.sort(key=lambda x: x[0])

        for i in range(len(detections) - 1):
            frame1, det1 = detections[i]
            frame2, det2 = detections[i + 1]
            gap = frame2 - frame1 - 1

            # Interpolate only if there is at least 1 missing frame and the gap is within the allowed max
            if gap <= max_gap_frames:
                for f in range(1, gap + 1):
                    interp_frame = frame1 + f
                    alpha = f / (frame2 - frame1)

                    interp_det = {
                        'track_id': track_id,
                        'confidence': min(det1['confidence'], det2['confidence']),
                        'cx': det1['cx'] * (1 - alpha) + det2['cx'] * alpha,
                        'cy': det1['cy'] * (1 - alpha) + det2['cy'] * alpha,
                        'radius': det1['radius'] * (1 - alpha) + det2['radius'] * alpha,
                        # 'interpolated': True
                    }

                    if interp_frame not in output_data:
                        output_data[interp_frame] = []
                    output_data[interp_frame].append(interp_det)

    print("Done")
    return output_data


def remove_duplicate_detections(tracking_data):
    print("Removing duplicate detections per frame... ", end='', flush=True)

    for frame, detections in tracking_data.items():
        # Group detections by track_id
        track_groups = defaultdict(list)
        for det in detections:
            track_groups[det['track_id']].append(det)

        # Keep only the highest-confidence detection for each track_id
        filtered_detections = []
        for track_id, dets in track_groups.items():
            if len(dets) == 1:
                filtered_detections.append(dets[0])
            else:
                best_det = max(dets, key=lambda d: d.get('confidence', 1.0))
                filtered_detections.append(best_det)

        tracking_data[frame] = filtered_detections

    print("Done")
    return tracking_data


def add_velocities_to_tracking_data(tracking_data, fps):
    print("Computing velocities... ", end='', flush=True)
    from collections import defaultdict

    track_index = defaultdict(list)
    for frame_idx, detections in tracking_data.items():
        for det in detections:
            track_index[det['track_id']].append((frame_idx, det))

    for _, detections in track_index.items():
        # Sort detections by frame
        detections.sort(key=lambda x: x[0])

        frame_to_det = {frame: det for frame, det in detections}
        frames = sorted(frame_to_det.keys())

        for i, frame in enumerate(frames):
            current = frame_to_det[frame]

            prev = frame_to_det.get(frames[i - 1]) if i > 0 else None
            next_ = frame_to_det.get(frames[i + 1]) if i < len(frames) - 1 else None

            if prev and next_:
                # Use central difference
                dt = (frames[i + 1] - frames[i - 1]) / fps
                vx = (next_['cx'] - prev['cx']) / dt
                vy = (next_['cy'] - prev['cy']) / dt
            elif prev:
                dt = (frame - frames[i - 1]) / fps
                vx = (current['cx'] - prev['cx']) / dt
                vy = (current['cy'] - prev['cy']) / dt
            elif next_:
                dt = (frames[i + 1] - frame) / fps
                vx = (next_['cx'] - current['cx']) / dt
                vy = (next_['cy'] - current['cy']) / dt
            else:
                vx, vy = 0.0, 0.0

            current['vx'] = vx
            current['vy'] = vy

    print("Done")
    return tracking_data


def generate_pursuit_scores(tracking_data, recording:ContRecording):
    print("Generating pursuit scores... ", end='', flush=True)
    export = recording.export
    data = export.data
    videoWorld = Video(recording.paths['VideoWorld'])
    videoField = Video(recording.paths['VideoField'])
    start_world = recording.metadata.get('start_world', 0)
    start_field = recording.metadata.get('start_field', 0)
    export_index = 0
    for index in sorted(tracking_data.keys()):
        timestamp = (index / videoField.frame_count) * videoField.duration - start_field
        detections = tracking_data[index]
        for detection in detections:
                detection['pursuit_score'] = 0 # Default

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

        # Gaze position and velocity
        pos_gaze_x = export.get_val('Perspective Gaze X', export_index, t)
        pos_gaze_y = export.get_val('Perspective Gaze Y', export_index, t)
        vel_gaze_x = export.get_val('Gaze Velocity X', export_index, t)
        vel_gaze_y = export.get_val('Gaze Velocity Y', export_index, t)
        if pos_gaze_x is None or pos_gaze_y is None or vel_gaze_x is None or vel_gaze_y is None:
            continue

        # Calculate pursuit score
        for detection in detections:
            distance = math.dist([detection['cx'], detection['cy']], [pos_gaze_x, pos_gaze_y])
            distance_score = max((PURSUIT_SCORE_DIST - distance) / PURSUIT_SCORE_DIST, 0)

            vel_gaze_magnitude = math.dist([0, 0], [vel_gaze_x, vel_gaze_y])
            vel_gaze_normalized = normalize_vector([vel_gaze_x, vel_gaze_y])
            vel_ball_magnitude = math.dist([0, 0], [detection['vx'], detection['vy']])
            vel_ball_normalized = normalize_vector([detection['vx'], detection['vy']])
            dot_product = np.dot(vel_gaze_normalized, vel_ball_normalized)
            alignment_score = (dot_product + 1) / 2
            velocity_grace = max((PURSUIT_VEL_THRESHOLD - min(vel_gaze_magnitude, vel_ball_magnitude)) / PURSUIT_VEL_THRESHOLD, 0)
            velocity_score = max(alignment_score, velocity_grace)

            pursuit_score = distance_score * velocity_score
            detection['pursuit_score'] = pursuit_score

    # Free memory
    videoWorld.destroy()
    videoField.destroy()

    print("Done")
    return tracking_data


def determine_best_pursuit(tracking_data):
    print("Determining best pursuit per frame... ", end='', flush=True)

    for _, detections in tracking_data.items():
        if not detections:
            continue

        # Find the detection with the highest pursuit score
        best_det = max(detections, key=lambda d: d.get('pursuit_score', 0.0))

        # Set all other scores to 0, unless they match the best
        for det in detections:
            if det is not best_det:
                det['pursuit_score'] = 0.0

    print("Done")
    return tracking_data


def smooth_pursuit_scores(tracking_data, window_size=15, pursuit_threshold=0.3):
    print("Smoothing pursuit scores... ", end='', flush=True)
    
    half_window = window_size // 2
    new_tracking_data = copy.deepcopy(tracking_data)

    # Group detections by track_id
    track_detections = defaultdict(list)
    for frame_idx, detections in tracking_data.items():
        for det in detections:
            track_detections[det['track_id']].append((frame_idx, det))

    for track_id, detections in track_detections.items():
        if len(detections) < 2:
            continue

        # Sort by frame
        detections.sort(key=lambda x: x[0])
        frames = [f for f, _ in detections]
        det_by_frame = {f: d for f, d in detections}

        for i in range(len(frames)):
            center_frame = frames[i]
            # Define window range
            window_frames = frames[max(0, i - half_window):min(len(frames), i + half_window + 1)]

            window_scores = [det_by_frame[f].get('pursuit_score', 0.0) for f in window_frames]
            avg_score = sum(window_scores) / len(window_scores)
            smoothed_score = max(window_scores) if avg_score >= pursuit_threshold else 0.0

            # Update ONLY the center frame in the copy
            if center_frame in new_tracking_data:
                for d in new_tracking_data[center_frame]:
                    if d['track_id'] == track_id:
                        d['pursuit_score'] = smoothed_score

    print("Done")
    return new_tracking_data


def normalize_vector(vector):
    vec = np.array(vector)
    norm = np.linalg.norm(vec)
    if norm == 0:
        return vec  # Avoid division by zero for a zero vector
    return vec / norm


def perspective_map_tracking(tracking_data, H):
    print("Perspective mapping... ", end='', flush=True)

    def map_position(cx, cy):
        return perspective_map(H, (cx, cy))

    for frame_idx, detections in tracking_data.items():
        for det in detections:
            det['cx'], det['cy'] = map_position(det['cx'], det['cy'])

    print("Done")
    return tracking_data


def merge_lost_tracks(tracking_data, max_difference_frames, max_merge_distance):
    print("Merging tracks...")

    frames_total = max(tracking_data)
    last_detected = {}
    starts = {}
    track_detections = defaultdict(lambda: {'frames': [], 'detections': []})

    # Organize and sort detections by track_id
    for frame_idx, detections in tracking_data.items():
        for det in detections:
            track_detections[det['track_id']]['frames'].append(frame_idx)
            track_detections[det['track_id']]['detections'].append(det)

    # Sort the frames and detections in sync
    for data in track_detections.values():
        paired = sorted(zip(data['frames'], data['detections']), key=lambda x: x[0])
        data['frames'], data['detections'] = zip(*paired)

    def interpolate_position(track_id, frame):
        data = track_detections.get(track_id)
        if not data or len(data['frames']) < 2:
            return None

        frames = data['frames']
        detections = data['detections']

        idx = bisect.bisect_left(frames, frame)

        if idx == 0:
            f1, f2 = frames[0], frames[1]
            d1, d2 = detections[0], detections[1]
        elif idx >= len(frames):
            f1, f2 = frames[-2], frames[-1]
            d1, d2 = detections[-2], detections[-1]
        else:
            f1, f2 = frames[idx - 1], frames[idx]
            d1, d2 = detections[idx - 1], detections[idx]

        alpha = (frame - f1) / (f2 - f1) if f2 != f1 else 0
        x = d1['cx'] * (1 - alpha) + d2['cx'] * alpha
        y = d1['cy'] * (1 - alpha) + d2['cy'] * alpha
        return (x, y)

    for frame in range(frames_total + 1):
        detections = tracking_data.get(frame, [])
        for det in detections:
            last = last_detected.get(det['track_id'], -max_difference_frames)
            if last <= frame - max_difference_frames:
                starts[det['track_id']] = frame
            last_detected[det['track_id']] = frame

        starts = {k: v for k, v in starts.items() if v >= frame - 2 * max_difference_frames}

        for id_end in list(last_detected):
            if last_detected[id_end] <= frame - max_difference_frames:
                candidates = {}
                for id_start, start_frame in starts.items():
                    if id_start == id_end:
                        continue

                    frame_swap = (last_detected[id_end] + start_frame) / 2
                    pos_end = interpolate_position(id_end, frame_swap)
                    pos_start = interpolate_position(id_start, frame_swap)
                    if pos_end is None or pos_start is None:
                        continue
                    distance = math.dist(pos_end, pos_start)
                    candidates[id_start] = distance

                if candidates:
                    closest_id = min(candidates, key=candidates.get)
                    if candidates[closest_id] <= max_merge_distance:
                        # Merge closest_id into id_end
                        frames_to_merge = track_detections.pop(closest_id)
                        track_detections[id_end]['frames'] += frames_to_merge['frames']
                        track_detections[id_end]['detections'] += frames_to_merge['detections']

                        # Sort merged data
                        paired = sorted(zip(track_detections[id_end]['frames'], track_detections[id_end]['detections']), key=lambda x: x[0])
                        track_detections[id_end]['frames'], track_detections[id_end]['detections'] = zip(*paired)

                        # Update detections in original tracking_data
                        for f, det in zip(frames_to_merge['frames'], frames_to_merge['detections']):
                            for d in tracking_data[f]:
                                if d is det:
                                    d['track_id'] = id_end
                                    break

                        last_detected[id_end] = max(last_detected[id_end], starts[closest_id])
                        starts.pop(closest_id, None)

        print(f"{frame + 1}/{frames_total + 1}", end='\r', flush=True)

    print("Finished merging tracks")
    return tracking_data

    from collections import defaultdict

    def frame_to_timestamp(frame, fps):
        total_seconds = frame / fps
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)
        milliseconds = int((total_seconds % 1) * 1000)
        return f"{minutes}:{seconds:02}:{milliseconds:03}"

    # Step 1: Collect first and last detection frames for each track_id
    track_ranges = defaultdict(lambda: [float('inf'), float('-inf')])  # [start, end]

    for frame_idx, detections in tracking_data.items():
        for det in detections:
            track_id = det['track_id']
            track_ranges[track_id][0] = min(track_ranges[track_id][0], frame_idx)
            track_ranges[track_id][1] = max(track_ranges[track_id][1], frame_idx)

    # Step 2: Sort track_ids by start frame
    sorted_tracks = sorted(track_ranges.items(), key=lambda x: x[1][0])  # sort by start frame

    # Step 3: Calculate and print gap sizes with timestamp
    for i in range(len(sorted_tracks) - 1):
        current_id, (start1, end1) = sorted_tracks[i]
        next_id, (start2, end2) = sorted_tracks[i + 1]
        gap = start2 - end1 - 1
        timestamp = frame_to_timestamp(start1, fps)
        print(f"id: {current_id}, gap: {gap}, time: {timestamp}")