import concurrent.futures
import cv2
from containers import ContRecording
from image_processing import COLORS, draw_crosshair, scale_position
from video import Video


BATCH_SIZE = 200 # How many frames should be processed in parallel


def render_tracking_video(recording:ContRecording):
    cap = cv2.VideoCapture(recording.paths['VideoField'])
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    path = recording.paths['Directory'] / "tracking_video.mp4"
    out = cv2.VideoWriter(path, fourcc, fps, (frame_width * 2, frame_height))

    def read_batch(cap):
        batch = []
        for _ in range(BATCH_SIZE):
            ret, frame = cap.read()
            if not ret:
                break
            batch.append(frame)
        return batch
    
    # Process frames
    print(f"Rendering tracking video...")
    processed_count = 0
    while True:
        # Read next batch
        frames = read_batch(cap)
        if not frames:
            break

        # Process batch in parallel
        args = [(recording, frame, processed_count + i) for i, frame in enumerate(frames)]
        with concurrent.futures.ThreadPoolExecutor() as executor:
            processed = list(executor.map(process_frame, args))

        # Write batch to output
        for frame in processed:
            out.write(frame)
        processed_count += len(frames)
        print(f"{processed_count}/{frame_count}", end='\r', flush=True)
        if processed_count > 3000: # TODO: Remove
            break

    # Release resources
    cap.release()
    out.release()

    print(f"Rendered tracking video as {path}")


def process_frame(args):
    recording, frame, i = args
    tracks_raw = frame.copy()
    tracks = frame.copy()

    detections_raw = [d for d in recording.tracking_data_raw.get(i, [])]
    detections = [d for d in recording.tracking_data.get(i, [])]

    # Render frame
    for detection in detections_raw:
        position = detection['cx'], detection['cy']
        color = COLORS[detection['track_id'] % len(COLORS)]
        draw_crosshair(tracks_raw, position, color, 3)
    for detection in detections:
        position = detection['cx'], detection['cy']
        color = COLORS[detection['track_id'] % len(COLORS)]
        draw_crosshair(tracks, position, color, 3)

    return cv2.hconcat([tracks_raw, tracks])