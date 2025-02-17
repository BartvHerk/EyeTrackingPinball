from interface import Interface
from IO import import_specifications, import_references, import_recordings, import_export_csv
from video import display_video_raw, display_video_gaze_mapped
from homography import set_perspective_mapping, perspective_map


# Import relevant data
specifications = import_specifications()
field_dimensions = float(specifications['field']['width']), float(specifications['field']['height'])
references = import_references()

# Start interface
Interface()





# set_perspective_mapping(references['IMG_20241210_154127'], field_dimensions)

recordings = import_recordings()
export = import_export_csv(recordings[0].paths["Export"], references)
# display_video_gaze_mapped(export)
# display_video_raw(recordings[0].paths["Video"], export)

# print(f"timestamps: {len(export.data)}")

# container = import_export_csv('data/recordings/Jesse1/Export.csv')
# xMax = -100000
# xMin = 100000
# yMax = -100000
# yMin = 100000
# for row in container.data:
#     try:
#         xMax = max(xMax, int(row['Mapped Gaze X']))
#         xMin = min(xMin, int(row['Mapped Gaze X']))
#         yMax = max(yMax, int(row['Mapped Gaze Y']))
#         yMin = min(yMin, int(row['Mapped Gaze Y']))
#     except:
#         continue
# print(f"X: {xMin}-{xMax}, Y: {yMin}-{yMax}")