import tkinter as tk
from tkinter import ttk

from resources import Resources
from interface.interface_custom import Tab, list_layout, update_text_widget
from containers import ContRecording
from stopwatch import Stopwatch
from interface.interface_images import InterfaceImages


class TabRecordings(Tab):
    def __init__(self, resources:Resources):
        Tab.__init__(self, resources)

        self.icon_play = tk.PhotoImage(file="assets/button_play.png")
        self.icon_pause = tk.PhotoImage(file="assets/button_pause.png")
    

    def load(self, master):
        super().load(master)

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

        # Displays
        self.selected_recording_displays_frame = ttk.Frame(self.selected_recording_frame, relief="groove", borderwidth=1, padding=10)
        self.selected_recording_displays_frame.grid(row=0, column=0, sticky="nsew")
        self.selected_recording_displays_frame.grid_propagate(False)
        
        self.selected_recording_displays_frame.grid_columnconfigure(0, weight=2)
        self.selected_recording_displays_frame.grid_columnconfigure(1, weight=1)
        self.selected_recording_displays_frame.grid_columnconfigure(2, weight=1)
        self.selected_recording_displays_frame.grid_columnconfigure(3, weight=1)
        self.selected_recording_displays_frame.grid_rowconfigure(0, weight=1)

        self.display_raw = ttk.Label(self.selected_recording_displays_frame, anchor="center", background="lightblue")
        self.display_raw.grid(row=0, column=0, sticky="nsew")
        
        self.display_gazemapped = ttk.Label(self.selected_recording_displays_frame, anchor="center", background="lightblue")
        self.display_gazemapped.grid(row=0, column=1, sticky="nsew")

        self.display_final = ttk.Label(self.selected_recording_displays_frame, anchor="center", background="lightblue")
        self.display_final.grid(row=0, column=2, sticky="nsew")

        self.display_ball = ttk.Label(self.selected_recording_displays_frame, anchor="center", background="lightblue")
        self.display_ball.grid(row=0, column=3, sticky="nsew")

        # Media buttons
        self.media_buttons_frame = ttk.Frame(self.selected_recording_frame)
        self.media_buttons_frame.grid(row=2, column=0, sticky="nsew")

        self.media_buttons_frame.grid_columnconfigure(0, weight=0)
        self.media_buttons_frame.grid_columnconfigure(1, weight=0, minsize=10)
        self.media_buttons_frame.grid_columnconfigure(2, weight=0)
        self.media_buttons_frame.grid_columnconfigure(3, weight=0, minsize=10)
        self.media_buttons_frame.grid_columnconfigure(4, weight=1)
        self.media_buttons_frame.grid_rowconfigure(0, weight=1)

        self.button_play = ttk.Button(self.media_buttons_frame, image=self.icon_play, command=self.on_button_play_click)
        self.button_play.config(state="disabled")
        self.button_play.grid(row=0, column=0)

        self.label_timestamp = ttk.Label(self.media_buttons_frame, text=self.format_duration(0))
        self.label_timestamp.grid(row=0, column=2, sticky="ew")

        self.scrubber_value = tk.DoubleVar()
        self.scrubber = ttk.Scale(self.media_buttons_frame, from_=0, to=1, orient="horizontal", variable=self.scrubber_value, command=self.on_scrubber_drag)
        self.scrubber.config(state="disabled")
        self.scrubber.grid(row=0, column=4, sticky="ew")

        # Information
        self.text_frame = ttk.Frame(self.selected_recording_frame)
        self.text_frame.grid(row=4, column=0, sticky="nsew")

        self.text_widget = tk.Text(self.text_frame, height=2, wrap="word", state="disabled", bg='gray94', borderwidth=0)
        self.text_widget.pack(fill="both", expand=True)

        # Add recordings to interface
        for recording in self.resources.recordings:
            item_id = self.treeview.insert("", "end", values=(f"{recording.paths['Directory']}",))
            self.recording_lookup[item_id] = recording


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
                self.scrubber.config(state="normal")
    

    def start_recording(self):
        self.interface_images.set_recording(self.active_recording, self.resources)
        self.update_information()
        self.stopwatch.set_time(0)
        self.stopwatch.play() if self.playing else self.stopwatch.pause()

    
    def end_recording(self):
        self.stopwatch.pause()

    
    def on_button_play_click(self):
        self.playing = not self.playing
        self.button_play.config(image=(self.icon_pause if self.playing else self.icon_play))
        self.stopwatch.play() if self.playing else self.stopwatch.pause()


    def on_scrubber_drag(self, value):
        timestamp = (int)(float(value) * self.interface_images.video.duration)
        self.update_timestamp()
        self.stopwatch.set_time(timestamp)

    
    def update_scrubber(self):
        ratio = max(min(self.stopwatch.get_time() / self.interface_images.video.duration, 1), 0)
        self.scrubber_value.set(ratio)

    def update_timestamp(self):
        timestamp = (int)(self.scrubber_value.get() * self.interface_images.video.duration)
        self.label_timestamp.config(text=self.format_duration(timestamp))
    

    def update_information(self):
        # Get information
        export = self.active_recording.export
        video = self.interface_images.video

        text = (
            f"Recording:  Path = {self.active_recording.paths['Directory']},  Duration = {self.format_duration(video.duration)},  Date = {export.info['Recording time']}\n"
            f"Respondent:  Name = {export.info['Respondent Name']},  Age = {export.info['Respondent Age']},  Gender = {export.info['Respondent Gender']}"
        )

        # Update text widget
        update_text_widget(self.text_widget, text)
    

    def format_duration(self, ms:int):
        minutes = (int)((ms // 60000) % 60)
        seconds = (int)((ms // 1000) % 60)
        milliseconds = (int)(ms % 1000)
        return f"{minutes}:{seconds:02}.{milliseconds:03}"


    def update_images_loop(self):
        if self.active_recording is None:
            return
        self.update_images()
        self.update_scrubber()
        self.update_timestamp()
        self.tab_frame.after(10, self.update_images_loop)
    

    def update_images(self):
        timestamp = self.stopwatch.get_time()
        frame_width = self.selected_recording_displays_frame.winfo_width() - 24
        frame_height = self.selected_recording_displays_frame.winfo_height() - 24

        # Get and set interface images
        (image_raw, image_gazemapped, image_perspective, image_static) = self.interface_images.get_images(timestamp, (frame_width, frame_height))
        self.display_raw.config(image=image_raw)
        self.display_gazemapped.config(image=image_gazemapped)
        self.display_final.config(image=image_perspective)
        self.display_ball.config(image=image_static)