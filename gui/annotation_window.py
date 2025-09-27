"""
Annotation Window
Handles image annotation with bounding boxes, labels, and segmentation.
Enhanced with flexible canvas sizing for variable image dimensions.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk, ImageDraw
import cv2
import numpy as np
from typing import List, Dict, Tuple, Callable
import os

class AnnotationWindow:
    """Window for annotating images with bounding boxes and segmentation."""
    
    def __init__(self, parent: tk.Tk, project_data: dict, callback: Callable):
        self.parent = parent
        self.project_data = project_data
        self.callback = callback
        
        # Annotation state
        self.current_image_index = 0
        self.current_image = None
        self.current_photo = None
        self.scale_factor = 1.0
        self.canvas_offset = (0, 0)
        
        # Canvas size constraints
        self.min_canvas_width = 400
        self.min_canvas_height = 300
        self.max_canvas_width = 1200
        self.max_canvas_height = 800
        
        # Drawing state
        self.drawing_mode = 'bbox'  # 'bbox', 'segment'
        self.is_drawing = False
        self.start_x = 0
        self.start_y = 0
        self.current_bbox = None
        self.segment_points = []
        self.temp_line = None
        self.current_segmentation_id = None
        self.segmentation_in_progress = False
        
        # Annotations for current image
        self.current_annotations = []
        
        self.create_window()
        self.load_current_image()
        
    def create_window(self):
        """Create the annotation window."""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Image Annotation - GENxCRY")
        self.window.geometry("1400x900")
        self.window.grab_set()  # Make window modal
        
        # Main container
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(1, weight=3)  # Give more weight to canvas column
        main_frame.columnconfigure(2, weight=1)  # Sidebar gets less weight
        main_frame.rowconfigure(1, weight=1)
        
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        
        # Create UI components
        self.create_toolbar(main_frame)
        self.create_canvas_area(main_frame)
        self.create_sidebar(main_frame)
        
        # Bind window close event
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def create_toolbar(self, parent):
        """Create the toolbar with navigation and tools."""
        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Navigation
        nav_frame = ttk.LabelFrame(toolbar_frame, text="Navigation", padding="5")
        nav_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Button(nav_frame, text="◀ Previous", command=self.previous_image).grid(row=0, column=0, padx=2)
        
        self.image_info_var = tk.StringVar()
        self.update_image_info()
        ttk.Label(nav_frame, textvariable=self.image_info_var).grid(row=0, column=1, padx=10)
        
        ttk.Button(nav_frame, text="Next ▶", command=self.next_image).grid(row=0, column=2, padx=2)
        
        # Drawing tools
        tools_frame = ttk.LabelFrame(toolbar_frame, text="Drawing Tools", padding="5")
        tools_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        self.tool_var = tk.StringVar(value='bbox')
        ttk.Radiobutton(tools_frame, text="Bounding Box", variable=self.tool_var, 
                       value='bbox', command=self.change_tool).grid(row=0, column=0, padx=5)
        ttk.Radiobutton(tools_frame, text="Segmentation", variable=self.tool_var, 
                       value='segment', command=self.change_tool).grid(row=0, column=1, padx=5)
        
        # Zoom controls
        zoom_frame = ttk.LabelFrame(toolbar_frame, text="Zoom", padding="5")
        zoom_frame.grid(row=0, column=2, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Button(zoom_frame, text="Fit", command=self.fit_image).grid(row=0, column=0, padx=2)
        ttk.Button(zoom_frame, text="100%", command=self.actual_size).grid(row=0, column=1, padx=2)
        ttk.Button(zoom_frame, text="Zoom In", command=self.zoom_in).grid(row=0, column=2, padx=2)
        ttk.Button(zoom_frame, text="Zoom Out", command=self.zoom_out).grid(row=0, column=3, padx=2)
        
        # Actions
        actions_frame = ttk.LabelFrame(toolbar_frame, text="Actions", padding="5")
        actions_frame.grid(row=0, column=3, sticky=(tk.W, tk.E))
        
        ttk.Button(actions_frame, text="Clear All", command=self.clear_annotations).grid(row=0, column=0, padx=2)
        ttk.Button(actions_frame, text="Save & Close", command=self.save_and_close).grid(row=0, column=1, padx=2)
        
        toolbar_frame.columnconfigure(1, weight=1)
        
    def create_canvas_area(self, parent):
        """Create the flexible image canvas area."""
        self.canvas_frame = ttk.LabelFrame(parent, text="Image Canvas", padding="5")
        self.canvas_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        self.canvas_frame.columnconfigure(0, weight=1)
        self.canvas_frame.rowconfigure(0, weight=1)
        
        # Create canvas with scrollbars
        self.canvas = tk.Canvas(self.canvas_frame, bg='white', cursor='crosshair')
        v_scrollbar = ttk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(self.canvas_frame, orient="horizontal", command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Bind canvas events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)  # Right-click for segmentation
        self.canvas.bind("<Motion>", self.on_canvas_motion)
        self.canvas.bind("<MouseWheel>", self.on_canvas_scroll)
        self.canvas.bind("<Button-4>", self.on_canvas_scroll)
        self.canvas.bind("<Button-5>", self.on_canvas_scroll)
        
    def create_sidebar(self, parent):
        """Create the sidebar with annotation list and properties."""
        sidebar_frame = ttk.LabelFrame(parent, text="Annotations", padding="5")
        sidebar_frame.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        sidebar_frame.columnconfigure(0, weight=1)
        sidebar_frame.rowconfigure(1, weight=1)
        
        # Instructions
        instructions = ttk.Label(sidebar_frame, text="Instructions:\n• Select tool and draw on image\n• For segmentation: Click points, Right-click to finish\n• Right-click annotations to edit\n• Double-click to add labels\n• Use mouse wheel to zoom", 
                                justify=tk.LEFT, font=('Arial', 9))
        instructions.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Annotation list
        list_frame = ttk.Frame(sidebar_frame)
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Create treeview for annotations
        self.annotation_tree = ttk.Treeview(list_frame, columns=('Type', 'Label'), show='tree headings', height=10)
        self.annotation_tree.heading('#0', text='ID')
        self.annotation_tree.heading('Type', text='Type')
        self.annotation_tree.heading('Label', text='Label')
        
        self.annotation_tree.column('#0', width=50)
        self.annotation_tree.column('Type', width=80)
        self.annotation_tree.column('Label', width=100)
        
        tree_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.annotation_tree.yview)
        self.annotation_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.annotation_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Bind tree events
        self.annotation_tree.bind("<Double-1>", self.edit_annotation)
        self.annotation_tree.bind("<Button-3>", self.show_context_menu)
        
        # Properties frame
        props_frame = ttk.LabelFrame(sidebar_frame, text="Properties", padding="5")
        props_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(props_frame, text="Label:").grid(row=0, column=0, sticky=tk.W)
        self.label_entry = ttk.Entry(props_frame, width=20)
        self.label_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        
        ttk.Button(props_frame, text="Add Label", command=self.add_label_to_selected).grid(row=1, column=0, columnspan=2, pady=5)
        
        # Segmentation controls
        seg_frame = ttk.Frame(props_frame)
        seg_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Button(seg_frame, text="Finish Segmentation", command=self.finish_segmentation).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(seg_frame, text="Cancel Segmentation", command=self.cancel_segmentation).grid(row=0, column=1)
        
        props_frame.columnconfigure(1, weight=1)
        
    def calculate_optimal_canvas_size(self, img_width, img_height):
        """Calculate optimal canvas size based on image dimensions."""
        # Get available space (accounting for other UI elements)
        self.window.update_idletasks()
        available_width = self.window.winfo_width() - 400  # Account for sidebar and padding
        available_height = self.window.winfo_height() - 200  # Account for toolbar and padding
        
        # Apply constraints
        canvas_width = max(self.min_canvas_width, min(available_width, self.max_canvas_width))
        canvas_height = max(self.min_canvas_height, min(available_height, self.max_canvas_height))
        
        # Consider image aspect ratio
        img_aspect = img_width / img_height
        canvas_aspect = canvas_width / canvas_height
        
        # Adjust canvas size to better accommodate the image
        if img_aspect > canvas_aspect:
            # Image is wider - adjust canvas width if possible
            optimal_width = min(canvas_height * img_aspect, self.max_canvas_width)
            if optimal_width >= self.min_canvas_width:
                canvas_width = optimal_width
        else:
            # Image is taller - adjust canvas height if possible
            optimal_height = min(canvas_width / img_aspect, self.max_canvas_height)
            if optimal_height >= self.min_canvas_height:
                canvas_height = optimal_height
                
        return int(canvas_width), int(canvas_height)
        
    def update_image_info(self):
        """Update the image information display."""
        total = len(self.project_data['images'])
        current = self.current_image_index + 1
        filename = os.path.basename(self.project_data['images'][self.current_image_index]) if self.project_data['images'] else ""
        
        # Add image dimensions info
        if self.current_image:
            width, height = self.current_image.size
            self.image_info_var.set(f"Image {current}/{total}: {filename} ({width}×{height})")
        else:
            self.image_info_var.set(f"Image {current}/{total}: {filename}")
        
    def load_current_image(self):
        """Load and display the current image with flexible canvas sizing."""
        if not self.project_data['images']:
            return
            
        image_path = self.project_data['images'][self.current_image_index]
        
        try:
            # Load image
            self.current_image = Image.open(image_path)
            img_width, img_height = self.current_image.size
            
            # Calculate optimal canvas size
            canvas_width, canvas_height = self.calculate_optimal_canvas_size(img_width, img_height)
            
            # Update canvas size
            self.canvas.configure(width=canvas_width, height=canvas_height)
            
            # Calculate scale to fit image in canvas
            self.fit_image_to_canvas(canvas_width, canvas_height)
            
            # Update image info
            self.update_image_info()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {str(e)}")
            
    def fit_image_to_canvas(self, canvas_width=None, canvas_height=None):
        """Fit image to canvas with proper scaling."""
        if not self.current_image:
            return
            
        if canvas_width is None:
            canvas_width = self.canvas.winfo_width()
        if canvas_height is None:
            canvas_height = self.canvas.winfo_height()
            
        img_width, img_height = self.current_image.size
        
        # Calculate scale to fit canvas
        scale_x = canvas_width / img_width
        scale_y = canvas_height / img_height
        self.scale_factor = min(scale_x, scale_y, 1.0)  # Don't scale up beyond 100%
        
        self.update_image_display()
        
    def update_image_display(self):
        """Update the image display with current scale factor."""
        if not self.current_image:
            return
            
        img_width, img_height = self.current_image.size
        
        # Calculate display dimensions
        display_width = int(img_width * self.scale_factor)
        display_height = int(img_height * self.scale_factor)
        
        # Resize image for display
        display_image = self.current_image.resize((display_width, display_height), Image.Resampling.LANCZOS)
        self.current_photo = ImageTk.PhotoImage(display_image)
        
        # Update canvas
        self.canvas.configure(scrollregion=(0, 0, display_width, display_height))
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.current_photo, tags="image")
        
        # Load and redraw annotations
        self.load_annotations()
        self.update_annotation_list()
        
    def fit_image(self):
        """Fit image to current canvas size."""
        if self.current_image:
            self.fit_image_to_canvas()
            
    def actual_size(self):
        """Display image at 100% scale."""
        if self.current_image:
            self.scale_factor = 1.0
            self.update_image_display()
            
    def zoom_in(self):
        """Zoom in on the image."""
        if self.current_image:
            self.scale_factor = min(self.scale_factor * 1.2, 5.0)  # Max 500% zoom
            self.update_image_display()
            
    def zoom_out(self):
        """Zoom out on the image."""
        if self.current_image:
            self.scale_factor = max(self.scale_factor / 1.2, 0.1)  # Min 10% zoom
            self.update_image_display()
            
    def on_canvas_scroll(self, event):
        """Handle canvas scroll events for zooming."""
        if self.current_image:
            # Determine zoom direction
            if event.delta > 0 or event.num == 4:
                zoom_factor = 1.1
            else:
                zoom_factor = 0.9
                
            # Get mouse position relative to canvas
            canvas_x = self.canvas.canvasx(event.x)
            canvas_y = self.canvas.canvasy(event.y)
            
            # Calculate new scale
            old_scale = self.scale_factor
            new_scale = max(0.1, min(5.0, self.scale_factor * zoom_factor))
            
            if new_scale != old_scale:
                # Calculate zoom center
                zoom_ratio = new_scale / old_scale
                
                # Update scale and display
                self.scale_factor = new_scale
                self.update_image_display()
                
                # Adjust scroll position to zoom towards mouse
                new_canvas_x = canvas_x * zoom_ratio
                new_canvas_y = canvas_y * zoom_ratio
                
                # Center the zoom point
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()
                
                scroll_x = (new_canvas_x - canvas_width/2) / (self.current_image.width * self.scale_factor)
                scroll_y = (new_canvas_y - canvas_height/2) / (self.current_image.height * self.scale_factor)
                
                self.canvas.xview_moveto(max(0, min(1, scroll_x)))
                self.canvas.yview_moveto(max(0, min(1, scroll_y)))
        
    def load_annotations(self):
        """Load existing annotations for the current image."""
        image_path = self.project_data['images'][self.current_image_index]
        self.current_annotations = self.project_data['annotations'].get(image_path, []).copy()
        
        # Draw existing annotations on canvas
        for i, annotation in enumerate(self.current_annotations):
            self.draw_annotation(annotation, i)
            
    def draw_annotation(self, annotation: dict, index: int):
        """Draw an annotation on the canvas."""
        if annotation['type'] == 'bbox':
            x1, y1, x2, y2 = annotation['coordinates']
            # Scale coordinates
            x1 *= self.scale_factor
            y1 *= self.scale_factor
            x2 *= self.scale_factor
            y2 *= self.scale_factor
            
            self.canvas.create_rectangle(x1, y1, x2, y2, outline='red', width=2, 
                                       tags=f"annotation_{index}")
            
            # Draw label if exists
            if annotation.get('label'):
                self.canvas.create_text(x1, y1-10, text=annotation['label'], 
                                      fill='red', anchor=tk.SW, tags=f"annotation_{index}")
                                      
        elif annotation['type'] == 'segment':
            points = annotation['coordinates']
            # Scale points
            scaled_points = []
            for x, y in points:
                scaled_points.extend([x * self.scale_factor, y * self.scale_factor])
                
            if len(scaled_points) >= 6:  # At least 3 points
                self.canvas.create_polygon(scaled_points, outline='blue', fill='', width=2,
                                         tags=f"annotation_{index}")
                                         
                # Draw label if exists
                if annotation.get('label'):
                    # Calculate centroid for label placement
                    centroid_x = sum(x for x, y in points) / len(points) * self.scale_factor
                    centroid_y = sum(y for x, y in points) / len(points) * self.scale_factor
                    self.canvas.create_text(centroid_x, centroid_y, text=annotation['label'], 
                                          fill='blue', anchor=tk.CENTER, tags=f"annotation_{index}",
                                          font=('Arial', 10, 'bold'))
                                         
    def change_tool(self):
        """Change the current drawing tool."""
        self.drawing_mode = self.tool_var.get()
        cursor = 'crosshair' if self.drawing_mode == 'bbox' else 'pencil'
        self.canvas.configure(cursor=cursor)
        
    def on_canvas_click(self, event):
        """Handle canvas click events."""
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        if self.drawing_mode == 'bbox':
            self.start_x = x
            self.start_y = y
            self.is_drawing = True
            
        elif self.drawing_mode == 'segment':
            # Start new segmentation if none in progress
            if not self.segmentation_in_progress:
                self.segment_points = []
                self.segmentation_in_progress = True
                self.current_segmentation_id = f"temp_segment_{len(self.current_annotations)}"
                
            # Add point to segment
            actual_x = x / self.scale_factor
            actual_y = y / self.scale_factor
            self.segment_points.append((actual_x, actual_y))
            
            # Draw point
            self.canvas.create_oval(x-3, y-3, x+3, y+3, fill='blue', outline='darkblue', width=2, tags=self.current_segmentation_id)
            
            # Draw line to previous point
            if len(self.segment_points) > 1:
                prev_x = self.segment_points[-2][0] * self.scale_factor
                prev_y = self.segment_points[-2][1] * self.scale_factor
                self.canvas.create_line(prev_x, prev_y, x, y, fill='blue', width=2, tags=self.current_segmentation_id)
                
            # Show preview line to first point if we have enough points
            if len(self.segment_points) > 2:
                first_x = self.segment_points[0][0] * self.scale_factor
                first_y = self.segment_points[0][1] * self.scale_factor
                self.canvas.delete("preview_line")
                self.canvas.create_line(x, y, first_x, first_y, fill='lightblue', width=1, dash=(5, 5), tags="preview_line")
                
    def on_canvas_drag(self, event):
        """Handle canvas drag events."""
        if self.drawing_mode == 'bbox' and self.is_drawing:
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            
            # Remove previous temporary rectangle
            if self.current_bbox:
                self.canvas.delete(self.current_bbox)
                
            # Draw new temporary rectangle
            self.current_bbox = self.canvas.create_rectangle(
                self.start_x, self.start_y, x, y, outline='red', width=2, tags="temp_bbox"
            )
            
    def on_canvas_release(self, event):
        """Handle canvas release events."""
        if self.drawing_mode == 'bbox' and self.is_drawing:
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            
            # Create bounding box annotation
            if abs(x - self.start_x) > 10 and abs(y - self.start_y) > 10:  # Minimum size
                # Convert to actual image coordinates
                actual_x1 = self.start_x / self.scale_factor
                actual_y1 = self.start_y / self.scale_factor
                actual_x2 = x / self.scale_factor
                actual_y2 = y / self.scale_factor
                
                # Ensure correct order
                x1, x2 = min(actual_x1, actual_x2), max(actual_x1, actual_x2)
                y1, y2 = min(actual_y1, actual_y2), max(actual_y1, actual_y2)
                
                annotation = {
                    'type': 'bbox',
                    'coordinates': [x1, y1, x2, y2],
                    'label': ''
                }
                
                self.current_annotations.append(annotation)
                self.update_annotation_list()
                
                # Remove temporary rectangle
                if self.current_bbox:
                    self.canvas.delete(self.current_bbox)
                    self.current_bbox = None
                    
                # Redraw all annotations
                self.redraw_annotations()
                
            self.is_drawing = False
            
    def on_canvas_motion(self, event):
        """Handle canvas motion events."""
        # Show preview line for segmentation
        if self.drawing_mode == 'segment' and self.segmentation_in_progress and self.segment_points:
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            
            # Remove previous preview line
            self.canvas.delete("motion_preview")
            
            # Draw line from last point to current mouse position
            last_x = self.segment_points[-1][0] * self.scale_factor
            last_y = self.segment_points[-1][1] * self.scale_factor
            self.canvas.create_line(last_x, last_y, x, y, fill='lightblue', width=1, dash=(3, 3), tags="motion_preview")
    
    def on_canvas_right_click(self, event):
        """Handle right-click events (finish segmentation)."""
        if self.drawing_mode == 'segment' and self.segmentation_in_progress and len(self.segment_points) >= 3:
            self.finish_segmentation()
        elif not self.segmentation_in_progress:
            # Show context menu for existing annotations
            self.show_canvas_context_menu(event)
            
    def redraw_annotations(self):
        """Redraw all annotations on the canvas."""
        # Clear existing annotation drawings
        self.canvas.delete("annotation")
        for i in range(len(self.current_annotations)):
            self.canvas.delete(f"annotation_{i}")
            
        # Redraw all annotations
        for i, annotation in enumerate(self.current_annotations):
            self.draw_annotation(annotation, i)
            
    def update_annotation_list(self):
        """Update the annotation list display."""
        # Clear existing items
        for item in self.annotation_tree.get_children():
            self.annotation_tree.delete(item)
            
        # Add current annotations
        for i, annotation in enumerate(self.current_annotations):
            self.annotation_tree.insert('', 'end', text=str(i+1), 
                                      values=(annotation['type'], annotation.get('label', '')))
                                      
    def edit_annotation(self, event):
        """Edit the selected annotation."""
        selection = self.annotation_tree.selection()
        if selection:
            item = selection[0]
            index = int(self.annotation_tree.item(item, 'text')) - 1
            
            if 0 <= index < len(self.current_annotations):
                annotation = self.current_annotations[index]
                
                # Edit label
                current_label = annotation.get('label', '')
                new_label = simpledialog.askstring("Edit Label", "Enter label:", initialvalue=current_label)
                
                if new_label is not None:
                    annotation['label'] = new_label
                    self.update_annotation_list()
                    self.redraw_annotations()
                    
    def show_context_menu(self, event):
        """Show context menu for annotations."""
        selection = self.annotation_tree.selection()
        if selection:
            context_menu = tk.Menu(self.window, tearoff=0)
            context_menu.add_command(label="Edit Label", command=lambda: self.edit_annotation(event))
            context_menu.add_command(label="Delete", command=self.delete_selected_annotation)
            
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()
                
    def delete_selected_annotation(self):
        """Delete the selected annotation."""
        selection = self.annotation_tree.selection()
        if selection:
            item = selection[0]
            index = int(self.annotation_tree.item(item, 'text')) - 1
            
            if 0 <= index < len(self.current_annotations):
                self.current_annotations.pop(index)
                self.update_annotation_list()
                self.redraw_annotations()
                
    def add_label_to_selected(self):
        """Add label to selected annotation."""
        selection = self.annotation_tree.selection()
        label_text = self.label_entry.get().strip()
        
        if selection and label_text:
            item = selection[0]
            index = int(self.annotation_tree.item(item, 'text')) - 1
            
            if 0 <= index < len(self.current_annotations):
                self.current_annotations[index]['label'] = label_text
                self.label_entry.delete(0, tk.END)
                self.update_annotation_list()
                self.redraw_annotations()
    
    def finish_segmentation(self):
        """Finish the current segmentation and create annotation."""
        if self.segmentation_in_progress and len(self.segment_points) >= 3:
            # Clean up temporary drawing elements
            self.canvas.delete("preview_line")
            self.canvas.delete("motion_preview")
            
            # Create segmentation annotation
            annotation = {
                'type': 'segment',
                'coordinates': self.segment_points.copy(),
                'label': ''
            }
            
            self.current_annotations.append(annotation)
            
            # Clean up temporary segmentation
            if self.current_segmentation_id:
                self.canvas.delete(self.current_segmentation_id)
            
            # Reset segmentation state
            self.segment_points = []
            self.segmentation_in_progress = False
            self.current_segmentation_id = None
            
            # Update UI
            self.update_annotation_list()
            self.redraw_annotations()
            
            # Prompt for label
            label = simpledialog.askstring("Segmentation Label", "Enter label for this segmentation:")
            if label:
                self.current_annotations[-1]['label'] = label
                self.update_annotation_list()
                self.redraw_annotations()
    
    def cancel_segmentation(self):
        """Cancel the current segmentation in progress."""
        if self.segmentation_in_progress:
            # Clean up temporary drawing elements
            if self.current_segmentation_id:
                self.canvas.delete(self.current_segmentation_id)
            self.canvas.delete("preview_line")
            self.canvas.delete("motion_preview")
            
            # Reset segmentation state
            self.segment_points = []
            self.segmentation_in_progress = False
            self.current_segmentation_id = None
    
    def show_canvas_context_menu(self, event):
        """Show context menu on canvas right-click."""
        context_menu = tk.Menu(self.window, tearoff=0)
        context_menu.add_command(label="Clear All Annotations", command=self.clear_annotations)
        
        if self.segmentation_in_progress:
            context_menu.add_separator()
            context_menu.add_command(label="Finish Segmentation", command=self.finish_segmentation)
            context_menu.add_command(label="Cancel Segmentation", command=self.cancel_segmentation)
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
                
    def clear_annotations(self):
        """Clear all annotations for the current image."""
        if self.current_annotations or self.segmentation_in_progress:
            result = messagebox.askyesno("Confirm", "Clear all annotations for this image?")
            if result:
                self.current_annotations.clear()
                
                # Cancel any segmentation in progress
                self.cancel_segmentation()
                
                # Clear all temporary elements
                self.canvas.delete("temp_segment")
                self.canvas.delete("temp_bbox")
                self.canvas.delete("preview_line")
                self.canvas.delete("motion_preview")
                
                self.update_annotation_list()
                self.redraw_annotations()
                
    def previous_image(self):
        """Navigate to previous image."""
        if self.current_image_index > 0:
            self.save_current_annotations()
            self.current_image_index -= 1
            self.update_image_info()
            self.load_current_image()
            
    def next_image(self):
        """Navigate to next image."""
        if self.current_image_index < len(self.project_data['images']) - 1:
            self.save_current_annotations()
            self.current_image_index += 1
            self.update_image_info()
            self.load_current_image()
            
    def save_current_annotations(self):
        """Save annotations for the current image."""
        if self.project_data['images']:
            image_path = self.project_data['images'][self.current_image_index]
            self.project_data['annotations'][image_path] = self.current_annotations.copy()
            
    def save_and_close(self):
        """Save all annotations and close the window."""
        self.save_current_annotations()
        
        # Check if we have annotations
        total_annotations = sum(len(annotations) for annotations in self.project_data['annotations'].values())
        
        if total_annotations == 0:
            result = messagebox.askyesno("Warning", "No annotations were created. Continue anyway?")
            if not result:
                return
                
        self.callback()
        self.window.destroy()
        
    def on_close(self):
        """Handle window close event."""
        result = messagebox.askyesno("Confirm", "Save annotations and close?")
        if result:
            self.save_and_close()