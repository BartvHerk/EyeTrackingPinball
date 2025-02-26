from interface.interface import Interface


# Start interface
Interface()







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