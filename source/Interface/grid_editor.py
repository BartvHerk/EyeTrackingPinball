import tkinter as tk
from tkinter import ttk
import numpy as np

from image_processing import cvimage_to_tkimage, draw_perspective_grid, draw_polygon, resize_image_to_fit
from resources import Resources
from homography import compute_perspective_mapping, is_convex_quadrilateral, perspective_mapping_inverse, sort_corners


class GridEditor(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.resources = Resources()

        self.img:np.ndarray = None
        self.img_width, self.img_height = 0, 0
        self.points:list[tuple[int, int]] = None
        self.points_saved:list[tuple[int, int]] = None
        self.editing = False
        self.rectified = True
        self.field_dimensions = self.resources.field_dimensions

        # Split display
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0, minsize=10)
        self.grid_rowconfigure(2, weight=0)
        self.grid_propagate(False)

        # Editor
        self.frame_editor = ttk.Frame(self, relief="groove", borderwidth=1, padding=10)
        self.frame_editor.grid(row=0, column=0, sticky="nsew")
        self.frame_editor.bind("<Configure>", self.on_resize)

        self.image_label = ttk.Label(self.frame_editor, anchor="center")
        self.image_label.pack(fill="both", expand=True)

        self.image_label.bind("<ButtonPress-1>", self.click_hold)
        self.image_label.bind("<B1-Motion>", self.click_hold)

        # Buttons
        self.frame_buttons = ttk.Frame(self)
        self.frame_buttons.grid(row=2, column=0, sticky="nsew")

        self.frame_buttons.columnconfigure(0, weight=0)
        self.frame_buttons.columnconfigure(1, weight=0)
        self.frame_buttons.columnconfigure(2, weight=1)
        self.frame_buttons.columnconfigure(3, weight=0)

        self.button_edit = ttk.Button(self.frame_buttons, text="Edit", command=self.edit_start)
        self.button_edit.config(state="disabled")
        self.button_edit.grid(row=0, column=0, sticky='w')

        self.button_apply = ttk.Button(self.frame_buttons, text="Apply", command=self.apply)
        self.button_apply.config(state="disabled")
        self.button_apply.grid(row=0, column=1, sticky='w')

        self.button_revert = ttk.Button(self.frame_buttons, text="Revert", command=self.revert)
        self.button_revert.config(state="disabled")
        self.button_revert.grid(row=0, column=2, sticky='w')

        self.check_var_show = tk.BooleanVar()
        self.check_var_show.set(self.resources.settings["show_plane"])
        self.check_button_show = ttk.Checkbutton(self.frame_buttons, text="Show plane", variable=self.check_var_show, command=self.on_check_show)
        self.check_button_show.config(state="disabled")
        self.check_button_show.grid(row=0, column=3, sticky='e')

    
    def load(self, img:np.ndarray, points:list[tuple[int, int]], callback_change, callback_apply, rectified:bool=True):
        self.button_edit.config(state="normal")
        self.check_button_show.config(state="normal")
        self.callback_change = callback_change
        self.callback_apply = callback_apply

        self.img = img
        self.img_height, self.img_width = img.shape[:2]

        self.points = points
        self.rectified = rectified
        if points is None:
            self.create_points()
        self.points_saved = self.points.copy()

        self.compute_matrix()
        self.update_image()
    

    def create_points(self):
        self.points = []
        self.points.append((0, 0))
        self.points.append((self.img_width - 1, self.img_height - 1))
        if not self.rectified:
            self.points.append((self.img_width - 1, 0))
            self.points.append((0, self.img_height - 1))

    
    def plane_points(self):
        plane_points = self.points.copy()
        if self.rectified:
            p1, p2 = self.points[0], self.points[1]
            plane_points.append((p1[0], p2[1]))
            plane_points.append((p2[0], p1[1]))
        plane_points = sort_corners(plane_points)
        return plane_points
    

    def click_hold(self, event):
        if self.editing:
            # Convert label coords to image coords
            label_width, label_height = (self.frame_editor.winfo_width(), self.frame_editor.winfo_height())
            offset_x = (label_width - self.img_scaled_width) // 2
            offset_y = (label_height - self.img_scaled_height) // 2
            img_x, img_y = (int)((event.x - offset_x + 10) / self.scale_factor), (int)((event.y - offset_y + 10) / self.scale_factor)
            
            # Move point
            points = self.plane_points()
            index = min(range(len(points)), key=lambda i: (points[i][0] - img_x)**2 + (points[i][1] - img_y)**2)
            points[index] = (img_x, img_y)
            if not self.rectified:
                self.points = points
                self.callback_change()
            else:
                self.points = [points[index], points[(index + 2) % 4]]
                self.callback_change(self.points)
            self.compute_matrix()
            self.update_image()
    

    def compute_matrix(self):
        points = sort_corners(self.plane_points())
        self.valid_matrix = False
        self.H = None
        if is_convex_quadrilateral(points): # Generate homography matrix
            self.H = compute_perspective_mapping(points, self.field_dimensions)
            try:
                self.H_inv = perspective_mapping_inverse(self.H)
                self.valid_matrix = True
            except:
                pass
    

    def update_image(self):
        max_size = (self.frame_editor.winfo_width() - 24, self.frame_editor.winfo_height() - 24)
        try:
            img_scaled, self.scale_factor = resize_image_to_fit(self.img, max_size)
            self.img_scaled_height, self.img_scaled_width = img_scaled.shape[:2]
            if (self.check_var_show.get() or self.editing):
                if self.valid_matrix:
                    draw_perspective_grid(img_scaled, self.H_inv, self.scale_factor, self.field_dimensions)
                else:
                    scaled_plane_points = list(map(lambda t: tuple(x * self.scale_factor for x in t), self.plane_points()))
                    draw_polygon(img_scaled, scaled_plane_points)
            image = cvimage_to_tkimage(img_scaled)
            self.image_label.config(image=image)
            self.image_label.image = image
        except:
            pass
    

    def edit_start(self):
        self.editing = True
        self.button_edit.config(state="disabled")
        self.button_apply.config(state="normal")
        self.button_revert.config(state="normal")
        self.update_image()
    

    def edit_finish(self):
        self.editing = False
        self.button_edit.config(state="normal")
        self.button_apply.config(state="disabled")
        self.button_revert.config(state="disabled")
        self.update_image()


    def apply(self):
        self.edit_finish()
        self.points_saved = self.points
        self.apply_updated_plane()
    

    def apply_updated_plane(self):
        self.callback_apply(self.points)


    def revert(self):
        self.edit_finish()
        self.points = self.points_saved
        self.callback_change() if not self.rectified else self.callback_change(self.points)
        self.compute_matrix()
        self.update_image()


    def on_check_show(self):
        self.resources.settings["show_plane"] = self.check_var_show.get()
        self.resources.save_settings_changes()
        self.update_image()


    def on_resize(self, event):
        if self.img is not None:
            self.update_image()