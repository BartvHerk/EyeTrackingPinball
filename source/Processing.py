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
    return tracking_data


def interpolate_mising_frames(tracking_data, max_gap_frames):
    last_frame_spotted = {} # Dictionary of the last frame each id was seen
    i = 0
    while i < len(tracking_data):

        i += 1
