import sys
import tkinter as tk
from tkinter import ttk
import sv_ttk


class Interface:
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

        # Configure grid to maintain layout
        self.tab_recordings.grid_columnconfigure(0, weight=0, minsize=350)
        self.tab_recordings.grid_columnconfigure(1, weight=1)
        self.tab_recordings.grid_rowconfigure(0, weight=1)

        self.scrollbar = ttk.Scrollbar(self.recordings_frame)
        self.treeview = ttk.Treeview(self.recordings_frame, yscrollcommand=self.scrollbar.set, show="tree")
        #self.treeview["columns"] = ("Column1")
        #self.treeview.column("#1", anchor="w", width=200)
        #self.treeview.heading('#0', text="Recordings")
        self.scrollbar.configure(command=self.treeview.yview)

        self.scrollbar.pack(side="right", fill="y")
        self.treeview.pack(side="left", fill="both", expand=True)

        for i in range(20):
            text = f"Item #{i+1}"
            self.treeview.insert("", "end", text=text)

        # Theme
        sv_ttk.set_theme("dark")
        self.apply_titlebar_theme(self.root)

        # Main event loop
        self.root.mainloop()

    def apply_titlebar_theme(self, window):
        if sys.platform == "win32": # Only affects Windows
            import pywinstyles
            pywinstyles.apply_style(window, "dark")