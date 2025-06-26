PURSUIT_THRESHOLD = 0.3
MAX_GAP = 20


def get_pursuit_data(tracking_data):
    pursuits = {}

    current_track_id = None
    frame_start = None
    last_valid_frame = None

    # Ensure frames are processed in order
    sorted_frames = sorted(tracking_data.keys())

    for frame_idx in sorted_frames:
        detections = tracking_data[frame_idx]

        # Find detections with pursuit score >= threshold
        strong_dets = [d for d in detections if d.get('pursuit_score', 0.0) >= PURSUIT_THRESHOLD]

        # If there are no qualifying detections on this frame
        if not strong_dets:
            if current_track_id is not None and (frame_idx - last_valid_frame) > MAX_GAP:
                # Close current pursuit
                duration = last_valid_frame - frame_start + 1
                pursuits[frame_start] = (duration, current_track_id)
                current_track_id = None
                frame_start = None
                last_valid_frame = None
            continue

        # Select best-scoring pursuit detection on this frame
        best_det = max(strong_dets, key=lambda d: d.get('pursuit_score', 0.0))
        track_id = best_det['track_id']

        if current_track_id is None:
            # Start new pursuit
            current_track_id = track_id
            frame_start = frame_idx
            last_valid_frame = frame_idx
        elif track_id == current_track_id:
            # Continue current pursuit
            last_valid_frame = frame_idx
        else:
            # New pursuit found — close current one
            duration = last_valid_frame - frame_start + 1
            pursuits[frame_start] = (duration, current_track_id)
            # Start new pursuit
            current_track_id = track_id
            frame_start = frame_idx
            last_valid_frame = frame_idx

    # Final check at the end of data
    if current_track_id is not None:
        duration = last_valid_frame - frame_start + 1
        pursuits[frame_start] = (duration, current_track_id)

    return pursuits