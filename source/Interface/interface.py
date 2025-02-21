import sys
import tkinter as tk
from tkinter import ttk

from resources import Resources
from Interface.interface_custom import Tab
from Interface.tab_recordings import TabRecordings
from Interface.rab_references import TabReferences


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
        self.tabs_control = ttk.Notebook(self.root)
        self.tabs_control.pack(expand = 1, fill ="both")
        self.tabs:list[Tab] = []
        self.tabs.append(TabRecordings(self.root, self.tabs_control, 'Recordings', self.resources))
        self.tabs.append(TabReferences(self.root, self.tabs_control, 'References', self.resources))

        # Theme
        self.apply_theme(self.root)

        # Start
        self.start()

        # Main event loop
        self.root.mainloop()

    
    def start(self):
        for tab in self.tabs:
            tab.start()


    def apply_theme(self, window):
        if sys.platform == "win32": # Only affects Windows
            import pywinstyles
            # pywinstyles.apply_style(window, "dark")
            pywinstyles.change_header_color(window, color="#5695C1")  