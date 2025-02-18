import cv2

from containers import ContExport
from openCV import resize_image_to_fit, draw_gaze_circle


def display_video_raw(path, export:ContExport):
    cap = cv2.VideoCapture(path)
    csv_timestamp = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Scale down if needed
        frame, scale_factor = resize_image_to_fit(frame)

        # Draw gaze dot
        video_timestamp = cap.get(cv2.CAP_PROP_POS_MSEC)
        while (export.data[csv_timestamp + 1]['Timestamp'] <= video_timestamp):
            csv_timestamp += 1
        try:
            gaze_x = export.data[csv_timestamp]['Interpolated Gaze X']
            gaze_y = export.data[csv_timestamp]['Interpolated Gaze Y']
            gaze_position = (gaze_x * scale_factor, gaze_y * scale_factor)
            draw_gaze_circle(frame, gaze_position)
        except:
            pass

        # Show frame
        cv2.imshow('Video', frame)
        
        # Advance and close video
        cv2.waitKey(20)
        if cv2.getWindowProperty('Video', cv2.WND_PROP_VISIBLE) < 1:
            break

    cap.release()
    cv2.destroyAllWindows()


def display_video_gaze_mapped(export:ContExport):
    if export.reference == None:
        print('Error: Export did not reference an image')
        return
    reference_image = export.reference.image
    height, width = reference_image.shape[:2]
    data_width, data_height = export.reference_dimensions
    ms_per_frame = 100
    video_timestamp = 0
    csv_timestamp = 0
    scaled_reference, scale_factor = resize_image_to_fit(reference_image.copy())
    
    while True:
        frame = scaled_reference.copy()

        # Draw gaze dot
        while (export.data[csv_timestamp + 1]['Timestamp'] <= video_timestamp):
            csv_timestamp += 1
        try:
            # print(f'From [{export.data[csv_timestamp]['Interpolated Gaze X']}, {export.data[csv_timestamp]['Interpolated Gaze Y']}] to [{export.data[csv_timestamp]['Mapped Gaze X']}, {export.data[csv_timestamp]['Mapped Gaze Y']}]')
            mapped_gaze_x = export.data[csv_timestamp]['Mapped Gaze X'] / data_width * width
            mapped_gaze_y = export.data[csv_timestamp]['Mapped Gaze Y'] / data_height * height
            gaze_position = (mapped_gaze_x * scale_factor, mapped_gaze_y * scale_factor)
            draw_gaze_circle(frame, gaze_position)
        except:
            pass

        # Show frame
        cv2.imshow('Video', frame)

        # Advance and close
        video_timestamp += ms_per_frame
        cv2.waitKey(20)
        if cv2.getWindowProperty('Video', cv2.WND_PROP_VISIBLE) < 1:
            break
    
    cv2.destroyAllWindows()