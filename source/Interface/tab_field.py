import tkinter as tk
from tkinter import ttk

from resources import Resources
from interface.interface_custom import Tab, update_text_widget, x_y_input
from interface.grid_editor import GridEditor


class TabField(Tab):
    def __init__(self, resources:Resources):
        Tab.__init__(self, resources)
    

    def load(self, master):
        super().load(master)

        self.changing_dimensions = False
        p1, p2 = self.resources.field_points[0], self.resources.field_points[1]
        self.plane_width, self.plane_height = (abs(p1[0] - p2[0]), abs(p1[1] - p2[1]))

        # Split display
        self.tab_frame.grid_columnconfigure(0, weight=1)
        self.tab_frame.grid_columnconfigure(1, weight=0, minsize=10)
        self.tab_frame.grid_columnconfigure(2, weight=1)
        self.tab_frame.grid_rowconfigure(0, weight=1)

        # Grid editor
        self.grid_editor = GridEditor(self.tab_frame)
        self.grid_editor.grid(row=0, column=2, sticky="nsew")

        self.grid_editor.load(self.resources.image_field, self.resources.field_points, self.callback_change, self.callback_apply, True)

        # Information
        self.information_frame = ttk.Frame(self.tab_frame)
        self.information_frame.grid(row=0, column=0, sticky="nsew")
        self.information_frame.pack_propagate(False)

        self.dimensions_label = tk.Text(self.information_frame, height=1, wrap="word", state="disabled", bg='gray94', borderwidth=0)
        update_text_widget(self.dimensions_label, "Plane dimensions (cm):")
        self.dimensions_label.pack(anchor="w")
        self.dimensions_frame, self.dimensions_input_x, self.dimensions_input_y = x_y_input(self.information_frame)
        self.dimensions_frame.pack(anchor="w")
        self.dimensions_input_x.bind("<<Modified>>", lambda event: self.edit_dimension(event, 0))
        self.dimensions_input_y.bind("<<Modified>>", lambda event: self.edit_dimension(event, 1))
        self.update_dimensions()

        self.remaining_info_label = tk.Text(self.information_frame, height=8, wrap="word", state="disabled", bg='gray94', borderwidth=0)
        self.update_information()
        self.remaining_info_label.pack(anchor="w")

        self.flippers_frame, self.flippers_input_x, self.flippers_input_y = x_y_input(self.information_frame)
        self.flippers_frame.pack(anchor="w")
        flippers = (tuple)(self.resources.specifications['flippers'])
        update_text_widget(self.flippers_input_x, flippers[0])
        update_text_widget(self.flippers_input_y, flippers[1])
        self.flippers_input_x.bind("<<Modified>>", self.edit_flippers)
        self.flippers_input_y.bind("<<Modified>>", self.edit_flippers)


    def callback_change(self, points):
        self.plane_width, self.plane_height = abs(round(points[0][0]) - round(points[1][0])), abs(round(points[0][1]) - round(points[1][1]))
        self.update_dimensions()

    
    def callback_apply(self, points):
        self.resources.specifications['field']['points'] = list(map(lambda t: tuple(map(round, t)), points.copy()))
        self.resources.save_specifications_changes()
        self.resources._H_inv_field = None
        self.resources.recalculate_exports()
        for reference in self.resources.references.values():
            reference.H_computed = False
    

    def edit_dimension(self, event, axis:int):
        input = self.dimensions_input_x if axis == 0 else self.dimensions_input_y
        if input.edit_modified() and not self.changing_dimensions:
            try:
                length_cm = float(input.get("1.0", tk.END).strip())
                length_px = self.plane_width if axis == 0 else self.plane_height
                self.resources.specifications['field']['cms_per_pixel'] = float(length_cm / length_px)
                self.resources.save_specifications_changes()
                self.update_dimensions(update_x=(axis != 0), update_y=(axis != 1))
                self.update_information()
            except:
                pass
        input.edit_modified(False)
    

    def edit_flippers(self, event):
        try:
            flippers_x = float(self.flippers_input_x.get("1.0", tk.END).strip())
            flippers_y = float(self.flippers_input_y.get("1.0", tk.END).strip())
            self.resources.specifications['flippers'] = (flippers_x, flippers_y)
            self.resources.save_specifications_changes()
        except:
            pass
        self.flippers_input_x.edit_modified(False)
        self.flippers_input_y.edit_modified(False)
    

    def update_dimensions(self, update_x:bool=True, update_y:bool=True):
        (width, height) = (self.plane_width * self.resources.field_scale, self.plane_height * self.resources.field_scale)
        self.grid_editor.field_dimensions = (width, height)
        self.grid_editor.compute_matrix()
        self.grid_editor.update_image()
        self.grid_editor.apply_updated_plane()
        self.changing_dimensions = True
        if update_x:
            update_text_widget(self.dimensions_input_x, f"{width:.1f}")
        if update_y:
            update_text_widget(self.dimensions_input_y, f"{height:.1f}")
        self.tab_frame.after(10, lambda: setattr(self, "changing_dimensions", False))


    def update_information(self):
        cm_per_pixels = self.resources.field_scale
        pixels_per_cm = (1 / cm_per_pixels) if cm_per_pixels != 0 else 0
        image_field_h, image_field_w = self.resources.image_field.shape[:2]
        text = (
            f"\nImage dimensions (px): \n{image_field_w} x {image_field_h}\n\n"
            f"Pixels per cm: \n{pixels_per_cm:.1f}\n\n"
            f"Flippers position (cm):"
        )
        update_text_widget(self.remaining_info_label, text)
