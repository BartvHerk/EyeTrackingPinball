import tkinter as tk
from tkinter import ttk

from resources import Resources
from Interface.tab import Tab
from containers import ContRecording
from stopwatch import Stopwatch
from Interface.interface_images import InterfaceImages


class TabRecordings(Tab):
    recording_lookup = {}
    active_recording:ContRecording = None
    stopwatch = Stopwatch()
    interface_images = InterfaceImages()

    def __init__(self, root:tk.Tk, master:ttk.Notebook, name:str, resources:Resources):
        Tab.__init__(self, root, master, name, resources)

        # Recordings
        self.recordings_frame = ttk.Frame(self.tab_frame, padding=10)
        self.recordings_frame.grid(row=0, column=0, sticky="nsew")

        self.tab_frame.grid_columnconfigure(0, weight=0, minsize=350)
        self.tab_frame.grid_columnconfigure(1, weight=1)
        self.tab_frame.grid_rowconfigure(0, weight=1)

        self.scrollbar = ttk.Scrollbar(self.recordings_frame)
        self.treeview = ttk.Treeview(self.recordings_frame, yscrollcommand=self.scrollbar.set, show="tree")
        self.scrollbar.configure(command=self.treeview.yview)

        self.scrollbar.pack(side="right", fill="y")
        self.treeview.pack(side="left", fill="both", expand=True)
        self.treeview.bind("<<TreeviewSelect>>", self.on_recording_selected)

        # Selected recording
        self.spacer = ttk.Frame(self.tab_frame, padding=(10, 1, 10, 10))
        self.spacer.grid(row=0, column=1, sticky="nsew")
        self.selected_recording_frame = ttk.LabelFrame(self.spacer, padding=(10, 1, 10, 10))
        self.selected_recording_frame["labelwidget"] = ttk.Label(self.selected_recording_frame)
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
    

    def start(self):
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
        self.root.after(10, self.update_images_loop)
    

    def update_images(self):
        timestamp = self.stopwatch.get_time()
        frame_width = self.selected_recording_frame.winfo_width()
        frame_height = self.selected_recording_frame.winfo_height()

        # Get and set interface images
        (image_raw, image_gazemapped, image_perspective) = self.interface_images.get_images(timestamp, (frame_width, frame_height))
        self.display_raw.config(image=image_raw)
        self.display_gazemapped.config(image=image_gazemapped)
        self.display_ball.config(image=image_perspective)