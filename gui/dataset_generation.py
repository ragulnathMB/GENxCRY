"""
Dataset Generation Frame
Handles the final stage - configuring and generating the dataset.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Callable
import os
import threading
from core.dataset_generator import DatasetGenerator

class DatasetGenerationFrame:
    """Frame for configuring and generating the final dataset."""
    
    def __init__(self, parent: tk.Widget, project_data: dict, callback: Callable):
        self.parent = parent
        self.project_data = project_data
        self.callback = callback
        
        # Generation state
        self.is_generating = False
        self.generator = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the dataset generation interface."""
        # Main container
        main_frame = ttk.Frame(self.parent)
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Dataset Generation", style='Header.TLabel')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Left panel - Configuration
        config_frame = ttk.LabelFrame(main_frame, text="Dataset Configuration", padding="10")
        config_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Output settings
        ttk.Label(config_frame, text="Output Directory:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        output_frame = ttk.Frame(config_frame)
        output_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        output_frame.columnconfigure(0, weight=1)
        
        self.output_path_var = tk.StringVar(value=os.path.join(os.getcwd(), "generated_dataset"))
        self.output_entry = ttk.Entry(output_frame, textvariable=self.output_path_var)
        self.output_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(output_frame, text="Browse", command=self.browse_output_directory).grid(row=0, column=1)
        
        # Dataset size
        ttk.Label(config_frame, text="Dataset Size:", font=('Arial', 10, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=(10, 5))
        
        size_frame = ttk.Frame(config_frame)
        size_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(size_frame, text="Number of images:").grid(row=0, column=0, sticky=tk.W)
        self.dataset_size = tk.IntVar(value=1000)
        size_spinbox = ttk.Spinbox(size_frame, from_=100, to=10000, textvariable=self.dataset_size, width=10)
        size_spinbox.grid(row=0, column=1, padx=(5, 0))
        
        # Export formats
        ttk.Label(config_frame, text="Export Formats:", font=('Arial', 10, 'bold')).grid(row=4, column=0, sticky=tk.W, pady=(10, 5))
        
        format_frame = ttk.Frame(config_frame)
        format_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.format_vars = {
            'yolo': tk.BooleanVar(value=True),
            'coco': tk.BooleanVar(value=False),
            'cnn': tk.BooleanVar(value=False),
            'rnn': tk.BooleanVar(value=False)
        }
        
        ttk.Checkbutton(format_frame, text="YOLO Format", variable=self.format_vars['yolo']).grid(row=0, column=0, sticky=tk.W)
        ttk.Checkbutton(format_frame, text="COCO Format", variable=self.format_vars['coco']).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        ttk.Checkbutton(format_frame, text="CNN Format", variable=self.format_vars['cnn']).grid(row=1, column=0, sticky=tk.W)
        ttk.Checkbutton(format_frame, text="RNN Format", variable=self.format_vars['rnn']).grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        # Object mixing settings
        ttk.Label(config_frame, text="Object Mixing:", font=('Arial', 10, 'bold')).grid(row=6, column=0, sticky=tk.W, pady=(10, 5))
        
        mixing_frame = ttk.Frame(config_frame)
        mixing_frame.grid(row=7, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        mixing_frame.columnconfigure(1, weight=1)
        
        self.enable_mixing = tk.BooleanVar(value=True)
        ttk.Checkbutton(mixing_frame, text="Enable Object Mixing", variable=self.enable_mixing).grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        ttk.Label(mixing_frame, text="Max objects per image:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.max_objects = tk.IntVar(value=3)
        ttk.Spinbox(mixing_frame, from_=1, to=10, textvariable=self.max_objects, width=5).grid(row=1, column=1, sticky=tk.W, padx=(5, 0))
        
        ttk.Label(mixing_frame, text="Min object spacing:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.min_spacing = tk.IntVar(value=20)
        ttk.Spinbox(mixing_frame, from_=5, to=100, textvariable=self.min_spacing, width=5).grid(row=2, column=1, sticky=tk.W, padx=(5, 0))
        
        # Generation button
        ttk.Separator(config_frame, orient='horizontal').grid(row=8, column=0, sticky=(tk.W, tk.E), pady=10)
        
        self.generate_btn = ttk.Button(config_frame, text="Generate Dataset", command=self.start_generation)
        self.generate_btn.grid(row=9, column=0, pady=5)
        
        # Right panel - Progress and preview
        progress_frame = ttk.LabelFrame(main_frame, text="Generation Progress", padding="10")
        progress_frame.grid(row=1, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        progress_frame.columnconfigure(0, weight=1)
        progress_frame.rowconfigure(2, weight=1)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Status label
        self.status_var = tk.StringVar(value="Ready to generate dataset")
        status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        status_label.grid(row=1, column=0, pady=(0, 10))
        
        # Log area
        log_frame = ttk.Frame(progress_frame)
        log_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = tk.Text(log_frame, height=15, width=50, wrap=tk.WORD)
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Project summary
        self.create_project_summary(main_frame)
        
    def create_project_summary(self, parent):
        """Create a project summary display."""
        summary_frame = ttk.LabelFrame(parent, text="Project Summary", padding="10")
        summary_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10), pady=(10, 0))
        
        # Calculate statistics
        total_images = len(self.project_data['images'])
        total_annotations = sum(len(annotations) for annotations in self.project_data['annotations'].values())
        annotation_types = ', '.join(self.project_data.get('annotation_types', []))
        
        # Count enabled augmentations
        enabled_augmentations = []
        config = self.project_data.get('augmentation_config', {})
        for category_name, category in config.items():
            for aug_name, aug_config in category.items():
                if isinstance(aug_config, dict) and aug_config.get('enabled', False):
                    enabled_augmentations.append(aug_name.replace('_', ' ').title())
                    
        # Display summary
        summary_text = f"""
Input Images: {total_images}
Total Annotations: {total_annotations}
Annotation Types: {annotation_types}
Enabled Augmentations: {len(enabled_augmentations)}
• {chr(10).join(f'  - {aug}' for aug in enabled_augmentations[:10])}
{f'  ... and {len(enabled_augmentations) - 10} more' if len(enabled_augmentations) > 10 else ''}
        """.strip()
        
        summary_label = ttk.Label(summary_frame, text=summary_text, justify=tk.LEFT, font=('Arial', 9))
        summary_label.grid(row=0, column=0, sticky=(tk.W, tk.N))
        
    def browse_output_directory(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_path_var.set(directory)
            
    def log_message(self, message: str):
        """Add a message to the log."""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.update()
        
    def update_progress(self, value: float, status: str):
        """Update progress bar and status."""
        self.progress_var.set(value)
        self.status_var.set(status)
        self.parent.update()
        
    def start_generation(self):
        """Start the dataset generation process."""
        # Validate settings
        if not self.validate_settings():
            return
            
        # Disable generate button
        self.generate_btn.configure(state='disabled', text='Generating...')
        self.is_generating = True
        
        # Clear log
        self.log_text.delete(1.0, tk.END)
        
        # Start generation in a separate thread
        generation_thread = threading.Thread(target=self.generate_dataset)
        generation_thread.daemon = True
        generation_thread.start()
        
    def validate_settings(self):
        """Validate generation settings."""
        # Check output directory
        output_path = self.output_path_var.get().strip()
        if not output_path:
            messagebox.showerror("Error", "Please specify an output directory.")
            return False
            
        # Check if directory exists or can be created
        try:
            os.makedirs(output_path, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot create output directory: {str(e)}")
            return False
            
        # Check dataset size
        if self.dataset_size.get() < 1:
            messagebox.showerror("Error", "Dataset size must be at least 1.")
            return False
            
        # Check export formats
        if not any(var.get() for var in self.format_vars.values()):
            messagebox.showerror("Error", "Please select at least one export format.")
            return False
            
        return True
        
    def generate_dataset(self):
        """Generate the dataset (runs in separate thread)."""
        try:
            # Prepare generation configuration
            generation_config = {
                'output_path': self.output_path_var.get(),
                'dataset_size': self.dataset_size.get(),
                'export_formats': [fmt for fmt, var in self.format_vars.items() if var.get()],
                'enable_mixing': self.enable_mixing.get(),
                'max_objects_per_image': self.max_objects.get(),
                'min_object_spacing': self.min_spacing.get()
            }
            
            # Create dataset generator
            self.generator = DatasetGenerator(
                self.project_data,
                generation_config,
                progress_callback=self.update_progress,
                log_callback=self.log_message
            )
            
            # Start generation
            self.log_message("Starting dataset generation...")
            self.update_progress(0, "Initializing...")
            
            success = self.generator.generate()
            
            if success:
                self.log_message("Dataset generation completed successfully!")
                self.update_progress(100, "Complete")
                
                # Show completion dialog
                self.parent.after(0, self.on_generation_complete)
            else:
                self.log_message("Dataset generation failed!")
                self.update_progress(0, "Failed")
                self.parent.after(0, self.on_generation_failed)
                
        except Exception as e:
            self.log_message(f"Error during generation: {str(e)}")
            self.update_progress(0, "Error")
            self.parent.after(0, self.on_generation_failed)
        finally:
            self.is_generating = False
            self.parent.after(0, self.reset_generate_button)
            
    def on_generation_complete(self):
        """Handle successful generation completion."""
        result = messagebox.askyesno(
            "Success", 
            f"Dataset generated successfully!\n\nOutput directory: {self.output_path_var.get()}\n\nWould you like to open the output folder?",
            icon='info'
        )
        
        if result:
            try:
                os.startfile(self.output_path_var.get())  # Windows
            except:
                try:
                    os.system(f'open "{self.output_path_var.get()}"')  # macOS
                except:
                    os.system(f'xdg-open "{self.output_path_var.get()}"')  # Linux
                    
        self.callback()
        
    def on_generation_failed(self):
        """Handle generation failure."""
        messagebox.showerror("Error", "Dataset generation failed. Please check the log for details.")
        
    def reset_generate_button(self):
        """Reset the generate button state."""
        self.generate_btn.configure(state='normal', text='Generate Dataset')
