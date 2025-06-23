import cv2
from containers import ContRecording
from image_processing import COLORS, draw_crosshair, scale_position
from interface.interface_images import InterfaceImages
from resources import Resources


DIMENSIONS = (1920, 1080)


def render_tracking_video(recording:ContRecording):
    cap = cv2.VideoCapture(recording.paths['VideoField'])
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    path = recording.paths['Directory'] / "video_tracking.mp4"
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


def render_video_full(recording:ContRecording):
    resources = Resources()
    hidden_images = InterfaceImages() # Interface images that aren't exposed to the user
    hidden_images.set_recording(recording, resources)
    print(f"Rendering full video...")

    # Get first frame for dimensions
    images = hidden_images.get_images(0, DIMENSIONS)
    w_complete = sum(img.shape[1] for img in images)
    h_complete = max(img.shape[0] for img in images)

    # setup output
    fps = hidden_images.videoField.fps
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    path = recording.paths['Directory'] / "video_output.mp4"
    out = cv2.VideoWriter(path, fourcc, fps, (w_complete, h_complete))

    # Render frames
    frame_count = int(hidden_images.duration / 1000 * fps)
    for i in range(frame_count):
        timestamp = (i / frame_count) * hidden_images.duration
        (image_raw, image_gazemapped, image_perspective, image_static) = hidden_images.get_images(timestamp, DIMENSIONS)
        frame_complete = cv2.hconcat([image_raw, image_gazemapped, image_perspective, image_static])
        out.write(frame_complete)
        print(f"{i+1}/{frame_count}", end='\r', flush=True)

    # Free memory
    out.release()
    hidden_images.set_recording(None, resources)
    print()
    print(f"Rendered full video as {path}")