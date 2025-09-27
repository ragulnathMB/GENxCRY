"""
Augmentation Configuration Frame
Handles the configuration of image augmentation parameters.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Callable
import os

class AugmentationConfigFrame:
    """Frame for configuring image augmentation parameters."""
    
    def __init__(self, parent: tk.Widget, project_data: dict, callback: Callable):
        self.parent = parent
        self.project_data = project_data
        self.callback = callback
        
        # Initialize default configuration
        self.init_default_config()
        self.setup_ui()
        
    def init_default_config(self):
        """Initialize default augmentation configuration."""
        if 'augmentation_config' not in self.project_data:
            self.project_data['augmentation_config'] = {}
            
        config = self.project_data['augmentation_config']
        
        # Set defaults if not already set
        defaults = {
            'geometric': {
                'rotation': {'enabled': True, 'min_angle': -30, 'max_angle': 30},
                'flipping': {'enabled': True, 'horizontal': True, 'vertical': False},
                'shearing': {'enabled': False, 'shear_range': 0.2},
                'translation': {'enabled': True, 'tx_range': 0.1, 'ty_range': 0.1},
                'scaling': {'enabled': True, 'scale_range': (0.8, 1.2)}
            },
            'visual': {
                'brightness': {'enabled': True, 'range': (-0.2, 0.2)},
                'contrast': {'enabled': True, 'range': (0.8, 1.2)},
                'blur': {'enabled': True, 'kernel_size': (3, 7)},
                'shadows': {'enabled': False, 'intensity': 0.3},
                'lighting': {'enabled': False, 'intensity': 0.2},
                'glare': {'enabled': False, 'intensity': 0.1},
                'reflections': {'enabled': False, 'intensity': 0.2}
            },
            'noise': {
                'background_replacement': {'enabled': True, 'custom_backgrounds': []},
                'random_texture': {'enabled': True, 'intensity': 0.3},
                'salt_pepper': {'enabled': False, 'amount': 0.01},
                'gaussian': {'enabled': True, 'mean': 0, 'std': 0.01},
                'scribbled_background': {'enabled': True, 'density': 0.2},
                'cluttered_background': {'enabled': False, 'density': 0.1}
            }
        }
        
        for category, settings in defaults.items():
            if category not in config:
                config[category] = settings
                
    def setup_ui(self):
        """Setup the augmentation configuration interface."""
        # Main container
        main_frame = ttk.Frame(self.parent)
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Augmentation Configuration", style='Header.TLabel')
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Create notebook for categories
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create tabs
        self.create_geometric_tab(notebook)
        self.create_visual_tab(notebook)
        self.create_noise_tab(notebook)
        
        # Bottom frame with buttons
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(20, 0))
        
        ttk.Button(bottom_frame, text="Reset to Defaults", command=self.reset_to_defaults).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(bottom_frame, text="Preview Augmentations", command=self.preview_augmentations).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(bottom_frame, text="Proceed to Dataset Generation", command=self.proceed_to_generation).grid(row=0, column=2)
        
        bottom_frame.columnconfigure(2, weight=1)
        
    def create_geometric_tab(self, notebook):
        """Create the geometric transformations tab."""
        frame = ttk.Frame(notebook, padding="10")
        notebook.add(frame, text="Geometric Variations")
        
        # Create scrollable frame
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        config = self.project_data['augmentation_config']['geometric']
        
        # Rotation
        rotation_frame = ttk.LabelFrame(scrollable_frame, text="Rotation", padding="10")
        rotation_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        rotation_frame.columnconfigure(1, weight=1)
        
        self.rotation_var = tk.BooleanVar(value=config['rotation']['enabled'])
        ttk.Checkbutton(rotation_frame, text="Enable Rotation", variable=self.rotation_var).grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        ttk.Label(rotation_frame, text="Min Angle:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.rotation_min = tk.DoubleVar(value=config['rotation']['min_angle'])
        ttk.Scale(rotation_frame, from_=-180, to=0, variable=self.rotation_min, orient=tk.HORIZONTAL).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        
        ttk.Label(rotation_frame, text="Max Angle:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.rotation_max = tk.DoubleVar(value=config['rotation']['max_angle'])
        ttk.Scale(rotation_frame, from_=0, to=180, variable=self.rotation_max, orient=tk.HORIZONTAL).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        
        # Flipping
        flipping_frame = ttk.LabelFrame(scrollable_frame, text="Flipping", padding="10")
        flipping_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.flipping_var = tk.BooleanVar(value=config['flipping']['enabled'])
        ttk.Checkbutton(flipping_frame, text="Enable Flipping", variable=self.flipping_var).grid(row=0, column=0, sticky=tk.W)
        
        self.flip_horizontal = tk.BooleanVar(value=config['flipping']['horizontal'])
        ttk.Checkbutton(flipping_frame, text="Horizontal Flip", variable=self.flip_horizontal).grid(row=1, column=0, sticky=tk.W)
        
        self.flip_vertical = tk.BooleanVar(value=config['flipping']['vertical'])
        ttk.Checkbutton(flipping_frame, text="Vertical Flip", variable=self.flip_vertical).grid(row=1, column=1, sticky=tk.W)
        
        # Shearing
        shearing_frame = ttk.LabelFrame(scrollable_frame, text="Shearing", padding="10")
        shearing_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        shearing_frame.columnconfigure(1, weight=1)
        
        self.shearing_var = tk.BooleanVar(value=config['shearing']['enabled'])
        ttk.Checkbutton(shearing_frame, text="Enable Shearing", variable=self.shearing_var).grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        ttk.Label(shearing_frame, text="Shear Range:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.shear_range = tk.DoubleVar(value=config['shearing']['shear_range'])
        ttk.Scale(shearing_frame, from_=0, to=1, variable=self.shear_range, orient=tk.HORIZONTAL).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        
        # Translation
        translation_frame = ttk.LabelFrame(scrollable_frame, text="Translation", padding="10")
        translation_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        translation_frame.columnconfigure(1, weight=1)
        
        self.translation_var = tk.BooleanVar(value=config['translation']['enabled'])
        ttk.Checkbutton(translation_frame, text="Enable Translation", variable=self.translation_var).grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        ttk.Label(translation_frame, text="X Range:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.tx_range = tk.DoubleVar(value=config['translation']['tx_range'])
        ttk.Scale(translation_frame, from_=0, to=0.5, variable=self.tx_range, orient=tk.HORIZONTAL).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        
        ttk.Label(translation_frame, text="Y Range:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.ty_range = tk.DoubleVar(value=config['translation']['ty_range'])
        ttk.Scale(translation_frame, from_=0, to=0.5, variable=self.ty_range, orient=tk.HORIZONTAL).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        
        # Scaling
        scaling_frame = ttk.LabelFrame(scrollable_frame, text="Scaling", padding="10")
        scaling_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=5)
        scaling_frame.columnconfigure(1, weight=1)
        
        self.scaling_var = tk.BooleanVar(value=config['scaling']['enabled'])
        ttk.Checkbutton(scaling_frame, text="Enable Scaling", variable=self.scaling_var).grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        ttk.Label(scaling_frame, text="Min Scale:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.scale_min = tk.DoubleVar(value=config['scaling']['scale_range'][0])
        ttk.Scale(scaling_frame, from_=0.1, to=1.0, variable=self.scale_min, orient=tk.HORIZONTAL).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        
        ttk.Label(scaling_frame, text="Max Scale:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.scale_max = tk.DoubleVar(value=config['scaling']['scale_range'][1])
        ttk.Scale(scaling_frame, from_=1.0, to=2.0, variable=self.scale_max, orient=tk.HORIZONTAL).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        
        scrollable_frame.columnconfigure(0, weight=1)
        
    def create_visual_tab(self, notebook):
        """Create the visual effects tab."""
        frame = ttk.Frame(notebook, padding="10")
        notebook.add(frame, text="Visual Effects")
        
        # Create scrollable frame
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        config = self.project_data['augmentation_config']['visual']
        
        # Brightness
        brightness_frame = ttk.LabelFrame(scrollable_frame, text="Brightness", padding="10")
        brightness_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        brightness_frame.columnconfigure(1, weight=1)
        
        self.brightness_var = tk.BooleanVar(value=config['brightness']['enabled'])
        ttk.Checkbutton(brightness_frame, text="Enable Brightness Adjustment", variable=self.brightness_var).grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        ttk.Label(brightness_frame, text="Range:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.brightness_range = tk.DoubleVar(value=config['brightness']['range'][1])
        ttk.Scale(brightness_frame, from_=0, to=0.5, variable=self.brightness_range, orient=tk.HORIZONTAL).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        
        # Contrast
        contrast_frame = ttk.LabelFrame(scrollable_frame, text="Contrast", padding="10")
        contrast_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        contrast_frame.columnconfigure(1, weight=1)
        
        self.contrast_var = tk.BooleanVar(value=config['contrast']['enabled'])
        ttk.Checkbutton(contrast_frame, text="Enable Contrast Adjustment", variable=self.contrast_var).grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        ttk.Label(contrast_frame, text="Range:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.contrast_range = tk.DoubleVar(value=config['contrast']['range'][1])
        ttk.Scale(contrast_frame, from_=0.5, to=2.0, variable=self.contrast_range, orient=tk.HORIZONTAL).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        
        # Blur
        blur_frame = ttk.LabelFrame(scrollable_frame, text="Blur", padding="10")
        blur_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        blur_frame.columnconfigure(1, weight=1)
        
        self.blur_var = tk.BooleanVar(value=config['blur']['enabled'])
        ttk.Checkbutton(blur_frame, text="Enable Blur", variable=self.blur_var).grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        ttk.Label(blur_frame, text="Max Kernel Size:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.blur_kernel = tk.IntVar(value=config['blur']['kernel_size'][1])
        ttk.Scale(blur_frame, from_=3, to=15, variable=self.blur_kernel, orient=tk.HORIZONTAL).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        
        # Advanced effects
        effects_frame = ttk.LabelFrame(scrollable_frame, text="Advanced Effects", padding="10")
        effects_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.shadows_var = tk.BooleanVar(value=config['shadows']['enabled'])
        ttk.Checkbutton(effects_frame, text="Shadows", variable=self.shadows_var).grid(row=0, column=0, sticky=tk.W)
        
        self.lighting_var = tk.BooleanVar(value=config['lighting']['enabled'])
        ttk.Checkbutton(effects_frame, text="Lighting Changes", variable=self.lighting_var).grid(row=0, column=1, sticky=tk.W)
        
        self.glare_var = tk.BooleanVar(value=config['glare']['enabled'])
        ttk.Checkbutton(effects_frame, text="Glare", variable=self.glare_var).grid(row=1, column=0, sticky=tk.W)
        
        self.reflections_var = tk.BooleanVar(value=config['reflections']['enabled'])
        ttk.Checkbutton(effects_frame, text="Reflections", variable=self.reflections_var).grid(row=1, column=1, sticky=tk.W)
        
        scrollable_frame.columnconfigure(0, weight=1)
        
    def create_noise_tab(self, notebook):
        """Create the noise and background tab."""
        frame = ttk.Frame(notebook, padding="10")
        notebook.add(frame, text="Background & Noise")
        
        # Create scrollable frame
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        config = self.project_data['augmentation_config']['noise']
        
        # Background replacement
        bg_frame = ttk.LabelFrame(scrollable_frame, text="Background Replacement", padding="10")
        bg_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        bg_frame.columnconfigure(1, weight=1)
        
        self.bg_replacement_var = tk.BooleanVar(value=config['background_replacement']['enabled'])
        ttk.Checkbutton(bg_frame, text="Enable Background Replacement", variable=self.bg_replacement_var).grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        ttk.Button(bg_frame, text="Add Custom Backgrounds", command=self.add_custom_backgrounds).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.bg_count_label = ttk.Label(bg_frame, text=f"Custom backgrounds: {len(config['background_replacement']['custom_backgrounds'])}")
        self.bg_count_label.grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        # Texture and noise
        texture_frame = ttk.LabelFrame(scrollable_frame, text="Texture & Noise", padding="10")
        texture_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        texture_frame.columnconfigure(1, weight=1)
        
        self.random_texture_var = tk.BooleanVar(value=config['random_texture']['enabled'])
        ttk.Checkbutton(texture_frame, text="Random Texture", variable=self.random_texture_var).grid(row=0, column=0, sticky=tk.W)
        
        self.scribbled_bg_var = tk.BooleanVar(value=config['scribbled_background']['enabled'])
        ttk.Checkbutton(texture_frame, text="Scribbled Background", variable=self.scribbled_bg_var).grid(row=0, column=1, sticky=tk.W)
        
        self.cluttered_bg_var = tk.BooleanVar(value=config['cluttered_background']['enabled'])
        ttk.Checkbutton(texture_frame, text="Cluttered Background", variable=self.cluttered_bg_var).grid(row=1, column=0, sticky=tk.W)
        
        # Noise types
        noise_frame = ttk.LabelFrame(scrollable_frame, text="Noise Types", padding="10")
        noise_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        noise_frame.columnconfigure(1, weight=1)
        
        self.salt_pepper_var = tk.BooleanVar(value=config['salt_pepper']['enabled'])
        ttk.Checkbutton(noise_frame, text="Salt & Pepper Noise", variable=self.salt_pepper_var).grid(row=0, column=0, sticky=tk.W)
        
        self.gaussian_var = tk.BooleanVar(value=config['gaussian']['enabled'])
        ttk.Checkbutton(noise_frame, text="Gaussian Noise", variable=self.gaussian_var).grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(noise_frame, text="Gaussian Std:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.gaussian_std = tk.DoubleVar(value=config['gaussian']['std'])
        ttk.Scale(noise_frame, from_=0, to=0.1, variable=self.gaussian_std, orient=tk.HORIZONTAL).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        
        scrollable_frame.columnconfigure(0, weight=1)
        
    def add_custom_backgrounds(self):
        """Add custom background images."""
        filetypes = [
            ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.gif"),
            ("All files", "*.*")
        ]
        
        files = filedialog.askopenfilenames(
            title="Select Background Images",
            filetypes=filetypes
        )
        
        if files:
            config = self.project_data['augmentation_config']['noise']['background_replacement']
            for file in files:
                if file not in config['custom_backgrounds']:
                    config['custom_backgrounds'].append(file)
                    
            self.bg_count_label.configure(text=f"Custom backgrounds: {len(config['custom_backgrounds'])}")
            messagebox.showinfo("Success", f"Added {len(files)} background image(s).")
            
    def reset_to_defaults(self):
        """Reset all settings to default values."""
        result = messagebox.askyesno("Confirm", "Reset all augmentation settings to defaults?")
        if result:
            # Clear current config and reinitialize
            self.project_data['augmentation_config'] = {}
            self.init_default_config()
            
            # Recreate the UI to reflect changes
            # This is a simple approach - in a more complex app, you'd update individual controls
            messagebox.showinfo("Reset", "Settings have been reset to defaults. Please restart the configuration.")
            
    def preview_augmentations(self):
        """Preview augmentations on sample images."""
        # This would open a preview window showing sample augmented images
        messagebox.showinfo("Preview", "Augmentation preview feature will be implemented in the next version.")
        
    def save_current_config(self):
        """Save the current configuration from UI controls."""
        config = self.project_data['augmentation_config']
        
        # Geometric transformations
        config['geometric']['rotation']['enabled'] = self.rotation_var.get()
        config['geometric']['rotation']['min_angle'] = self.rotation_min.get()
        config['geometric']['rotation']['max_angle'] = self.rotation_max.get()
        
        config['geometric']['flipping']['enabled'] = self.flipping_var.get()
        config['geometric']['flipping']['horizontal'] = self.flip_horizontal.get()
        config['geometric']['flipping']['vertical'] = self.flip_vertical.get()
        
        config['geometric']['shearing']['enabled'] = self.shearing_var.get()
        config['geometric']['shearing']['shear_range'] = self.shear_range.get()
        
        config['geometric']['translation']['enabled'] = self.translation_var.get()
        config['geometric']['translation']['tx_range'] = self.tx_range.get()
        config['geometric']['translation']['ty_range'] = self.ty_range.get()
        
        config['geometric']['scaling']['enabled'] = self.scaling_var.get()
        config['geometric']['scaling']['scale_range'] = (self.scale_min.get(), self.scale_max.get())
        
        # Visual effects
        config['visual']['brightness']['enabled'] = self.brightness_var.get()
        config['visual']['brightness']['range'] = (-self.brightness_range.get(), self.brightness_range.get())
        
        config['visual']['contrast']['enabled'] = self.contrast_var.get()
        config['visual']['contrast']['range'] = (1/self.contrast_range.get(), self.contrast_range.get())
        
        config['visual']['blur']['enabled'] = self.blur_var.get()
        config['visual']['blur']['kernel_size'] = (3, self.blur_kernel.get())
        
        config['visual']['shadows']['enabled'] = self.shadows_var.get()
        config['visual']['lighting']['enabled'] = self.lighting_var.get()
        config['visual']['glare']['enabled'] = self.glare_var.get()
        config['visual']['reflections']['enabled'] = self.reflections_var.get()
        
        # Noise and background
        config['noise']['background_replacement']['enabled'] = self.bg_replacement_var.get()
        config['noise']['random_texture']['enabled'] = self.random_texture_var.get()
        config['noise']['salt_pepper']['enabled'] = self.salt_pepper_var.get()
        config['noise']['gaussian']['enabled'] = self.gaussian_var.get()
        config['noise']['gaussian']['std'] = self.gaussian_std.get()
        config['noise']['scribbled_background']['enabled'] = self.scribbled_bg_var.get()
        config['noise']['cluttered_background']['enabled'] = self.cluttered_bg_var.get()
        
    def proceed_to_generation(self):
        """Proceed to the dataset generation stage."""
        self.save_current_config()
        
        # Check if at least some augmentations are enabled
        config = self.project_data['augmentation_config']
        has_augmentations = False
        
        for category in config.values():
            for setting in category.values():
                if isinstance(setting, dict) and setting.get('enabled', False):
                    has_augmentations = True
                    break
            if has_augmentations:
                break
                
        if not has_augmentations:
            result = messagebox.askyesno("Warning", "No augmentations are enabled. Continue anyway?")
            if not result:
                return
                
        self.callback()
