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


def set_start_widget(master:ttk.Frame):
    style = ttk.Style()
    style.configure("Custom.TButton", background="lightblue")

    set_start_outer = tk.Frame(master, height=20, bg="lightblue")
    set_start_widget = tk.Frame(set_start_outer, bg="lightblue")
    set_start_widget.place(relx=0.5, rely=0.5, anchor="center")
    set_start_inner = tk.Frame(set_start_widget, bg="lightblue")
    set_start_inner.pack()
    set_start_button = ttk.Button(set_start_inner, text="Set start", style="Custom.TButton")
    set_start_button.pack(side="left")
    set_start_entry = tk.Text(set_start_inner, height=1, width=6, wrap="none")
    set_start_entry.pack(side="left", padx=(5, 0))

    return set_start_outer, set_start_button, set_start_entry


def update_text_widget(text_widget:tk.Text, text:str):
    state = text_widget.cget("state")
    text_widget.config(state="normal")
    text_widget.delete(1.0, "end")
    text_widget.insert(1.0, text)
    text_widget.config(state=state)


def create_toplevel(root:tk.Tk, title:str, ok_action=None):
    toplevel = tk.Toplevel(root)

    # Frame and OK button
    toplevel_frame = ttk.Frame(toplevel, padding=10)
    toplevel_frame.pack(fill="both", expand=True)
    toplevel_frame.grid_columnconfigure(0, weight=1)
    toplevel_frame.grid_rowconfigure(0, weight=1)
    toplevel.toplevel_frame = toplevel_frame
    
    content_frame = ttk.Frame(toplevel_frame)
    content_frame.grid(row=0, column=0, sticky="nsew")

    if (ok_action is not None):
        toplevel_frame.grid_rowconfigure(1, weight=0, minsize=20)
        toplevel_frame.grid_rowconfigure(2, weight=0)
        OK_button = ttk.Button(toplevel_frame, text="OK", command=ok_action)
        OK_button.grid(row=2, column=0)
    
    # Settings
    toplevel.title(title)
    toplevel.resizable(False, False)
    return toplevel, content_frame



def ready_toplevel(toplevel:tk.Toplevel, root:tk.Tk):
    # Size and position
    root.update_idletasks()
    parent_x, parent_y = root.winfo_x(), root.winfo_y()
    parent_w, parent_h = root.winfo_width(), root.winfo_height()
    w, h = toplevel.toplevel_frame.winfo_reqwidth(), toplevel.toplevel_frame.winfo_reqheight()
    x, y = parent_x + (parent_w - w) // 2, parent_y + (parent_h - h) // 2

    # Create window
    toplevel.geometry(f"{w}x{h}+{x}+{y}")

    # Disable interaction with root
    toplevel.grab_set()        # Redirect all events to this popup
    toplevel.transient(root)  # Keep on top of main window
    toplevel.wait_window()