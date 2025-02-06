from IO import gather_data, import_csv_gazemap, display_video_with_gazemap


recordings = gather_data()
gazemap = import_csv_gazemap(recordings[1].paths["Gazemap"])
display_video_with_gazemap(recordings[1].paths["Video"], gazemap)

# print(f"timestamps: {len(gazemap.data)}")


# container = import_csv_gazemap('data/recordings/Jesse1/export.csv')
# xMax = -100000
# xMin = 100000
# yMax = -100000
# yMin = 100000
# for row in container.data:
#     try:
#         xMax = max(xMax, int(row['Gaze X']))
#         xMin = min(xMin, int(row['Gaze X']))
#         yMax = max(yMax, int(row['Gaze Y']))
#         yMin = min(yMin, int(row['Gaze Y']))
#     except:
#         continue
# print(f"X: {xMin}-{xMax}, Y: {yMin}-{yMax}")
# print(container.data[0])