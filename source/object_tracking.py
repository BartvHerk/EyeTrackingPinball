from ultralytics import YOLO
import yaml, os
import tempfile


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
        model.train(data=tmp_path, epochs=50, imgsz=960, batch=16, name='pinball_detector')
    finally:
        # Auto-delete the temp YAML file after training
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def perform_tracking():
    model = YOLO('runs/detect/pinball_detector/weights/best.pt')  # Adjust path if needed

    # Run tracking on a video
    results = model.track(
        source='data/recordings/Jesse11apr2/Field_converted.mp4',       # Path to your video
        show=False,                     # Display live window (optional)
        save=True,                     # Save the output video
        tracker='bytetrack.yaml',      # Default tracker (you can customize it)
        conf=0.25,                      # Confidence threshold
        stream=True
    )

    for r in results:
        pass

perform_tracking()