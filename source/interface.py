import sys
import tkinter as tk
from tkinter import ttk
import sv_ttk
from PIL import ImageTk, Image
import cv2

from openCV import resize_image_to_fit
from resources import Resources
from containers import ContRecording


class Interface:
    resources:Resources
    recording_lookup = {}
    active_recording = None

    def __init__(self):
        # Create window
        self.root = tk.Tk()
        self.root.title("Pinball Tracker")
        icon = tk.PhotoImage(file = 'icon.png')
        self.root.iconphoto(True, icon)
        self.root.geometry("1200x700")

        # Tabs
        self.tabs_control = ttk.Notebook(self.root)
        self.tab_recordings = ttk.Frame(self.tabs_control) 
        self.tab_references = ttk.Frame(self.tabs_control)

        self.tabs_control.add(self.tab_recordings, text ='Recordings') 
        self.tabs_control.add(self.tab_references, text ='References') 
        self.tabs_control.pack(expand = 1, fill ="both")

        # Recordings
        self.recordings_frame = ttk.Frame(self.tab_recordings, padding=10)
        self.recordings_frame.grid(row=0, column=0, sticky="nsew")

        self.tab_recordings.grid_columnconfigure(0, weight=0, minsize=350)
        self.tab_recordings.grid_columnconfigure(1, weight=1)
        self.tab_recordings.grid_rowconfigure(0, weight=1)

        self.scrollbar = ttk.Scrollbar(self.recordings_frame)
        self.treeview = ttk.Treeview(self.recordings_frame, yscrollcommand=self.scrollbar.set, show="tree")
        self.scrollbar.configure(command=self.treeview.yview)

        self.scrollbar.pack(side="right", fill="y")
        self.treeview.pack(side="left", fill="both", expand=True)
        self.treeview.bind("<<TreeviewSelect>>", self.on_recording_selected)

        # Selected recording
        self.spacer = ttk.Frame(self.tab_recordings, padding=(10, 1, 10, 10))
        self.spacer.grid(row=0, column=1, sticky="nsew")
        self.selected_recording_frame = ttk.LabelFrame(self.spacer, padding=(10, 1, 10, 10))
        self.selected_recording_frame["labelwidget"] = ttk.Label(self.selected_recording_frame)
        self.selected_recording_frame.pack(fill="both", expand=True)

        self.selected_recording_frame.grid_columnconfigure(0, weight=1)
        self.selected_recording_frame.grid_columnconfigure(1, weight=1)
        self.selected_recording_frame.grid_rowconfigure(0, weight=1)
        self.selected_recording_frame.grid_rowconfigure(1, weight=1)

        self.display_raw = ttk.Label(self.selected_recording_frame, anchor="center", background="lightblue")
        self.display_raw.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        self.display_reference = ttk.Label(self.selected_recording_frame, anchor="center", background="lightblue")
        self.display_reference.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        self.display_static = ttk.Label(self.selected_recording_frame, anchor="center", background="lightblue")
        self.display_static.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        self.display_final = ttk.Label(self.selected_recording_frame, anchor="center", background="lightblue")
        self.display_final.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

        # Theme
        # sv_ttk.set_theme("dark")
        self.apply_titlebar_theme(self.root, "dark")

        # Start
        self.start()

        # Main event loop
        self.root.mainloop()

    
    def start(self):
        self.resources = Resources()
        
        for recording in self.resources.recordings:
            self.add_recording_interface(recording)
    

    def add_recording_interface(self, recording:ContRecording):
        item_id = self.treeview.insert("", "end", text=recording.paths['Directory'])
        self.recording_lookup[item_id] = recording
    

    def on_recording_selected(self, event):
        selected_recording = self.treeview.selection()
        if selected_recording:
            recording = self.recording_lookup.get(selected_recording[0])
            if recording:
                updating = self.active_recording is not None
                self.active_recording = recording
                if not updating:
                    self.update_images_loop()


    def update_images_loop(self):
        if self.active_recording is None:
            return
        self.update_images()
        self.root.after(50, self.update_images_loop)
    

    def update_images(self):
        frame_width = self.selected_recording_frame.winfo_width() / 2
        frame_height = self.selected_recording_frame.winfo_height() / 2

        # Reference image for gaze mapped display
        reference_image = self.active_recording.export.reference.image
        scaled_reference, scale_factor = resize_image_to_fit(reference_image.copy(), (frame_width, frame_height))

        rgb_image = cv2.cvtColor(scaled_reference, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb_image)
        imgtk = ImageTk.PhotoImage(image=img)
        self.display_reference.config(image=imgtk)
        self.display_reference.image = imgtk

        self.display_static.config(image=imgtk)


    def apply_titlebar_theme(self, window, theme):
        if sys.platform == "win32": # Only affects Windows
            import pywinstyles
            # pywinstyles.apply_style(window, theme)
            pywinstyles.change_header_color(window, color="#5695C1")  