"""
Main Window for GENxCRY Application
Handles the primary interface and navigation between different stages.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Dict, Any
import os

from gui.image_selection import ImageSelectionFrame
from gui.annotation_window import AnnotationWindow
from gui.augmentation_config import AugmentationConfigFrame
from gui.dataset_generation import DatasetGenerationFrame

class MainWindow:
    """Main application window managing the pipeline stages."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.current_stage = 0
        self.project_data = {
            'images': [],
            'annotations': {},
            'annotation_types': [],
            'augmentation_config': {},
            'dataset_config': {}
        }
        
        self.setup_ui()
        self.setup_styles()
        
    def setup_styles(self):
        """Setup custom styles for the application."""
        style = ttk.Style()
        
        # Configure custom styles
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Subtitle.TLabel', font=('Arial', 12))
        style.configure('Header.TLabel', font=('Arial', 14, 'bold'))
        
    def setup_ui(self):
        """Setup the main user interface."""
        # Create main container
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(1, weight=1)
        
        # Create header
        self.create_header()
        
        # Create navigation sidebar
        self.create_sidebar()
        
        # Create content area
        self.create_content_area()
        
        # Start with image selection stage
        self.show_image_selection()
        
    def create_header(self):
        """Create the application header."""
        header_frame = ttk.Frame(self.main_frame)
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Title
        title_label = ttk.Label(header_frame, text="GENxCRY", style='Title.TLabel')
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # Subtitle
        subtitle_label = ttk.Label(header_frame, text="AI Dataset Generator by RN Software", style='Subtitle.TLabel')
        subtitle_label.grid(row=1, column=0, sticky=tk.W)
        
        # Progress indicator
        self.progress_var = tk.StringVar(value="Stage 1/4: Image Selection")
        progress_label = ttk.Label(header_frame, textvariable=self.progress_var)
        progress_label.grid(row=0, column=1, sticky=tk.E)
        
        header_frame.columnconfigure(1, weight=1)
        
    def create_sidebar(self):
        """Create the navigation sidebar."""
        sidebar_frame = ttk.LabelFrame(self.main_frame, text="Pipeline Stages", padding="10")
        sidebar_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Stage buttons
        self.stage_buttons = []
        stages = [
            ("1. Image Selection", self.show_image_selection),
            ("2. Annotation", self.show_annotation),
            ("3. Augmentation Config", self.show_augmentation_config),
            ("4. Dataset Generation", self.show_dataset_generation)
        ]
        
        for i, (text, command) in enumerate(stages):
            btn = ttk.Button(sidebar_frame, text=text, command=command, width=20)
            btn.grid(row=i, column=0, pady=2, sticky=(tk.W, tk.E))
            self.stage_buttons.append(btn)
            
            # Disable buttons beyond current stage initially
            if i > 0:
                btn.configure(state='disabled')
        
        # Project info
        ttk.Separator(sidebar_frame, orient='horizontal').grid(row=len(stages), column=0, sticky=(tk.W, tk.E), pady=10)
        
        info_frame = ttk.Frame(sidebar_frame)
        info_frame.grid(row=len(stages)+1, column=0, sticky=(tk.W, tk.E))
        
        ttk.Label(info_frame, text="Project Info:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W)
        
        self.info_images = ttk.Label(info_frame, text="Images: 0")
        self.info_images.grid(row=1, column=0, sticky=tk.W)
        
        self.info_annotations = ttk.Label(info_frame, text="Annotations: 0")
        self.info_annotations.grid(row=2, column=0, sticky=tk.W)
        
    def create_content_area(self):
        """Create the main content area."""
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.rowconfigure(0, weight=1)
        
    def clear_content(self):
        """Clear the content area."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
    def update_project_info(self):
        """Update the project information display."""
        self.info_images.configure(text=f"Images: {len(self.project_data['images'])}")
        annotation_count = sum(len(annotations) for annotations in self.project_data['annotations'].values())
        self.info_annotations.configure(text=f"Annotations: {annotation_count}")
        
    def show_image_selection(self):
        """Show the image selection stage."""
        self.current_stage = 0
        self.progress_var.set("Stage 1/4: Image Selection")
        self.clear_content()
        
        self.image_selection_frame = ImageSelectionFrame(
            self.content_frame, 
            self.project_data,
            self.on_images_selected
        )
        
    def show_annotation(self):
        """Show the annotation stage."""
        if not self.project_data['images']:
            messagebox.showwarning("Warning", "Please select images first!")
            return
            
        self.current_stage = 1
        self.progress_var.set("Stage 2/4: Annotation")
        
        # Open annotation window
        self.annotation_window = AnnotationWindow(
            self.root,
            self.project_data,
            self.on_annotation_complete
        )
        
    def show_augmentation_config(self):
        """Show the augmentation configuration stage."""
        if not self.project_data['annotations']:
            messagebox.showwarning("Warning", "Please complete annotations first!")
            return
            
        self.current_stage = 2
        self.progress_var.set("Stage 3/4: Augmentation Configuration")
        self.clear_content()
        
        self.augmentation_frame = AugmentationConfigFrame(
            self.content_frame,
            self.project_data,
            self.on_augmentation_configured
        )
        
    def show_dataset_generation(self):
        """Show the dataset generation stage."""
        if not self.project_data['augmentation_config']:
            messagebox.showwarning("Warning", "Please configure augmentation settings first!")
            return
            
        self.current_stage = 3
        self.progress_var.set("Stage 4/4: Dataset Generation")
        self.clear_content()
        
        self.dataset_frame = DatasetGenerationFrame(
            self.content_frame,
            self.project_data,
            self.on_dataset_generated
        )
        
    def on_images_selected(self):
        """Callback when images are selected."""
        self.stage_buttons[1].configure(state='normal')
        self.update_project_info()
        
    def on_annotation_complete(self):
        """Callback when annotation is complete."""
        self.stage_buttons[2].configure(state='normal')
        self.update_project_info()
        
    def on_augmentation_configured(self):
        """Callback when augmentation is configured."""
        self.stage_buttons[3].configure(state='normal')
        
    def on_dataset_generated(self):
        """Callback when dataset generation is complete."""
        messagebox.showinfo("Success", "Dataset generated successfully!")
