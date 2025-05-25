import math
import statistics
import numpy as np
from collections import defaultdict
from scipy.interpolate import CubicSpline, interp1d
import bisect

from containers import ContExport


MAX_GAP_DURATION = 100


def process_data(export:ContExport):
    convert_to_numerics(export)
    interpolate_mapped_gaze_gaps(export)
    generate_perspective_mapped_data(export)


def convert_to_numerics(export:ContExport):
    for row in export.data:
        row['Timestamp'] = int(row['Timestamp']) # Timestamp can always convert
        row['Gaze X'] = convert(row['Gaze X'], int)
        row['Gaze Y'] = convert(row['Gaze Y'], int)
        row['Interpolated Gaze X'] = convert(row['Interpolated Gaze X'], float)
        row['Interpolated Gaze Y'] = convert(row['Interpolated Gaze Y'], float)
        row['Mapped Gaze X'] = convert(row['Mapped Gaze X'], int)
        row['Mapped Gaze Y'] = convert(row['Mapped Gaze Y'], int)


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


def has_mapped_gaze(row) -> bool:
    return (row['Mapped Gaze X'] is not None) and (row['Mapped Gaze Y'] is not None)


def process_tracking_data(tracking_data): # TODO: Add more processing
    if not tracking_data:
        return tracking_data
    
    tracking_data = split_tracks(tracking_data, 10)
    tracking_data = interpolate_gaps(tracking_data)
    
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


def interpolate_gaps(tracking_data):
    print("Interpolating tracks... ", end='', flush=True)

    # Group detections by track_id
    track_detections = defaultdict(list)
    for frame_idx, detections in tracking_data.items():
        for det in detections:
            track_detections[det['track_id']].append((frame_idx, det))

    for track_id, dets in track_detections.items():
        if len(dets) < 3:
            continue  # Not enough data to interpolate smoothly

        # Sort detections by frame
        dets.sort(key=lambda x: x[0])

        # Filter out duplicate frames (keep only first per frame)
        unique_dets = {}
        for f, d in dets:
            if f not in unique_dets:
                unique_dets[f] = d
        if len(unique_dets) < 2:
            continue

        sorted_unique = sorted(unique_dets.items())
        frames = [f for f, _ in sorted_unique]
        cxs = [d['cx'] for _, d in sorted_unique]
        cys = [d['cy'] for _, d in sorted_unique]
        radii = [d.get('radius', 0.0) for _, d in sorted_unique]
        confs = [d.get('confidence', 1.0) for _, d in sorted_unique]

        existing_frames = set(frames)
        frame_range = range(frames[0], frames[-1] + 1)

        # Interpolators
        spline_x = CubicSpline(frames, cxs, bc_type='natural')
        spline_y = CubicSpline(frames, cys, bc_type='natural')
        linear_radius = interp1d(frames, radii, kind='linear', fill_value="extrapolate")
        linear_conf = interp1d(frames, confs, kind='linear', fill_value="extrapolate")

        for f in frame_range:
            if f not in existing_frames:
                cx = float(spline_x(f))
                cy = float(spline_y(f))
                radius = float(linear_radius(f))
                conf = float(linear_conf(f))

                interpolated_det = {
                    'track_id': track_id,
                    'cx': cx,
                    'cy': cy,
                    'radius': radius,
                    'confidence': conf,
                    'interpolated': True
                }
                if f not in tracking_data:
                    tracking_data[f] = []
                tracking_data[f].append(interpolated_det)

    print("Done")
    return tracking_data


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
                    }

                    if interp_frame not in output_data:
                        output_data[interp_frame] = []
                    output_data[interp_frame].append(interp_det)

    return output_data


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