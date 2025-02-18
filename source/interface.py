import sys
import tkinter as tk
from tkinter import ttk
import sv_ttk

from resources import Resources


class Interface:
    recording_lookup = {}

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

        self.selected_recording_frame = ttk.Frame(self.tab_recordings, padding=10)
        self.selected_recording_frame.grid(row=0, column=1, sticky="nsew")

        self.tab_recordings.grid_columnconfigure(0, weight=0, minsize=350)
        self.tab_recordings.grid_columnconfigure(1, weight=1)
        self.tab_recordings.grid_rowconfigure(0, weight=1)

        self.scrollbar = ttk.Scrollbar(self.recordings_frame)
        self.treeview = ttk.Treeview(self.recordings_frame, yscrollcommand=self.scrollbar.set, show="tree")
        self.scrollbar.configure(command=self.treeview.yview)

        self.scrollbar.pack(side="right", fill="y")
        self.treeview.pack(side="left", fill="both", expand=True)
        self.treeview.bind("<<TreeviewSelect>>", self.on_recording_selected)

        # Theme
        sv_ttk.set_theme("dark")
        self.apply_titlebar_theme(self.root)

        # Start
        self.start()

        # Main event loop
        self.root.mainloop()

    
    def start(self):
        self.resources = Resources()

        for recording in self.resources.recordings:
            self.add_recording_interface(recording.paths['Directory'], recording)
    

    def add_recording_interface(self, display_text, obj):
        item_id = self.treeview.insert("", "end", text=display_text)
        self.recording_lookup[item_id] = obj
    

    def on_recording_selected(self, event):
        selected_recording = self.treeview.selection()
        if selected_recording:
            obj = self.recording_lookup.get(selected_recording[0])
            if obj:
                self.handle_selection(obj)

    
    def handle_selection(self, obj):
        print(f"Selected object: {obj}")


    def apply_titlebar_theme(self, window):
        if sys.platform == "win32": # Only affects Windows
            import pywinstyles
            pywinstyles.apply_style(window, "dark")