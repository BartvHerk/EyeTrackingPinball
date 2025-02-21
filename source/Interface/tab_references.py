import tkinter as tk
from tkinter import ttk

from resources import Resources
from Interface.interface_custom import Tab, list_layout
from containers import ContReference
from image_processing import cvimage_to_tkimage, draw_perspective_grid, resize_image_to_fit
from homography import set_perspective_mapping


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

        # Active reference display
        selected_item_frame.grid_columnconfigure(0, weight=1)
        selected_item_frame.grid_columnconfigure(1, weight=0, minsize=10)
        selected_item_frame.grid_columnconfigure(2, weight=1)
        selected_item_frame.grid_rowconfigure(0, weight=1)

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

        # Buttons
        self.button_frame = ttk.Frame(self.information_frame) #, relief="groove", borderwidth=1)
        self.button_frame.config(height=100)
        self.button_frame.grid(row=1, column=0, sticky="nsew")
        self.button_frame.pack_propagate(False)

        self.button_homography = ttk.Button(self.button_frame, text="Define perspective plane", command=self.on_button_homography_click)
        self.button_homography.config(state="disabled")
        self.button_homography.pack(side='bottom', anchor='w')

        self.check_var_plane = tk.BooleanVar()
        self.check_var_plane.set(self.resources.settings["show_perspective_plane"])
        self.check_button_plane = ttk.Checkbutton(self.button_frame, text="Show perspective plane", variable=self.check_var_plane, command=self.on_check_plane)
        self.check_button_plane.config(state="disabled")
        self.check_button_plane.pack(side='bottom', anchor='w')

        # Image
        self.selected_reference_frame = ttk.Frame(selected_item_frame, relief="groove", borderwidth=1, padding=10)
        self.selected_reference_frame.grid(row=0, column=2, sticky="nsew")
        self.selected_reference_frame.bind("<Configure>", self.on_resize)
        self.selected_reference_frame.pack_propagate(False)

        self.display_reference = ttk.Label(self.selected_reference_frame, anchor="center")
        self.display_reference.pack(fill="both", expand=True)

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
        self.update_image()
        self.update_information()
        self.check_button_plane.config(state="normal")
        self.button_homography.config(state="normal")

    
    def on_resize(self, event):
        if (self.active_reference is None):
            return

        self.update_image()

    
    def on_check_plane(self):
        self.resources.settings["show_perspective_plane"] = self.check_var_plane.get()
        self.resources.save_settings_changes()
        self.update_image()
    

    def on_button_homography_click(self):
        if set_perspective_mapping(self.resources.references[self.active_reference.name], self.resources.field_dimensions):
            self.resources.on_homography_matrix_update(self.active_reference)
            self.update_image()
            self.update_information()
    

    def update_image(self):
        width = self.selected_reference_frame.winfo_width()
        height = self.selected_reference_frame.winfo_height()
        img, scale_factor = resize_image_to_fit(self.active_reference.image, (width, height))
        if (self.check_var_plane.get() and self.active_reference.H_inv is not None):
            draw_perspective_grid(img, self.active_reference.H_inv, scale_factor, self.resources.field_dimensions)
        image_reference = cvimage_to_tkimage(img)
        self.display_reference.config(image=image_reference)
        self.display_reference.image = image_reference


    def update_information(self):
        # Get information
        name = self.active_reference.name
        reference_image_height, reference_image_width = self.active_reference.image.shape[:2]
        text = (
            f"Name:\n{name}\n\n"
            f"Path:\n{self.active_reference.path}\n\n"
            f"Dimensions: \n{reference_image_width} x {reference_image_height}\n\n"
            f"Homography matrix: \n{self.homography_matrix_text()}\n\n"
        )

        # Update text widget
        self.text_widget.config(state="normal")
        self.text_widget.delete(1.0, "end")
        self.text_widget.insert(1.0, text)
        self.text_widget.config(state="disabled")
    

    def homography_matrix_text(self):
        H = self.active_reference.H
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