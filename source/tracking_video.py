import cv2
from containers import ContRecording
from image_processing import COLORS, draw_crosshair, scale_position


def render_tracking_video(recording:ContRecording):
    cap = cv2.VideoCapture(recording.paths['VideoField'])
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    path = recording.paths['Directory'] / "tracking_video.mp4"
    out = cv2.VideoWriter(path, fourcc, fps, (frame_width * 2, frame_height))
    
    # Process frames
    print(f"Rendering tracking video...")
    processed_count = 0
    while True:
        # Read next frame
        ret, frame = cap.read()
        if not ret:
            break

        # Process
        result = process_frame(recording, frame, processed_count)
        out.write(result)
        processed_count += 1
        print(f"{processed_count}/{frame_count}", end='\r', flush=True)

    # Release resources
    cap.release()
    out.release()

    print(f"Rendered tracking video as {path}")


def process_frame(recording, frame, i):
    tracks_raw = frame.copy()
    tracks = frame.copy()

    detections_raw = [d for d in recording.tracking_data_raw.get(i, [])]
    detections = [d for d in recording.tracking_data.get(i, [])]

    for detection in detections_raw:
        position = detection['cx'], detection['cy']
        color = COLORS[detection['track_id'] % len(COLORS)]
        draw_crosshair(tracks_raw, position, color, 3)

    for detection in detections:
        position = detection['cx'], detection['cy']
        color = COLORS[detection['track_id'] % len(COLORS)]
        draw_crosshair(tracks, position, color, 3)

    return cv2.hconcat([tracks_raw, tracks])