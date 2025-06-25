from containers import ContRecording
from video import Video


def generate_field_conditions(recording:ContRecording):
    # Timing
    videoField = Video(recording.paths['VideoField'])

    # Conditions (single ball, multiball)
    condition_windows = extract_condition_windows(recording.tracking_data)
    is_condition_true = condition_check_factory(condition_windows)

    # Iterate through recording
    conditions = []
    for i in range(videoField.frame_count):
        conditions_dict = {}

        condition = ""
        condition = "Single ball" if is_condition_true('condition_default', i) else condition
        condition = "Multiball" if is_condition_true('condition_multiball', i) else condition
        conditions_dict['condition'] = condition
        conditions_dict['has_detection'] = len(recording.tracking_data.get(i, [])) > 0

        conditions.append(conditions_dict)

    # Free memory
    videoField.destroy()
    return conditions


# Build condition data structure
def extract_condition_windows(tracking_data, max_gap=60):
    from collections import defaultdict

    condition_settings = {
        'condition_default': {'max_gap': 60, 'min_duration': 0},
        'condition_multiball': {'max_gap': 100, 'min_duration': 300},
    }

    # Get all frame indices sorted
    all_frames = sorted(tracking_data.keys())
    condition_frames = {
        'condition_default': set(),
        'condition_multiball': set(),
    }

    # Determine which frames qualify for each condition
    for frame in all_frames:
        detections = tracking_data.get(frame, [])
        count = len(detections)
        if count >= 1:
            condition_frames['condition_default'].add(frame)
        if count >= 2:
            condition_frames['condition_multiball'].add(frame)

    # Build windows with condition-specific settings
    def build_windows(frames_set, max_gap, min_duration):
        sorted_frames = sorted(frames_set)
        windows = []
        if not sorted_frames:
            return windows

        start = sorted_frames[0]
        prev = start

        for f in sorted_frames[1:]:
            if f - prev > max_gap:
                if prev - start + 1 >= min_duration:
                    windows.append((start, prev))
                start = f
            prev = f

        if prev - start + 1 >= min_duration:
            windows.append((start, prev))

        return windows

    condition_windows = {}
    for cond, frames in condition_frames.items():
        settings = condition_settings.get(cond, {})
        max_gap = settings.get('max_gap', 60)
        min_duration = settings.get('min_duration', 0)
        condition_windows[cond] = build_windows(frames, max_gap, min_duration)

    return condition_windows


# Returns polling function
def condition_check_factory(condition_windows):
    from bisect import bisect_right

    # Preprocess time windows into list of start and end points for binary search
    window_index = {}
    for cond, windows in condition_windows.items():
        starts = [start for start, _ in windows]
        ends = [end for _, end in windows]
        window_index[cond] = (starts, ends)

    def is_condition_true(condition_name, frame):
        starts, ends = window_index.get(condition_name, ([], []))
        idx = bisect_right(starts, frame) - 1
        if 0 <= idx < len(ends):
            return starts[idx] <= frame <= ends[idx]
        return False

    return is_condition_true