from IO import gather_references, gather_data, import_csv_gazemap, display_video_raw, display_video_gaze_mapped


references = gather_references()
recordings = gather_data()
gazemap = import_csv_gazemap(recordings[0].paths["Gazemap"])
display_video_gaze_mapped(references, gazemap)
# display_video_raw(recordings[0].paths["Video"], gazemap)

# print(f"timestamps: {len(gazemap.data)}")

# container = import_csv_gazemap('data/recordings/Jesse1/Export.csv')
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