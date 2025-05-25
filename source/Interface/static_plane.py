import tkinter as tk
from tkinter import ttk
import cv2
import numpy as np

from containers import ContRecording
from interface.interface_custom import create_toplevel, ready_toplevel
from resources import Resources
from interface.grid_editor import GridEditor
from IO import save_recording_metadata
from video import Video


FRAME_SAMPLES = 10


def set_plane_static(recording:ContRecording):
    resources = Resources()
    

    def OK_action():
        try:
            selected_option = dropdown.get()
            if selected_option == "Custom":
                # New / edit existing
                popup.destroy()
                custom_plane(recording)
            else:
                # Copy other recording
                r = recordings.get(dropdown_recording.get(), None)
                if r is not None:
                    recording.metadata['points'] = r.metadata['points']
                    recording.H_computed = False
                    save_recording_metadata(recording)
                popup.destroy()
        except:
            popup.destroy()
    
    
    popup, content_frame = create_toplevel(resources.root, "Set plane", OK_action)

    def on_dropdown_select(event):
        selected_option = dropdown.get()
        if selected_option == "Custom":
            dropdown_recording.config(state="disabled")
        else:
            dropdown_recording.config(state="readonly")

    # Create content
    dropdown = ttk.Combobox(content_frame, values=["Copy existing", "Custom"], width=40, state="readonly")
    dropdown.bind("<<ComboboxSelected>>", on_dropdown_select)
    dropdown.set("Copy existing")  # Default text
    dropdown.pack()

    recordings = {}
    for r in resources.recordings:
        if r != recording and r.metadata.get('points', None) is not None:
            recordings[r.paths['Directory'].stem] = r
    dropdown_recording = ttk.Combobox(content_frame, values=list(recordings.keys()), width=40, state="readonly")
    dropdown_recording.bind("<<ComboboxSelected>>", on_dropdown_select)
    dropdown_recording.set(next(iter(recordings)) if len(recordings) > 0 else "None available")  # Default text
    dropdown_recording.pack(pady=(10, 0))


    ready_toplevel(popup, resources.root)


def custom_plane(recording:ContRecording):
    resources = Resources()
    

    def OK_action():
        popup.destroy()
        recording.metadata['points'] = updated_points
        recording.H_computed = False
        save_recording_metadata(recording)
    
    updated_points = None
    popup, content_frame = create_toplevel(resources.root, "Set plane", OK_action, True)

    def create_image():
        video = Video(recording.paths['VideoField'])
        accumulated = np.zeros((video.height, video.width, 3), dtype=np.uint8)
        
        for i in range(FRAME_SAMPLES):
            frame_index = int(i * video.frame_count / FRAME_SAMPLES)
            frame = video.get_frame_at_index(frame_index, False)
            alpha = 1/(i + 1)
            accumulated = cv2.convertScaleAbs((1 - alpha) * accumulated + alpha * frame)

        video.destroy()
        return accumulated
    

    def callback_apply(points):
        nonlocal updated_points
        updated_points = list(map(lambda t: tuple(map(round, t)), points))


    # Create content
    editor_frame = ttk.Frame(content_frame)
    editor_frame.pack(fill="both", expand=True)

    grid_editor = GridEditor(editor_frame)
    grid_editor.load(create_image(), recording.metadata.get('points', None), lambda *args: None, callback_apply, False)
    try:
        grid_editor.field_dimensions = resources.fields[recording.export.reference.field].field_dimensions
    except:
        grid_editor.field_dimensions = 100, 100
    grid_editor.update_with_matrix()
    grid_editor.pack(fill="both", expand=True)


    ready_toplevel(popup, resources.root, (400, 700))