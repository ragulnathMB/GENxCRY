"""
Image Selection Frame
Handles the first stage of the pipeline - selecting input images and annotation types.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
from typing import List, Callable

class ImageSelectionFrame:
    """Frame for selecting images and annotation types."""
    
    def __init__(self, parent: tk.Widget, project_data: dict, callback: Callable):
        self.parent = parent
        self.project_data = project_data
        self.callback = callback
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the image selection interface."""
        # Main container
        main_frame = ttk.Frame(self.parent)
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Image Selection & Annotation Types", style='Header.TLabel')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Left panel - Controls
        controls_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        controls_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Image selection
        ttk.Label(controls_frame, text="Select Images:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        ttk.Button(controls_frame, text="Browse Images", command=self.browse_images).grid(row=1, column=0, sticky=(tk.W, tk.E), pady=2)
        ttk.Button(controls_frame, text="Add Folder", command=self.add_folder).grid(row=2, column=0, sticky=(tk.W, tk.E), pady=2)
        ttk.Button(controls_frame, text="Clear All", command=self.clear_images).grid(row=3, column=0, sticky=(tk.W, tk.E), pady=2)
        
        # Annotation types
        ttk.Separator(controls_frame, orient='horizontal').grid(row=4, column=0, sticky=(tk.W, tk.E), pady=10)
        ttk.Label(controls_frame, text="Annotation Types:", font=('Arial', 10, 'bold')).grid(row=5, column=0, sticky=tk.W, pady=(0, 5))
        
        self.annotation_vars = {
            'bounding_box': tk.BooleanVar(value=True),
            'labeling': tk.BooleanVar(value=True),
            'segmentation': tk.BooleanVar()
        }
        
        ttk.Checkbutton(controls_frame, text="Bounding Box Annotation", 
                       variable=self.annotation_vars['bounding_box']).grid(row=6, column=0, sticky=tk.W, pady=2)
        ttk.Checkbutton(controls_frame, text="Labeling Annotation", 
                       variable=self.annotation_vars['labeling']).grid(row=7, column=0, sticky=tk.W, pady=2)
        ttk.Checkbutton(controls_frame, text="Segmentation Annotation", 
                       variable=self.annotation_vars['segmentation']).grid(row=8, column=0, sticky=tk.W, pady=2)
        
        # Proceed button
        ttk.Separator(controls_frame, orient='horizontal').grid(row=9, column=0, sticky=(tk.W, tk.E), pady=10)
        self.proceed_btn = ttk.Button(controls_frame, text="Proceed to Annotation", 
                                     command=self.proceed_to_annotation, state='disabled')
        self.proceed_btn.grid(row=10, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Right panel - Image preview
        preview_frame = ttk.LabelFrame(main_frame, text="Selected Images", padding="10")
        preview_frame.grid(row=1, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        
        # Create scrollable frame for images
        self.create_image_preview(preview_frame)
        
    def create_image_preview(self, parent):
        """Create scrollable image preview area."""
        # Create canvas and scrollbar
        canvas = tk.Canvas(parent, bg='white')
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.canvas = canvas
        
        # Bind mousewheel to canvas
        canvas.bind("<MouseWheel>", self._on_mousewheel)
        
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def browse_images(self):
        """Browse and select image files."""
        filetypes = [
            ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.gif"),
            ("JPEG files", "*.jpg *.jpeg"),
            ("PNG files", "*.png"),
            ("All files", "*.*")
        ]
        
        files = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=filetypes
        )
        
        if files:
            self.add_images(files)
            
    def add_folder(self):
        """Add all images from a selected folder."""
        folder = filedialog.askdirectory(title="Select Image Folder")
        
        if folder:
            image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif'}
            image_files = []
            
            for file in os.listdir(folder):
                if os.path.splitext(file.lower())[1] in image_extensions:
                    image_files.append(os.path.join(folder, file))
            
            if image_files:
                self.add_images(image_files)
            else:
                messagebox.showinfo("Info", "No image files found in the selected folder.")
                
    def add_images(self, file_paths: List[str]):
        """Add images to the project."""
        added_count = 0
        
        for file_path in file_paths:
            if file_path not in self.project_data['images']:
                self.project_data['images'].append(file_path)
                added_count += 1
                
        if added_count > 0:
            self.update_image_preview()
            self.update_proceed_button()
            messagebox.showinfo("Success", f"Added {added_count} image(s) to the project.")
        else:
            messagebox.showinfo("Info", "No new images were added (duplicates ignored).")
            
    def clear_images(self):
        """Clear all selected images."""
        if self.project_data['images']:
            result = messagebox.askyesno("Confirm", "Are you sure you want to clear all images?")
            if result:
                self.project_data['images'].clear()
                self.project_data['annotations'].clear()
                self.update_image_preview()
                self.update_proceed_button()
                
    def update_image_preview(self):
        """Update the image preview display."""
        # Clear existing previews
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        # Add image previews
        for i, image_path in enumerate(self.project_data['images']):
            self.create_image_item(i, image_path)
            
    def create_image_item(self, index: int, image_path: str):
        """Create a preview item for an image."""
        item_frame = ttk.Frame(self.scrollable_frame)
        item_frame.grid(row=index, column=0, sticky=(tk.W, tk.E), pady=5, padx=5)
        item_frame.columnconfigure(1, weight=1)
        
        try:
            # Load and resize image for preview
            image = Image.open(image_path)
            image.thumbnail((80, 80), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            
            # Image preview
            img_label = ttk.Label(item_frame, image=photo)
            img_label.image = photo  # Keep a reference
            img_label.grid(row=0, column=0, rowspan=2, padx=(0, 10))
            
        except Exception as e:
            # If image can't be loaded, show placeholder
            img_label = ttk.Label(item_frame, text="[Image]", width=10, relief='sunken')
            img_label.grid(row=0, column=0, rowspan=2, padx=(0, 10))
            
        # Image info
        filename = os.path.basename(image_path)
        ttk.Label(item_frame, text=filename, font=('Arial', 9, 'bold')).grid(row=0, column=1, sticky=tk.W)
        ttk.Label(item_frame, text=image_path, font=('Arial', 8), foreground='gray').grid(row=1, column=1, sticky=tk.W)
        
        # Remove button
        remove_btn = ttk.Button(item_frame, text="Remove", width=8,
                               command=lambda idx=index: self.remove_image(idx))
        remove_btn.grid(row=0, column=2, rowspan=2, padx=(10, 0))
        
    def remove_image(self, index: int):
        """Remove an image from the project."""
        if 0 <= index < len(self.project_data['images']):
            image_path = self.project_data['images'][index]
            self.project_data['images'].pop(index)
            
            # Remove associated annotations
            if image_path in self.project_data['annotations']:
                del self.project_data['annotations'][image_path]
                
            self.update_image_preview()
            self.update_proceed_button()
            
    def update_proceed_button(self):
        """Update the proceed button state."""
        if self.project_data['images'] and any(var.get() for var in self.annotation_vars.values()):
            self.proceed_btn.configure(state='normal')
        else:
            self.proceed_btn.configure(state='disabled')
            
    def proceed_to_annotation(self):
        """Proceed to the annotation stage."""
        # Save selected annotation types
        selected_types = [
            annotation_type for annotation_type, var in self.annotation_vars.items()
            if var.get()
        ]
        
        if not selected_types:
            messagebox.showwarning("Warning", "Please select at least one annotation type.")
            return
            
        self.project_data['annotation_types'] = selected_types
        
        # Initialize annotations dictionary
        for image_path in self.project_data['images']:
            if image_path not in self.project_data['annotations']:
                self.project_data['annotations'][image_path] = []
                
        # Call the callback
        self.callback()
