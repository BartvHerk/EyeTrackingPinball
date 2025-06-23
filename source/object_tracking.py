from ultralytics import YOLO
import yaml, os
import tempfile

from IO import save_tracking_data


def train_model():
    # Load and adjust the YAML dynamically
    yaml_path = os.path.abspath('data/dataset/dataset.yaml')
    with open(yaml_path, 'r') as f:
        data_cfg = yaml.safe_load(f)
    data_cfg['train'] = os.path.join(os.path.dirname(yaml_path), data_cfg['train'])
    data_cfg['val'] = os.path.join(os.path.dirname(yaml_path), data_cfg['val'])

    # Temporary yaml
    with tempfile.NamedTemporaryFile('w+', suffix='.yaml', delete=False) as tmp:
        yaml.dump(data_cfg, tmp)
        tmp_path = tmp.name

    try:
        # Train the model
        model = YOLO('yolov8n.pt')
        model.train(data=tmp_path, epochs=50, imgsz=960, batch=16, name='pinball_detector_final')
    finally:
        # Auto-delete the temp YAML file after training
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def perform_tracking(path, output_path):
    model = YOLO('runs/detect/pinball_detector_final/weights/best.pt')  # Adjust path if needed
    detections_total = []

    # Run tracking on a video
    results = model.track(
        source=path,
        show=False,
        save=False,
        save_txt=False,
        save_conf=False,
        tracker='bytetrack.yaml',
        conf=0.15, # Confidence threshold
        stream=True
    )

    # Extract relevant data
    frame_index = 0
    for r in results:
        if r.boxes is None:
            frame_index += 1
            continue

        # Get all boxes, confidences, and IDs if present
        boxes = r.boxes.xyxy
        confs = r.boxes.conf
        ids = r.boxes.id if r.boxes.id is not None else [None] * len(boxes)

        for i, (box, conf, track_id) in enumerate(zip(boxes, confs, ids)):
            x1, y1, x2, y2 = box.tolist()
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            radius = ((x2 - x1) + (y2 - y1)) / 4

            conf = float(conf)
            track_id = int(track_id) if track_id is not None else -1

            # Format: frame_index, track_id, confidence, center_x, center_y, radius
            detections_total.append([frame_index, track_id, conf, cx, cy, radius])

        frame_index += 1
    
    # Group by frame
    detections_by_frame = {}
    for detection in detections_total:
        frame = detection[0]
        if frame not in detections_by_frame:
            detections_by_frame[frame] = []
        detection_dict = {
                        'track_id': detection[1],
                        'confidence': detection[2],
                        'cx': detection[3],
                        'cy': detection[4],
                        'radius': detection[5]
                    }
        detections_by_frame[frame].append(detection_dict)
    
    # Save data
    save_tracking_data(output_path, detections_by_frame)
    print(f"Saved {len(detections_total)} detections to {output_path}")

# train_model()