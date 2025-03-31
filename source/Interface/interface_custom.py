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
    master.grid_columnconfigure(0, weight=0, minsize=220)
    master.grid_columnconfigure(1, weight=0, minsize=20)
    master.grid_columnconfigure(2, weight=1)
    master.grid_rowconfigure(0, weight=1)

    # List
    list_frame = ttk.Frame(master)
    list_frame.grid(row=0, column=0, sticky="nsew")


    scrollbar = ttk.Scrollbar(list_frame)
    treeview = ttk.Treeview(list_frame, yscrollcommand=scrollbar.set, columns=("Item",), show="tree")
    treeview.heading("Item", text="Item")
    treeview.column("#0", width=0, stretch=tk.NO)
    treeview.column("Item", anchor="w")
    scrollbar.configure(command=treeview.yview)

    scrollbar.pack(side="right", fill="y")
    treeview.pack(side="left", fill="both", expand=True)
    treeview.bind("<<TreeviewSelect>>", on_item_selected)

    # Selected item frame
    selected_item_frame = ttk.Frame(master)
    selected_item_frame.grid(row=0, column=2, sticky="nsew")

    return (treeview, selected_item_frame)


def x_y_input(master:ttk.Frame, separator:str=" x "):
    x_y_frame = ttk.Frame(master)
    x_y_frame.grid_columnconfigure(0, weight=0)
    x_y_frame.grid_columnconfigure(1, weight=0)
    x_y_frame.grid_columnconfigure(2, weight=1)

    input_x = tk.Text(x_y_frame, height=1, width=5, wrap="none")
    input_x.grid(row=0, column=0)
    input_divider = tk.Text(x_y_frame, height=1, width=len(separator), wrap="word", state="disabled", bg='gray94', borderwidth=0)
    update_text_widget(input_divider, separator)
    input_divider.grid(row=0, column=1)
    input_y = tk.Text(x_y_frame, height=1, width=5, wrap="none")
    input_y.grid(row=0, column=2)

    return x_y_frame, input_x, input_y


def update_text_widget(text_widget:tk.Text, text:str):
    state = text_widget.cget("state")
    text_widget.config(state="normal")
    text_widget.delete(1.0, "end")
    text_widget.insert(1.0, text)
    text_widget.config(state=state)