import tkinter as tk
from tkinter import ttk

from resources import Resources
from interface.interface_custom import Tab, list_layout, update_text_widget
from containers import ContReference
from interface.grid_editor import GridEditor
from IO import save_reference_points


H_DIGITS = 9
H_DECIMALS = 4


class TabReferences(Tab):
    def __init__(self, resources:Resources):
        Tab.__init__(self, resources)
    

    def load(self, master):
        super().load(master)

        self.reference_lookup = {}
        self.active_reference:ContReference = None

        # List layout
        self.treeview, selected_item_frame = list_layout(self.tab_frame, self.on_reference_selected)

        # Split display
        selected_item_frame.grid_columnconfigure(0, weight=1)
        selected_item_frame.grid_columnconfigure(1, weight=0, minsize=10)
        selected_item_frame.grid_columnconfigure(2, weight=1)
        selected_item_frame.grid_rowconfigure(0, weight=1)

        # Grid editor
        self.grid_editor = GridEditor(selected_item_frame)
        self.grid_editor.grid(row=0, column=2, sticky="nsew")

        # Information
        self.information_frame = ttk.Frame(selected_item_frame)
        self.information_frame.grid(row=0, column=0, sticky="nsew")
        self.information_frame.grid_columnconfigure(0, weight=1)
        self.information_frame.grid_rowconfigure(0, weight=1)
        self.information_frame.grid_rowconfigure(1, weight=0)

        self.text_frame = ttk.Frame(self.information_frame)
        self.text_frame.grid(row=0, column=0, sticky="nsew")
        self.text_frame.pack_propagate(False)

        self.text_widget = tk.Text(self.text_frame, wrap="word", state="disabled", bg='gray94', borderwidth=0)
        self.text_widget.pack(fill="both", expand=True)

        # Add references to interface
        for reference in self.resources.references.values():
            item_id = self.treeview.insert("", "end", text=reference.name)
            self.reference_lookup[item_id] = reference


    def on_reference_selected(self, event):
        selected_reference = self.treeview.selection()
        if selected_reference:
            reference = self.reference_lookup.get(selected_reference[0])
            if reference:
                self.active_reference = reference
                self.select_reference()
    

    def select_reference(self):
        self.grid_editor.load(self.active_reference.image, self.active_reference.points, self.update_information, self.callback_apply, False)
        self.update_information()

    
    def callback_apply(self, points):
        self.active_reference.points = list(map(lambda t: tuple(map(round, t)), points))
        self.active_reference.H_computed = False
        save_reference_points(self.active_reference)


    def update_information(self):
        # Get information
        name = self.active_reference.name
        reference_image_height, reference_image_width = self.active_reference.image.shape[:2]
        H = self.grid_editor.H
        text = (
            f"Name:\n{name}\n\n"
            f"Path:\n{self.active_reference.path}\n\n"
            f"Image dimensions (px): \n{reference_image_width} x {reference_image_height}\n\n"
            f"Homography matrix: \n{self.homography_matrix_text(H)}\n\n"
        )

        # Update text widget
        update_text_widget(self.text_widget, text)
    

    def homography_matrix_text(self, H):
        if (H is None):
            return "n/a"
        
        lines = [
            f"{H[0, 0]: {H_DIGITS}.{H_DECIMALS}f} {H[1, 0]: {H_DIGITS}.{H_DECIMALS}f} {H[2, 0]: {H_DIGITS}.{H_DECIMALS}f}",
            f"{H[0, 1]: {H_DIGITS}.{H_DECIMALS}f} {H[1, 1]: {H_DIGITS}.{H_DECIMALS}f} {H[2, 1]: {H_DIGITS}.{H_DECIMALS}f}",
            f"{H[0, 2]: {H_DIGITS}.{H_DECIMALS}f} {H[1, 2]: {H_DIGITS}.{H_DECIMALS}f} {H[2, 2]: {H_DIGITS}.{H_DECIMALS}f}"
        ]

        # Remove leading spaces
        min_leading_spaces = min(len(line) - len(line.lstrip()) for line in lines)
        lines = [line[min_leading_spaces:] for line in lines]
        return "\n".join(lines)