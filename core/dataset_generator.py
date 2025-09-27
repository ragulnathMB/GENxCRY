"""
Dataset Generator
Core functionality for generating augmented datasets with object mixing.
"""

import os
import json
import random
import math
from typing import Dict, List, Tuple, Callable, Optional
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import xml.etree.ElementTree as ET
from datetime import datetime

from core.augmentation_engine import AugmentationEngine
from core.export_formats import AnnotationExporter

class DatasetGenerator:
    """Main dataset generator class."""
    
    def __init__(self, project_data: dict, generation_config: dict, 
                 progress_callback: Callable = None, log_callback: Callable = None):
        self.project_data = project_data
        self.config = generation_config
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        
        # Initialize paths
        self.output_path = generation_config['output_path']
        self.images_path = os.path.join(self.output_path, 'images')
        self.annotations_path = os.path.join(self.output_path, 'annotations')
        
        # Create output directories
        os.makedirs(self.images_path, exist_ok=True)
        os.makedirs(self.annotations_path, exist_ok=True)
        
        # Load and prepare source objects
        self.source_objects = []
        self.background_images = []
        self.class_names = set()
        
        # Initialize engines
        self.augmentation_engine = None
        self.annotation_exporter = None
        
        self.prepare_source_data()
        
    def log(self, message: str):
        """Log a message."""
        if self.log_callback:
            self.log_callback(message)
        print(message)
        
    def update_progress(self, progress: float, status: str):
        """Update progress."""
        if self.progress_callback:
            self.progress_callback(progress, status)
            
    def prepare_source_data(self):
        """Prepare source objects and backgrounds from annotations."""
        self.log("Preparing source data...")
        
        for image_path, annotations in self.project_data['annotations'].items():
            if not annotations:
                continue
                
            try:
                # Load source image
                source_image = Image.open(image_path)
                
                for annotation in annotations:
                    if annotation.get('label'):  # Process both bbox and segment annotations
                        try:
                            if annotation['type'] == 'bbox':
                                # Extract object from bounding box
                                x1, y1, x2, y2 = annotation['coordinates']
                                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                                
                                # Validate bounding box coordinates
                                if x1 >= x2 or y1 >= y2:
                                    self.log(f"Invalid bounding box coordinates in {image_path}: ({x1}, {y1}, {x2}, {y2})")
                                    continue
                                    
                                # Ensure coordinates are within image bounds
                                img_width, img_height = source_image.size
                                x1 = max(0, min(x1, img_width - 1))
                                y1 = max(0, min(y1, img_height - 1))
                                x2 = max(x1 + 1, min(x2, img_width))
                                y2 = max(y1 + 1, min(y2, img_height))
                                
                                # Crop object
                                object_image = source_image.crop((x1, y1, x2, y2))
                                
                                # Ensure the cropped image has valid dimensions
                                if object_image.size[0] == 0 or object_image.size[1] == 0:
                                    self.log(f"Invalid object size after cropping in {image_path}")
                                    continue
                                
                                # Create mask (simple rectangular mask for now)
                                mask = Image.new('L', object_image.size, 255)
                                
                                # Store object data
                                object_data = {
                                    'image': object_image,
                                    'mask': mask,
                                    'label': annotation['label'],
                                    'original_size': (x2 - x1, y2 - y1),
                                    'source_path': image_path,
                                    'annotation_type': 'bbox'
                                }
                                
                                self.source_objects.append(object_data)
                                self.class_names.add(annotation['label'])
                                
                            elif annotation['type'] == 'segment':
                                # Extract object from segmentation
                                points = annotation['coordinates']
                                if len(points) < 3:
                                    self.log(f"Invalid segmentation with less than 3 points in {image_path}")
                                    continue
                                
                                # Calculate bounding box from segmentation points
                                x_coords = [int(p[0]) for p in points]
                                y_coords = [int(p[1]) for p in points]
                                x1, y1 = min(x_coords), min(y_coords)
                                x2, y2 = max(x_coords), max(y_coords)
                                
                                # Ensure coordinates are within image bounds
                                img_width, img_height = source_image.size
                                x1 = max(0, min(x1, img_width - 1))
                                y1 = max(0, min(y1, img_height - 1))
                                x2 = max(x1 + 1, min(x2, img_width))
                                y2 = max(y1 + 1, min(y2, img_height))
                                
                                # Crop object using bounding box
                                object_image = source_image.crop((x1, y1, x2, y2))
                                
                                if object_image.size[0] == 0 or object_image.size[1] == 0:
                                    self.log(f"Invalid object size after cropping segmentation in {image_path}")
                                    continue
                                
                                # Create precise mask from segmentation points
                                mask = self.create_segmentation_mask(points, (x1, y1), object_image.size)
                                
                                # Store object data
                                object_data = {
                                    'image': object_image,
                                    'mask': mask,
                                    'label': annotation['label'],
                                    'original_size': (x2 - x1, y2 - y1),
                                    'source_path': image_path,
                                    'annotation_type': 'segment',
                                    'segmentation_points': points
                                }
                                
                                self.source_objects.append(object_data)
                                self.class_names.add(annotation['label'])
                                
                        except Exception as e:
                            self.log(f"Error processing {annotation['type']} annotation in {image_path}: {str(e)}")
                            continue
                        
            except Exception as e:
                self.log(f"Error processing {image_path}: {str(e)}")
                
        # Load background images
        bg_config = self.project_data['augmentation_config']['noise']['background_replacement']
        if bg_config['enabled'] and bg_config['custom_backgrounds']:
            for bg_path in bg_config['custom_backgrounds']:
                try:
                    bg_image = Image.open(bg_path)
                    self.background_images.append(bg_image)
                except Exception as e:
                    self.log(f"Error loading background {bg_path}: {str(e)}")
                    
        self.log(f"Prepared {len(self.source_objects)} objects from {len(self.class_names)} classes")
        
        # Initialize engines after data preparation
        self.augmentation_engine = AugmentationEngine(self.project_data['augmentation_config'])
        self.annotation_exporter = AnnotationExporter(self.output_path, self.class_names)
        
    def generate(self) -> bool:
        """Generate the complete dataset."""
        try:
            dataset_size = self.config['dataset_size']
            
            # Generate images
            for i in range(dataset_size):
                progress = (i / dataset_size) * 90  # Reserve 10% for export
                self.update_progress(progress, f"Generating image {i+1}/{dataset_size}")
                
                success = self.generate_single_image(i)
                if not success:
                    self.log(f"Failed to generate image {i+1}")
                    
            # Export in different formats
            self.update_progress(90, "Exporting annotations...")
            self.annotation_exporter.export_consolidated_annotations(self.config['export_formats'])
            
            # Create dataset info
            self.create_dataset_info()
            
            self.update_progress(100, "Complete")
            return True
            
        except Exception as e:
            self.log(f"Generation failed: {str(e)}")
            return False
            
    def generate_single_image(self, image_index: int) -> bool:
        """Generate a single augmented image."""
        try:
            # Initial canvas size
            initial_canvas_size = (640, 640)
            
            # Create initial background
            background = self.augmentation_engine.create_background(initial_canvas_size, self.background_images)
            
            # Generate objects for this image
            objects_data = []
            
            if self.config['enable_mixing'] and len(self.source_objects) > 1:
                # Mix multiple objects
                num_objects = random.randint(1, min(self.config['max_objects_per_image'], len(self.source_objects)))
                selected_objects = random.sample(self.source_objects, num_objects)
                
                for obj_data in selected_objects:
                    augmented_obj = self.augmentation_engine.augment_object(obj_data)
                    position = self.augmentation_engine.find_valid_position(
                        background, augmented_obj, objects_data, self.config['min_object_spacing']
                    )
                    
                    if position:
                        objects_data.append({
                            'object': augmented_obj,
                            'position': position,
                            'label': obj_data['label']
                        })
            else:
                # Single object
                if self.source_objects:
                    obj_data = random.choice(self.source_objects)
                    augmented_obj = self.augmentation_engine.augment_object(obj_data)
                    
                    # Center the object
                    obj_width, obj_height = augmented_obj['image'].size
                    position = (
                        (initial_canvas_size[0] - obj_width) // 2,
                        (initial_canvas_size[1] - obj_height) // 2
                    )
                    
                    objects_data.append({
                        'object': augmented_obj,
                        'position': position,
                        'label': obj_data['label']
                    })
            
            # Calculate required canvas size to fit all objects
            final_canvas_size = self.calculate_required_canvas_size(objects_data, initial_canvas_size)
            
            # Resize background if needed
            if final_canvas_size != initial_canvas_size:
                background = self.resize_background(background, final_canvas_size)
                    
            # Composite final image
            final_image = self.augmentation_engine.composite_image(background, objects_data)
            
            # Apply final augmentations
            final_image = self.augmentation_engine.apply_final_augmentations(final_image)
            
            # Save image
            image_filename = f"image_{image_index:06d}.jpg"
            image_path = os.path.join(self.images_path, image_filename)
            final_image.save(image_path, 'JPEG', quality=95)
            
            # Save annotation data with final canvas size
            self.annotation_exporter.save_annotations(
                image_index, image_filename, final_canvas_size, objects_data, self.config['export_formats']
            )
            
            return True
            
        except Exception as e:
            self.log(f"Error generating image {image_index}: {str(e)}")
            return False
    
    def calculate_required_canvas_size(self, objects_data: List[dict], initial_size: Tuple[int, int]) -> Tuple[int, int]:
        """Calculate the minimum canvas size required to fit all objects."""
        if not objects_data:
            return initial_size
        
        # Find the bounding box that contains all objects
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        for obj_info in objects_data:
            obj_image = obj_info['object']['image']
            position = obj_info['position']
            
            obj_width, obj_height = obj_image.size
            x, y = position
            
            # Update bounding box
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x + obj_width)
            max_y = max(max_y, y + obj_height)
        
        # Add padding around objects
        padding = 20
        
        # Calculate offsets needed to bring negative coordinates to zero
        x_offset = max(0, -min_x + padding)
        y_offset = max(0, -min_y + padding)
        
        # Adjust object positions if we need to shift them due to negative coordinates
        if x_offset > 0 or y_offset > 0:
            for obj_info in objects_data:
                current_pos = obj_info['position']
                obj_info['position'] = (current_pos[0] + x_offset, current_pos[1] + y_offset)
            
            # Update bounding box after position adjustment
            max_x += x_offset
            max_y += y_offset
        
        # Calculate required canvas size with padding
        required_width = max(initial_size[0], int(max_x + padding))
        required_height = max(initial_size[1], int(max_y + padding))
        
        # Apply reasonable size limits to prevent excessive canvas sizes
        max_canvas_size = 2048  # Maximum canvas dimension
        if required_width > max_canvas_size or required_height > max_canvas_size:
            # If canvas would be too large, scale down proportionally
            scale_factor = min(max_canvas_size / required_width, max_canvas_size / required_height)
            
            # Scale down canvas size
            required_width = int(required_width * scale_factor)
            required_height = int(required_height * scale_factor)
            
            # Scale down object positions and sizes proportionally
            for obj_info in objects_data:
                current_pos = obj_info['position']
                obj_info['position'] = (int(current_pos[0] * scale_factor), int(current_pos[1] * scale_factor))
                
                # Scale object image if needed
                obj_image = obj_info['object']['image']
                new_size = (int(obj_image.width * scale_factor), int(obj_image.height * scale_factor))
                if new_size[0] > 0 and new_size[1] > 0:
                    obj_info['object']['image'] = obj_image.resize(new_size, Image.Resampling.LANCZOS)
                    if obj_info['object']['mask']:
                        obj_info['object']['mask'] = obj_info['object']['mask'].resize(new_size, Image.Resampling.LANCZOS)
        
        return (required_width, required_height)
    
    def resize_background(self, background: Image.Image, new_size: Tuple[int, int]) -> Image.Image:
        """Resize background to accommodate all objects."""
        current_size = background.size
        
        if new_size == current_size:
            return background
        
        # Create a new background with the required size
        if new_size[0] > current_size[0] or new_size[1] > current_size[1]:
            # Create extended background
            extended_bg = self.augmentation_engine.create_background(new_size, self.background_images)
            
            # Optionally, we could paste the original background in the center
            # For now, we'll create a completely new background
            return extended_bg
        else:
            # If somehow we need a smaller background, just resize
            return background.resize(new_size, Image.Resampling.LANCZOS)
    
    def create_segmentation_mask(self, points: List[Tuple[float, float]], offset: Tuple[int, int], size: Tuple[int, int]) -> Image.Image:
        """Create a precise mask from segmentation points."""
        mask = Image.new('L', size, 0)  # Start with black mask
        draw = ImageDraw.Draw(mask)
        
        # Adjust points relative to the cropped area
        adjusted_points = []
        for x, y in points:
            adj_x = int(x - offset[0])
            adj_y = int(y - offset[1])
            # Ensure points are within mask bounds
            adj_x = max(0, min(adj_x, size[0] - 1))
            adj_y = max(0, min(adj_y, size[1] - 1))
            adjusted_points.append((adj_x, adj_y))
        
        # Draw filled polygon
        if len(adjusted_points) >= 3:
            draw.polygon(adjusted_points, fill=255)
        
        return mask
            
    def create_dataset_info(self):
        """Create dataset information file."""
        info = {
            'dataset_name': 'GENxCRY Generated Dataset',
            'created_by': 'RN Software',
            'creation_date': datetime.now().isoformat(),
            'total_images': self.config['dataset_size'],
            'classes': sorted(list(self.class_names)),
            'num_classes': len(self.class_names),
            'export_formats': self.config['export_formats'],
            'augmentation_config': self.project_data['augmentation_config'],
            'generation_config': self.config
        }
        
        info_path = os.path.join(self.output_path, 'dataset_info.json')
        with open(info_path, 'w') as f:
            json.dump(info, f, indent=2)
            
        self.log(f"Dataset info saved to {info_path}")
