import numpy as np
from containers import ContExport


MAX_GAP_DURATION = 100


def process_data(export:ContExport):
    convert_to_numerics(export)
    interpolate_mapped_gaze_gaps(export)
    print(export.data[100]['Mapped Gaze X'])


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
    def has_mapped_gaze(row):
        return (row['Mapped Gaze X'] is not None) and (row['Mapped Gaze Y'] is not None)

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