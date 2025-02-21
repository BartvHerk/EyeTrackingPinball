import tkinter as tk
from tkinter import ttk

from resources import Resources


class Tab:
    def __init__(self, resources:Resources):
        self.resources = resources

    
    def load(self, master):
        self.tab_frame = ttk.Frame(master, padding=10)
        self.tab_frame.pack(fill="both", expand=True)


class LazyNotebook(ttk.Notebook):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.tab_holders = []
        self.tab_objects:list[Tab] = []
        self.active_index = 0
        
        # Bind tab switch event
        self.bind("<<NotebookTabChanged>>", self.on_tab_change)
    

    def on_tab_change(self, event):
        index = self.index(self.select())
        if (self.active_index == index):
            return
        
        # Unload current tab
        tab_holder = self.tab_holders[self.active_index]
        for widget in tab_holder.winfo_children():
            widget.destroy()

        # Load new tab
        self.active_index = index
        self.load_tab()
    

    def load_tab(self):
        tab_holder = self.tab_holders[self.active_index]
        self.tab_objects[self.active_index].load(tab_holder)
    

    def add_tab(self, name:str, tab:Tab):
        tab_holder = ttk.Frame(self)
        self.tab_holders.append(tab_holder)
        self.tab_objects.append(tab)
        self.add(tab_holder, text=name)


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