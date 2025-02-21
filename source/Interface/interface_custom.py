import tkinter as tk
from tkinter import ttk

from resources import Resources


class Tab:
    def __init__(self, root:tk.Tk, master:ttk.Notebook, name:str, resources:Resources):
        self.root = root
        self.tab_frame = ttk.Frame(master, padding=10)
        master.add(self.tab_frame, text =name)
        self.resources = resources

    
    def start(self):
        pass


def list_layout(master:ttk.Frame, on_item_selected):
    master.grid_columnconfigure(0, weight=0, minsize=350)
    master.grid_columnconfigure(1, weight=0, minsize=20)
    master.grid_columnconfigure(2, weight=1)
    master.grid_rowconfigure(0, weight=1)

    # List
    list_frame = ttk.Frame(master)
    list_frame.grid(row=0, column=0, sticky="nsew")


    scrollbar = ttk.Scrollbar(list_frame)
    treeview = ttk.Treeview(list_frame, yscrollcommand=scrollbar.set, show="tree")
    scrollbar.configure(command=treeview.yview)

    scrollbar.pack(side="right", fill="y")
    treeview.pack(side="left", fill="both", expand=True)
    treeview.bind("<<TreeviewSelect>>", on_item_selected)

    # Selected item frame
    selected_item_frame = ttk.Frame(master)
    selected_item_frame.grid(row=0, column=2, sticky="nsew")

    return (treeview, selected_item_frame)