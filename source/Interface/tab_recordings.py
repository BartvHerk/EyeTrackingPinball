import tkinter as tk
from tkinter import ttk

from resources import Resources
from Interface.interface_custom import Tab, list_layout
from containers import ContRecording
from stopwatch import Stopwatch
from Interface.interface_images import InterfaceImages


class TabRecordings(Tab):
    def __init__(self, resources:Resources):
        Tab.__init__(self, resources)
    

    def load(self, master):
        super().load(master)

        self.recording_lookup = {}
        self.active_recording:ContRecording = None
        self.stopwatch = Stopwatch()
        self.interface_images = InterfaceImages()

        # List layout
        self.treeview, selected_item_frame = list_layout(self.tab_frame, self.on_recording_selected)

        # Active recording
        self.selected_recording_frame = ttk.Frame(selected_item_frame, relief="groove", borderwidth=1, padding=10)
        self.selected_recording_frame.pack(fill="both", expand=True)
        self.selected_recording_frame.grid_propagate(False)
        
        self.selected_recording_frame.grid_columnconfigure(0, weight=2)
        self.selected_recording_frame.grid_columnconfigure(1, weight=1)
        self.selected_recording_frame.grid_columnconfigure(2, weight=1)
        self.selected_recording_frame.grid_columnconfigure(3, weight=1)
        self.selected_recording_frame.grid_rowconfigure(0, weight=1)

        self.display_raw = ttk.Label(self.selected_recording_frame, anchor="center", background="lightblue")
        self.display_raw.grid(row=0, column=0, sticky="nsew")
        
        self.display_gazemapped = ttk.Label(self.selected_recording_frame, anchor="center", background="lightblue")
        self.display_gazemapped.grid(row=0, column=1, sticky="nsew")

        self.display_ball = ttk.Label(self.selected_recording_frame, anchor="center", background="lightblue")
        self.display_ball.grid(row=0, column=2, sticky="nsew")

        self.display_final = ttk.Label(self.selected_recording_frame, anchor="center", background="lightblue")
        self.display_final.grid(row=0, column=3, sticky="nsew")

        # Add recordings to interface
        for recording in self.resources.recordings:
            item_id = self.treeview.insert("", "end", text=recording.paths['Directory'])
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
    

    def start_recording(self):
        self.interface_images.set_recording(self.active_recording, self.resources)
        self.stopwatch.set_time(0)
        self.stopwatch.play()

    
    def end_recording(self):
        self.stopwatch.pause()


    def update_images_loop(self):
        if self.active_recording is None:
            return
        self.update_images()
        self.tab_frame.after(10, self.update_images_loop)
    

    def update_images(self):
        timestamp = self.stopwatch.get_time()
        frame_width = self.selected_recording_frame.winfo_width()
        frame_height = self.selected_recording_frame.winfo_height()

        # Get and set interface images
        (image_raw, image_gazemapped, image_perspective) = self.interface_images.get_images(timestamp, (frame_width, frame_height))
        self.display_raw.config(image=image_raw)
        self.display_gazemapped.config(image=image_gazemapped)
        self.display_ball.config(image=image_perspective)