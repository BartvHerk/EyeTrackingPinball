import sys
import tkinter as tk
from tkinter import ttk

from resources import Resources
from Interface.interface_custom import LazyNotebook, Tab
from Interface.tab_recordings import TabRecordings
from Interface.tab_references import TabReferences


class Interface:
    resources = Resources()


    def __init__(self):
        # Create window
        self.root = tk.Tk()
        self.root.title("Pinball Tracker")
        icon = tk.PhotoImage(file = 'icon.png')
        self.root.iconphoto(True, icon)
        self.root.geometry("1200x700")

        # Tabs
        self.tabs_control = LazyNotebook(self.root)
        self.tabs_control.pack(expand=True, fill ="both")

        self.tabs_control.add_tab('Recordings', TabRecordings(self.resources))
        self.tabs_control.add_tab('References', TabReferences(self.resources))

        self.tabs_control.load_tab()

        # Theme
        self.apply_theme(self.root)

        # Main event loop
        self.root.mainloop()


    def apply_theme(self, window):
        if sys.platform == "win32": # Only affects Windows
            import pywinstyles
            # pywinstyles.apply_style(window, "dark")
            pywinstyles.change_header_color(window, color="#5695C1")  