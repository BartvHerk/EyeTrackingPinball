import random
import tkinter as tk
from tkinter import ttk

from interface.interface_custom import create_toplevel, ready_toplevel, update_text_widget
from containers import ContRecording
from image_processing import cvimage_to_tkimage, draw_polygon, resize_image_to_fit
from resources import Resources
from IO import load_dataset_frames_for_recording, save_dataset_frame_for_recording
from video import Video


def start_annotation(recording:ContRecording):
    resources = Resources()


    def OK_action():
        try:
            video = Video(recording.paths['VideoField'])
            frames_left = (int)(count_input.get("1.0", tk.END).strip())
            popup.destroy()
            annotate_random_frame(recording, video, frames_left)
        except:
            popup.destroy()
    
    
    popup, content_frame = create_toplevel(resources.root, "Annotate", OK_action)

    # Create content
    count_frame = ttk.Frame(content_frame)
    count_frame.grid(row=0, column=0)

    count_text = tk.Text(count_frame, width=18, height=1, wrap="none", state="disabled", bg='gray94', borderwidth=0)
    update_text_widget(count_text, "Number of frames: ")
    count_text.grid(row=0, column=0, sticky="nsew")

    count_input = tk.Text(count_frame, height=1, width=4, wrap="none")
    update_text_widget(count_input, "50")
    count_input.grid(row=0, column=1)

    # Instantiate popup
    ready_toplevel(popup, resources.root)


def annotate_random_frame(recording:ContRecording, video:Video, frames_left:int):
    if (frames_left <= 0):
        video.destroy()
        return
    
    resources = Resources()
    

    def OK_action():
        nonlocal x_0, y_0, x_1, y_1
        popup.destroy()

        # Save annotation
        annotation_text = ""
        for i in range(len(x_0)):
            x, y = (x_0[i] + x_1[i]) / 2, (y_0[i] + y_1[i]) / 2
            w, h = abs(x_1[i] - x_0[i]), abs(y_1[i] - y_0[i])
            if w != 0 and h != 0:
                annotation_text += f"0 {x} {y} {w} {h}\n"
        save_dataset_frame_for_recording(recording, index, frame, annotation_text)
        
        # Next frame
        annotate_random_frame(recording, video, frames_left-1)
    
    
    def load_frame(index:int):
        nonlocal display_label, frame_text, offset_total, frame, frame_scaled

        # Image
        frame = video.get_frame_at_index(index)
        frame_scaled, _ = resize_image_to_fit(frame)
        update_frame()

        # Text
        update_text()
    

    def update_text():
        nonlocal frame_text, frames_annotated
        text = f"Annotated: {len(frames_annotated)}\nFrame: {index + 1}/{video.frame_count}"
        if offset_total != 0:
            text += f" ({"+" if offset_total > 0 else ""}{offset_total})"
        update_text_widget(frame_text, text)
        frame_text.config(width=len(text))

    
    def move_frame(offset:int):
        nonlocal index, offset_total
        index += offset
        offset_total += offset
        load_frame(index)
    

    def convert_coords(position):
        nonlocal display_label, frame_scaled
        frame_scaled_height, frame_scaled_width = frame_scaled.shape[:2]
        label_width, label_height = (display_label.winfo_width(), display_label.winfo_height())
        offset_x = (label_width - frame_scaled_width) // 2
        offset_y = (label_height - frame_scaled_height) // 2
        return ((position[0] - offset_x) / frame_scaled_width, (position[1] - offset_y) / frame_scaled_height)
    

    def click_on_frame(event):
        nonlocal x_0, y_0
        x, y = convert_coords((event.x, event.y))
        x_0.append(x)
        y_0.append(y)
        x_1.append(x)
        y_1.append(y)


    def right_click_on_frame(event):
        nonlocal x_0, y_0, x_1, y_1
        x_0, y_0, x_1, y_1, = [], [], [], []
        update_frame()


    def drag_on_frame(event):
        nonlocal x_0, y_0, x_1, y_1
        x, y = convert_coords((event.x, event.y))
        box = len(x_0) - 1
        x_1[box] = x
        y_1[box] = y
        update_frame()
    

    def update_frame():
        nonlocal display_label, frame_scaled, x_0, y_0, x_1, y_1
        frame_scaled_height, frame_scaled_width = frame_scaled.shape[:2]
        frame_final = frame_scaled.copy()
        for i in range(len(x_0)):
            points_raw = [(x_0[i], y_0[i]), (x_1[i], y_0[i]), (x_1[i], y_1[i]), (x_0[i], y_1[i])]
            points = list(map(lambda t: (t[0] * frame_scaled_width, t[1] * frame_scaled_height), points_raw))
            draw_polygon(frame_final, points, 1)
        tkimage = cvimage_to_tkimage(frame_final)
        display_label.config(image=tkimage)
        display_label.image = tkimage


    popup, content_frame = create_toplevel(resources.root, "Annotate frame", OK_action)

    # Get dataset
    frames_annotated = load_dataset_frames_for_recording(recording)

    # Create content
    content_frame.grid_columnconfigure(0, weight=1)
    content_frame.grid_rowconfigure(0, weight=0)
    content_frame.grid_rowconfigure(1, weight=0, minsize=10)
    content_frame.grid_rowconfigure(2, weight=1)
    content_frame.grid_rowconfigure(3, weight=0, minsize=10)
    content_frame.grid_rowconfigure(4, weight=0)

    display_frame = ttk.Frame(content_frame, relief="groove", borderwidth=1, padding=10)
    display_frame.grid(row=2, column=0, sticky="nsew")
    display_label = ttk.Label(display_frame, anchor="center", background="lightblue")
    display_label.pack(fill="both", expand=True)
    display_label.bind("<ButtonPress-1>", click_on_frame)
    display_label.bind("<ButtonPress-3>", right_click_on_frame)
    display_label.bind("<B1-Motion>", drag_on_frame)

    # Text
    frame_text = tk.Text(content_frame, width=1, height=2, wrap="none", state="disabled", bg='gray94', borderwidth=0)
    frame_text.tag_configure("center", justify="center")
    frame_text.tag_add("center", "1.0", "end")
    frame_text.grid(row=0, column=0, sticky="nsew")

    # Select random frame
    while True:
        index = random.randrange(0, video.frame_count)
        if index not in frames_annotated:
            break
    offset_total = 0
    frame = None
    frame_scaled = None
    x_0, y_0, x_1, y_1, = [], [], [], []
    load_frame(index)

    # Frame buttons
    resources = Resources()
    media_buttons_frame = ttk.Frame(content_frame)
    media_buttons_frame.grid(row=4, column=0, sticky="nsew")
    media_buttond_frame_inner = ttk.Frame(media_buttons_frame)
    media_buttond_frame_inner.pack()

    button_left = ttk.Button(media_buttond_frame_inner, image=resources.icons.icon_left, command=lambda: move_frame(-1))
    button_left.pack(side="left")
    button_reset = ttk.Button(media_buttond_frame_inner, text="Reset to frame", command=lambda: move_frame(-offset_total))
    button_reset.pack(side="left", padx=(2, 0))
    button_right = ttk.Button(media_buttond_frame_inner, image=resources.icons.icon_right, command=lambda: move_frame(1))
    button_right.pack(side="left", padx=(2, 0))

    # Instantiate popup
    ready_toplevel(popup, resources.root)