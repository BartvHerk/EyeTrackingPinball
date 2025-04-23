import math
import numpy as np

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
    tracking_data = interpolate_missing_frames(tracking_data, 5) # Interpolate gaps of at most five frames
    tracking_data = merge_lost_tracks(tracking_data, 5, 200) # Merge detections with different IDs if they belong to the same object
    tracking_data = interpolate_missing_frames(tracking_data, 5) # Interpolate again now that merges have occured
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
    last_detected = {} # track_id : frame
    starts = {} # track_id : frame
    
    for frame in sorted(tracking_data):
        # Find last detected and starts
        detections = tracking_data[frame]
        for detection in detections:
            last = last_detected.get(detection['track_id'], -max_difference_frames)
            if last <= frame - max_difference_frames: # Start found
                starts[detection['track_id']] = frame
            last_detected[detection['track_id']] = frame
        
        # Only keep recent starts
        starts = {k: v for k, v in starts.items() if v >= frame - max_difference_frames * 2}
        
        # Find ends
        for id in last_detected.keys():
            if last_detected[id] <= frame - max_difference_frames: # End found
                candidates = {} # track_id : distance
                for id_start in starts.keys():
                    if id_start == id:
                        continue

                    # Merging candidate found (id and id_start)
                    frame_swap = (last_detected[id] + starts[id_start]) / 2 # Doesn't have to be an int
                    pos_end = track_position(tracking_data, id, frame_swap)
                    pos_start = track_position(tracking_data, id_start, frame_swap)
                    if (pos_end is None or pos_start is None):
                        continue
                    candidates[id_start] = math.dist(pos_end, pos_start)
                if not candidates:
                    continue
                closest_id = min(candidates, key=candidates.get)
                if candidates[closest_id] <= max_merge_distance:
                    # Merge (id_start becomes id)
                    print(f"Merged {id} and {id_start} (around frame {frame_swap}) with distance {candidates[closest_id]}")
                    for detections in tracking_data.values():
                        for det in detections:
                            if det['track_id'] == id_start:
                                det['track_id'] = id
                    last_detected[id] = max(last_detected[id], starts[id_start])
                    starts.pop(id_start)

    return tracking_data


def track_position(tracking_data, track_id, frame):
    # Collect all detections for the given track_id
    detections = []
    for frame_idx in tracking_data:
        for det in tracking_data[frame_idx]:
            if det['track_id'] == track_id:
                detections.append((frame_idx, det))
    detections.sort(key=lambda x: x[0])
    if not detections:
        return None
    if len(detections) == 1:
        return (detections[0][1]['cx'], detections[0][1]['cy'])

    # If an exact match exists, return directly
    for frame_idx, det in detections:
        if frame_idx == frame:
            return (det['cx'], det['cy'])

    # Find two detections closest to the target frame for interpolation or extrapolation
    before, after = None, None
    for i in range(len(detections) - 1):
        f1, d1 = detections[i]
        f2, d2 = detections[i + 1]
        if f1 <= frame <= f2:
            before = (f1, d1)
            after = (f2, d2)
            break

    # If frame is outside the detection range, use the two nearest endpoints
    if before is None or after is None:
        if frame < detections[0][0]:
            before, after = detections[0], detections[1]
        elif frame > detections[-1][0]:
            before, after = detections[-2], detections[-1]

    f1, d1 = before
    f2, d2 = after
    alpha = (frame - f1) / (f2 - f1)

    x = d1['cx'] * (1 - alpha) + d2['cx'] * alpha
    y = d1['cy'] * (1 - alpha) + d2['cy'] * alpha

    return (x, y)
