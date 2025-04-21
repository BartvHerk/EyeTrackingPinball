import subprocess
import os
import tkinter as tk
from tkinter import ttk
import concurrent.futures

from containers import ContRecording
from interface.interface_custom import create_toplevel, ready_toplevel, update_text_widget
from resources import Resources
from IO import save_recording_metadata


def process_video(recording:ContRecording):
    resources = Resources()
    
    def OK_action():
        # Paths
        world_video_name = world_input.get("1.0", tk.END).strip()
        field_video_name = field_input.get("1.0", tk.END).strip()
        recording.metadata["video_world"] = world_video_name
        recording.metadata["video_field"] = field_video_name
        save_recording_metadata(recording)
        directory = recording.paths['Directory']

        # process
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(convert_video, f"{directory}/World.mp4", f"{directory}/{world_video_name}.mp4"),
                executor.submit(convert_video, f"{directory}/Field.mp4", f"{directory}/{field_video_name}.mp4", 180, 60, (-1, 1080)) # Auto-compute width
            ]

            # Wait for completion
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                    print("Video processed")
                except Exception as e:
                    print(f"Error during video processing: {e}")
        popup.destroy()
    
    
    popup, content_frame = create_toplevel(resources.root, "Process videos", OK_action)

    # Create content
    inputs_frame = ttk.Frame(content_frame)
    inputs_frame.grid(row=0, column=0)
    inputs_frame.grid_rowconfigure(0, weight=1)
    inputs_frame.grid_rowconfigure(1, weight=0, minsize=10)
    inputs_frame.grid_rowconfigure(2, weight=1)

    world_text = tk.Text(inputs_frame, width=17, height=1, wrap="none", state="disabled", bg='gray94', borderwidth=0)
    update_text_widget(world_text, "New world video: ")
    world_text.grid(row=0, column=0, sticky="nsew")
    world_input = tk.Text(inputs_frame, height=1, width=20, wrap="none")
    update_text_widget(world_input, "World_converted")
    world_input.grid(row=0, column=1)
    world_extension = tk.Text(inputs_frame, width=4, height=1, wrap="none", state="disabled", bg='gray94', borderwidth=0)
    update_text_widget(world_extension, ".mp4")
    world_extension.grid(row=0, column=2, sticky="nsew")

    field_text = tk.Text(inputs_frame, width=17, height=1, wrap="none", state="disabled", bg='gray94', borderwidth=0)
    update_text_widget(field_text, "New field video: ")
    field_text.grid(row=2, column=0, sticky="nsew")
    field_input = tk.Text(inputs_frame, height=1, width=20, wrap="none")
    update_text_widget(field_input, "Field_converted")
    field_input.grid(row=2, column=1)
    field_extension = tk.Text(inputs_frame, width=4, height=1, wrap="none", state="disabled", bg='gray94', borderwidth=0)
    update_text_widget(field_extension, ".mp4")
    field_extension.grid(row=2, column=2, sticky="nsew")

    # Instantiate popup
    ready_toplevel(popup, resources.root)


def convert_video(path, path_output, rotation=0, fps=60, scale=None): # Rotation must be a multiple of 90
    if not os.path.exists(path):
        return

    # Rotate
    transpose_map = {
        90: "transpose=1",          # clockwise
        270: "transpose=2",         # counter-clockwise
        180: "transpose=2,transpose=2"  # rotate twice (180 degrees)
    }

    filters = []
    if rotation in transpose_map:
        filters.append(transpose_map[rotation])

    # Set framerate
    filters.append(f"fps={fps}")
    vf_filter = ",".join(filters)

    # Scale
    if scale is not None:
        filters.append(f"scale={scale[0]}:{scale[1]}")

    cmd = [
        "ffmpeg", "-y", "-i", path,
        "-vf", vf_filter,
        "-c:v", "libx264", "-preset", "veryfast", f"-crf", "20", # 20 = visually almost lossless
        "-c:a", "copy",
        "-movflags", "+faststart",
        path_output
    ]
    subprocess.run(cmd)