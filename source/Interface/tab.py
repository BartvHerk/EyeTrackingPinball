import tkinter as tk
from tkinter import ttk

from resources import Resources


class Tab:
    def __init__(self, root:tk.Tk, master:ttk.Notebook, name:str, resources:Resources):
        self.root = root
        self.tab_frame = ttk.Frame(master)
        master.add(self.tab_frame, text =name)
        self.resources = resources

    
    def start(self):
        pass