import copy
import os
import tkinter as tk
from tkinter import ttk

from resources import Resources
from interface.interface_custom import Tab, list_layout, set_start_widget, update_text_widget
from containers import ContRecording
from IO import load_dataset_frames_for_recording, save_recording_metadata, save_tracking_data
from interface.annotation import start_annotation
from processing import process_tracking_data
from object_tracking import perform_tracking
from interface.static_plane import set_plane_static
from graphs import run_graphing
from stats import export_stats, generate_stats
from tracking_video import render_tracking_video, render_video_full
from video_processing import process_video
from stopwatch import Stopwatch
from interface.interface_images import InterfaceImages


class TabRecordings(Tab):
    def __init__(self, resources:Resources):
        Tab.__init__(self, resources)
    

    def load(self, master):
        super().load(master)

        self.icons = self.resources.icons
        self.playing = False
        self.recording_lookup = {}
        self.active_recording:ContRecording = None
        self.stopwatch = Stopwatch()
        self.interface_images = InterfaceImages()

        # List layout
        self.treeview, selected_item_frame = list_layout(self.tab_frame, self.on_recording_selected)

        # Active recording
        self.selected_recording_frame = ttk.Frame(selected_item_frame)
        self.selected_recording_frame.pack(fill="both", expand=True)
        self.selected_recording_frame.grid_columnconfigure(0, weight=1)
        self.selected_recording_frame.grid_rowconfigure(0, weight=1)
        self.selected_recording_frame.grid_rowconfigure(1, weight=0, minsize=10)
        self.selected_recording_frame.grid_rowconfigure(2, weight=0)
        self.selected_recording_frame.grid_rowconfigure(3, weight=0, minsize=10)
        self.selected_recording_frame.grid_rowconfigure(4, weight=0)
        self.selected_recording_frame.grid_rowconfigure(5, weight=0, minsize=10)
        self.selected_recording_frame.grid_rowconfigure(6, weight=0)
        self.selected_recording_frame.grid_rowconfigure(7, weight=0, minsize=5)
        self.selected_recording_frame.grid_rowconfigure(8, weight=0)

        # Displays
        self.selected_recording_displays_frame = ttk.Frame(self.selected_recording_frame, relief="groove", borderwidth=1, padding=10)
        self.selected_recording_displays_frame.grid(row=0, column=0, sticky="nsew")

        style = ttk.Style()
        style.configure("Custom.TFrame", background="lightblue")  # Set background color
        self.selected_recording_displays = ttk.Frame(self.selected_recording_displays_frame, style="Custom.TFrame")
        self.selected_recording_displays.pack(fill="both", expand=True)

        self.selected_recording_displays.grid_columnconfigure(0, weight=1)
        self.selected_recording_displays.grid_columnconfigure(1, weight=0)
        self.selected_recording_displays.grid_columnconfigure(2, weight=0)
        self.selected_recording_displays.grid_columnconfigure(3, weight=0)
        self.selected_recording_displays.grid_columnconfigure(4, weight=0)
        self.selected_recording_displays.grid_columnconfigure(5, weight=1)
        self.selected_recording_displays.grid_rowconfigure(0, weight=1)
        self.selected_recording_displays.grid_rowconfigure(1, weight=0)
        self.selected_recording_displays.grid_rowconfigure(2, weight=0)
        self.selected_recording_displays.grid_rowconfigure(3, weight=1)

        self.selected_recording_displays.grid_propagate(False)

        self.display_raw = ttk.Label(self.selected_recording_displays, anchor="center", background="lightblue")
        self.display_raw.grid(row=1, column=1, sticky="nsew")
        set_start_frame, self.button_set_start_raw, self.entry_set_start_raw = set_start_widget(self.selected_recording_displays)
        set_start_frame.grid(row=2, column=1, sticky="nsew")
        self.button_set_start_raw.config(command=lambda: self.start_time_button_pressed('start_world'))
        self.entry_set_start_raw.bind("<<Modified>>", lambda event: self.start_time_edited(event, 'start_world'))
        
        self.display_gazemapped = ttk.Label(self.selected_recording_displays, anchor="center", background="lightblue")
        self.display_gazemapped.grid(row=1, column=2, sticky="nsew")

        self.display_final = ttk.Label(self.selected_recording_displays, anchor="center", background="lightblue")
        self.display_final.grid(row=1, column=3, sticky="nsew")

        self.display_ball = ttk.Label(self.selected_recording_displays, anchor="center", background="lightblue")
        self.display_ball.grid(row=1, column=4, sticky="nsew")
        set_start_frame, self.button_set_start_ball, self.entry_set_start_ball = set_start_widget(self.selected_recording_displays)
        set_start_frame.grid(row=2, column=4, sticky="nsew")
        self.button_set_start_ball.config(command=lambda: self.start_time_button_pressed('start_field'))
        self.entry_set_start_ball.bind("<<Modified>>", lambda event: self.start_time_edited(event, 'start_field'))

        # Media buttons
        self.media_buttons_frame = ttk.Frame(self.selected_recording_frame)
        self.media_buttons_frame.grid(row=2, column=0, sticky="nsew")

        self.media_buttons_frame.grid_columnconfigure(0, weight=0)
        self.media_buttons_frame.grid_columnconfigure(1, weight=0, minsize=2)
        self.media_buttons_frame.grid_columnconfigure(2, weight=0)
        self.media_buttons_frame.grid_columnconfigure(3, weight=0, minsize=2)
        self.media_buttons_frame.grid_columnconfigure(4, weight=0)
        self.media_buttons_frame.grid_columnconfigure(5, weight=0, minsize=10)
        self.media_buttons_frame.grid_columnconfigure(6, weight=0)
        self.media_buttons_frame.grid_columnconfigure(7, weight=0, minsize=10)
        self.media_buttons_frame.grid_columnconfigure(8, weight=1)
        self.media_buttons_frame.grid_rowconfigure(0, weight=1)

        self.button_play = ttk.Button(self.media_buttons_frame, image=self.icons.icon_play, command=self.on_button_play_click)
        self.button_play.config(state="disabled")
        self.button_play.grid(row=0, column=0)

        self.button_left = ttk.Button(self.media_buttons_frame, image=self.icons.icon_left, command=lambda: self.scrub_frame(-1))
        self.button_left.config(state="disabled")
        self.button_left.grid(row=0, column=2)

        self.button_right = ttk.Button(self.media_buttons_frame, image=self.icons.icon_right, command=lambda: self.scrub_frame(1))
        self.button_right.config(state="disabled")
        self.button_right.grid(row=0, column=4)

        self.label_timestamp = ttk.Label(self.media_buttons_frame, text=self.format_duration(0))
        self.label_timestamp.grid(row=0, column=6, sticky="ew")

        self.scrubber_value = tk.DoubleVar()
        self.scrubber = ttk.Scale(self.media_buttons_frame, from_=0, to=1, orient="horizontal", variable=self.scrubber_value, command=self.on_scrubber_drag)
        self.scrubber.config(state="disabled")
        self.scrubber.grid(row=0, column=8, sticky="ew")

        # Information
        self.text_frame = ttk.Frame(self.selected_recording_frame)
        self.text_frame.grid(row=4, column=0, sticky="nsew")

        self.text_widget = tk.Text(self.text_frame, height=5, wrap="word", state="disabled", bg='gray94', borderwidth=0)
        self.text_widget.pack(fill="both", expand=True)

        # Action buttons
        action_button_frame = ttk.Frame(self.selected_recording_frame)
        action_button_frame.grid(row=6, column=0, sticky="nsew")

        prep_btn = ttk.Menubutton(action_button_frame, text="Preparation")
        prep_menu = tk.Menu(prep_btn, tearoff=0)
        prep_menu.add_command(label="Preprocess videos", command=self.start_video_processing)
        prep_menu.add_command(label="Annotate frames", command=lambda: start_annotation(self.active_recording))
        prep_menu.add_command(label="Set plane", command=self.set_plane)
        prep_btn["menu"] = prep_menu
        prep_btn.grid(row=0, column=0, sticky="w")

        track_btn = ttk.Menubutton(action_button_frame, text="Tracking")
        track_menu = tk.Menu(track_btn, tearoff=0)
        track_menu.add_command(label="Perform tracking (all)", command=self.start_perform_tracking_all)
        track_menu.add_command(label="Perform tracking", command=lambda: self.start_perform_tracking(self.active_recording))
        track_menu.add_command(label="Postprocess tracking", command=self.post_process_tracking)
        track_menu.add_command(label="Render tracking video", command=lambda: render_tracking_video(self.active_recording))
        track_btn["menu"] = track_menu
        track_btn.grid(row=0, column=1, padx=(5, 0), sticky="w")

        analysis_btn = ttk.Menubutton(action_button_frame, text="Analysis")
        analysis_menu = tk.Menu(analysis_btn, tearoff=0)
        analysis_menu.add_command(label="Generate stats (all)", command=self.generate_stats_all)
        analysis_menu.add_command(label="Generate stats", command=lambda: generate_stats(self.active_recording))
        analysis_menu.add_command(label="Export stats", command=export_stats)
        analysis_menu.add_command(label="Create graphs", command=run_graphing)
        analysis_menu.add_command(label="Render full video", command=lambda: render_video_full(self.active_recording))
        analysis_btn["menu"] = analysis_menu
        analysis_btn.grid(row=0, column=2, padx=(5, 0), sticky="w")

        # Participant dropdown
        participant_label = tk.Text(action_button_frame, height=1, width=12, wrap='none', state="disabled", bg='gray94', borderwidth=0)
        participant_label.grid(row=0, column=3, padx=(25, 0), sticky="w")
        update_text_widget(participant_label, 'Participant:')

        names = [d["Name"] for d in self.resources.participants]
        self.dropdown_participant = ttk.Combobox(action_button_frame, values=names, width=30, state="readonly")
        self.dropdown_participant.bind("<<ComboboxSelected>>", self.on_participant_select)
        self.dropdown_participant.set("Select")  # Default text
        self.dropdown_participant.grid(row=0, column=4, padx=(5, 0), sticky="w")

        # High task demand checkbutton
        self.high_task_demand = tk.IntVar()
        self.checkbutton = ttk.Checkbutton(action_button_frame, text='High demand', variable=self.high_task_demand, command=self.on_checkbutton_selected)
        self.checkbutton.grid(row=0, column=5, padx=(5, 0), sticky="w")

        # Add recordings to interface
        for recording in self.resources.recordings:
            item_id = self.treeview.insert("", "end", values=(f"{recording.paths['Directory']}",))
            self.recording_lookup[item_id] = recording
        self.treeview.selection_set(next(iter(self.recording_lookup)))


    def on_recording_selected(self, event):
        selected_recording = self.treeview.selection()
        if selected_recording:
            recording = self.recording_lookup.get(selected_recording[0])
            if recording:
                already_updating = self.active_recording is not None
                if already_updating:
                    self.end_recording()
                self.active_recording = recording
                self.start_recording()
                if not already_updating:
                    self.update_images_loop()
                self.button_play.config(state="normal")
                self.button_left.config(state="normal")
                self.button_right.config(state="normal")
                self.scrubber.config(state="normal")
                participant_default = self.active_recording.metadata.get('participant', "Select")
                self.dropdown_participant.set(participant_default)
                task_key_default = 1 if self.active_recording.metadata.get('task_key', "norm") == "high" else 0
                self.high_task_demand.set(task_key_default)
    

    def start_recording(self):
        self.interface_images.set_recording(self.active_recording, self.resources)
        self.update_information()
        self.start_world = self.active_recording.metadata.get('start_world', 0)
        self.start_field = self.active_recording.metadata.get('start_field', 0)
        update_text_widget(self.entry_set_start_raw, f"{float(self.start_world / 1000):.3f}")
        update_text_widget(self.entry_set_start_ball, f"{float(self.start_field / 1000):.3f}")
        self.stopwatch.limit = self.interface_images.duration
        self.stopwatch.set_time(0)
        self.stopwatch.play() if self.playing else self.stopwatch.pause()
    

    def start_time_button_pressed(self, key):
        widget = self.entry_set_start_raw if key == "start_world" else self.entry_set_start_ball
        video = self.interface_images.videoWorld if key == "start_world" else self.interface_images.videoField
        current_time = min((int)(video.last_index * video.frame_duration), 99999)
        self.active_recording.metadata[key] = current_time
        save_recording_metadata(self.active_recording)
        update_text_widget(widget, f"{(current_time / 1000):.3f}")
        self.interface_images.recalculate_offset_and_duration()
        self.stopwatch.limit = self.interface_images.duration
    

    def start_time_edited(self, event, key):
        widget = event.widget
        text = widget.get("1.0", tk.END).strip()
        try:
            start_time = float(text)
            if start_time > 99.999:
                start_time = 99.999
                update_text_widget(widget, f"{start_time:.3f}")
            start_time_ms = (int)(start_time * 1000)
            start_time_saved = self.active_recording.metadata.get(key, 0)
            if start_time_ms != start_time_saved:
                self.active_recording.metadata[key] = start_time_ms
                save_recording_metadata(self.active_recording)
                self.interface_images.recalculate_offset_and_duration()
                self.stopwatch.limit = self.interface_images.duration
        except:
            pass
        widget.edit_modified(False)

    
    def end_recording(self):
        self.stopwatch.pause()

    
    def on_button_play_click(self):
        self.playing = not self.playing
        self.button_play.config(image=(self.icons.icon_pause if self.playing else self.icons.icon_play))
        self.stopwatch.play() if self.playing else self.stopwatch.pause()

    
    def scrub_frame(self, offset):
        duration = self.interface_images.videoWorld.frame_duration * offset
        time = self.stopwatch.get_time() + duration
        self.stopwatch.set_time(time)


    def on_scrubber_drag(self, value):
        timestamp = float(value) * self.interface_images.duration
        self.update_timestamp()
        self.stopwatch.set_time(timestamp)

    
    def update_scrubber(self):
        ratio = max(min(self.stopwatch.get_time() / self.interface_images.duration, 1), 0)
        self.scrubber_value.set(ratio)

    def update_timestamp(self):
        timestamp = (int)(self.scrubber_value.get() * self.interface_images.duration)
        self.label_timestamp.config(text=self.format_duration(timestamp))
    

    def update_information(self):
        # Get information
        export = self.active_recording.export
        videoWorld = self.interface_images.videoWorld
        videoField = self.interface_images.videoField
        has_preprocessed = "True" if (self.active_recording.metadata.get('video_world', "") and self.active_recording.metadata.get('video_field', "")) else "False"
        has_tracking_data = "True" if (self.active_recording.tracking_data_raw) else "False"
        has_tracking_data_post = "True" if (self.active_recording.metadata.get('post_processed_tracking', "")) else "False"

        text = (
            f"Export:  Path = {self.active_recording.paths['Directory']},  Duration = {self.format_duration(export.data[len(export.data) - 1]['Timestamp'])},  Date = {export.info['Recording time']},  Reference = {export.reference.name}\n"
            f"World video:  Duration = {self.format_duration(videoWorld.duration)}\n"
            f"Field video:  Duration = {self.format_duration(videoField.duration)}\n"
            f"Metadata: Preprocessed = {has_preprocessed}, Annotations = {len(load_dataset_frames_for_recording(self.active_recording))}, Tracked = {has_tracking_data}, Postprocessed = {has_tracking_data_post}\n"
            f"Respondent:  Name = {export.info['Respondent Name']},  Age = {export.info['Respondent Age']},  Gender = {export.info['Respondent Gender']}"
        )

        # Update text widget
        update_text_widget(self.text_widget, text)
    

    def on_participant_select(self, event):
        selected_field = self.dropdown_participant.get()
        self.active_recording.metadata['participant'] = selected_field
        save_recording_metadata(self.active_recording)


    def on_checkbutton_selected(self):
        task_key = "high" if self.high_task_demand.get() else "norm"
        self.active_recording.metadata['task_key'] = task_key
        save_recording_metadata(self.active_recording)
    

    def format_duration(self, ms:int):
        minutes = (int)((ms // 60000) % 60)
        seconds = (int)((ms // 1000) % 60)
        milliseconds = (int)(ms % 1000)
        return f"{minutes}:{seconds:02}.{milliseconds:03}"


    def start_video_processing(self):
        process_video(self.active_recording)

    
    def start_perform_tracking(self, recording:ContRecording):
        path = recording.paths['VideoField']
        output_path = recording.paths['Directory'] / "tracking_data.txt"
        perform_tracking(path, output_path)
    

    def start_perform_tracking_all(self):
        print("Performing tracking for remaining recordings...")
        recordings_left = []
        for recording in self.resources.recordings:
            if not os.path.isfile(recording.paths['Directory'] / "tracking_data.txt"):
                recordings_left.append(recording)
        for recording in recordings_left:
            self.start_perform_tracking(recording)
        print("All remaining recordings have been tracked")
    

    def generate_stats_all(self):
        print("Generating stats for all recordings...")
        for recording in self.resources.recordings:
            generate_stats(recording)
        print("Finished generating stats for all recordings")

    
    def post_process_tracking(self):
        tracking_data = process_tracking_data(copy.deepcopy(self.active_recording.tracking_data_raw), self.active_recording)
        self.active_recording.tracking_data = tracking_data
        save_tracking_data(self.active_recording.paths['Directory'] / "tracking_data_post.txt", tracking_data)

        self.active_recording.metadata['post_processed_tracking'] = "tracking_data_post"
        save_recording_metadata(self.active_recording)
    

    def set_plane(self):
        set_plane_static(self.active_recording)


    def update_images_loop(self):
        if self.active_recording is None:
            return
        self.update_images()
        self.update_scrubber()
        self.update_timestamp()
        self.tab_frame.after(10, self.update_images_loop)
    

    def update_images(self):
        timestamp = self.stopwatch.get_time()
        frame_width = self.selected_recording_displays.winfo_width() - 14
        frame_height = self.selected_recording_displays.winfo_height() - 32

        # Get and set interface images
        (image_raw, image_gazemapped, image_perspective, image_static) = self.interface_images.get_photo_images(timestamp, (frame_width, frame_height))
        self.display_raw.config(image=image_raw)
        self.display_gazemapped.config(image=image_gazemapped)
        self.display_final.config(image=image_perspective)
        self.display_ball.config(image=image_static)