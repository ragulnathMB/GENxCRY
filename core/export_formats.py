"""
Export Formats
Handles exporting annotations in different formats (YOLO, COCO, CNN, RNN).
"""

import os
import json
from typing import Dict, List, Tuple
from datetime import datetime

class AnnotationExporter:
    """Handles exporting annotations in various formats."""
    
    def __init__(self, output_path: str, class_names: set):
        self.output_path = output_path
        self.annotations_path = os.path.join(output_path, 'annotations')
        self.class_names = sorted(list(class_names))
        self.class_map = {name: idx for idx, name in enumerate(self.class_names)}
        
    def save_annotations(self, image_index: int, image_filename: str, 
                        canvas_size: Tuple[int, int], objects_data: List[dict], 
                        export_formats: List[str]):
        """Save annotations in specified formats."""
        annotations = []
        
        for obj_info in objects_data:
            if 'position' in obj_info:  # Generated object from dataset generator
                x, y = obj_info['position']
                obj_width, obj_height = obj_info['object']['image'].size
                
                annotation = {
                    'type': 'bbox',
                    'bbox': [x, y, x + obj_width, y + obj_height],
                    'label': obj_info['label'],
                    'area': obj_width * obj_height
                }
                annotations.append(annotation)
            else:  # Direct annotation from annotation window
                annotation = {
                    'type': obj_info.get('type', 'bbox'),
                    'label': obj_info.get('label', ''),
                }
                
                if obj_info['type'] == 'bbox':
                    x1, y1, x2, y2 = obj_info['coordinates']
                    annotation['bbox'] = [x1, y1, x2, y2]
                    annotation['area'] = (x2 - x1) * (y2 - y1)
                elif obj_info['type'] == 'segment':
                    annotation['segmentation'] = obj_info['coordinates']
                    # Calculate bounding box from segmentation
                    points = obj_info['coordinates']
                    x_coords = [p[0] for p in points]
                    y_coords = [p[1] for p in points]
                    x1, y1 = min(x_coords), min(y_coords)
                    x2, y2 = max(x_coords), max(y_coords)
                    annotation['bbox'] = [x1, y1, x2, y2]
                    annotation['area'] = (x2 - x1) * (y2 - y1)
                    
                annotations.append(annotation)
            
        # Save in different formats
        for format_name in export_formats:
            if format_name == 'yolo':
                self.save_yolo_annotation(image_index, canvas_size, annotations)
            elif format_name == 'coco':
                self.save_coco_annotation(image_index, image_filename, canvas_size, annotations)
            elif format_name == 'cnn':
                self.save_cnn_annotation(image_index, image_filename, annotations)
            elif format_name == 'rnn':
                self.save_rnn_annotation(image_index, image_filename, annotations)
                
    def save_yolo_annotation(self, image_index: int, canvas_size: Tuple[int, int], annotations: List[dict]):
        """Save annotation in YOLO format."""
        filename = f"image_{image_index:06d}.txt"
        filepath = os.path.join(self.annotations_path, 'yolo', filename)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            for ann in annotations:
                if ann['label'] not in self.class_map:
                    continue  # Skip annotations without valid labels
                    
                class_id = self.class_map[ann['label']]
                
                if ann.get('type') == 'segment' and 'segmentation' in ann:
                    # YOLO segmentation format: class_id x1 y1 x2 y2 x3 y3 ...
                    points = ann['segmentation']
                    normalized_points = []
                    for x, y in points:
                        # Clamp coordinates to canvas bounds before normalizing
                        x = max(0, min(x, canvas_size[0]))
                        y = max(0, min(y, canvas_size[1]))
                        
                        # Normalize and clamp to [0, 1] range
                        norm_x = max(0.0, min(1.0, x / canvas_size[0]))
                        norm_y = max(0.0, min(1.0, y / canvas_size[1]))
                        normalized_points.extend([norm_x, norm_y])
                    
                    # Only write if we have valid points
                    if len(normalized_points) >= 6:  # At least 3 points (x,y pairs)
                        points_str = ' '.join(f"{p:.6f}" for p in normalized_points)
                        f.write(f"{class_id} {points_str}\n")
                else:
                    # YOLO bounding box format
                    x1, y1, x2, y2 = ann['bbox']
                    
                    # Ensure coordinates are within canvas bounds
                    x1 = max(0, min(x1, canvas_size[0]))
                    y1 = max(0, min(y1, canvas_size[1]))
                    x2 = max(0, min(x2, canvas_size[0]))
                    y2 = max(0, min(y2, canvas_size[1]))
                    
                    # Ensure x2 > x1 and y2 > y1
                    if x2 <= x1:
                        x2 = x1 + 1
                    if y2 <= y1:
                        y2 = y1 + 1
                    
                    # Convert to YOLO format (normalized center coordinates and dimensions)
                    center_x = (x1 + x2) / 2 / canvas_size[0]
                    center_y = (y1 + y2) / 2 / canvas_size[1]
                    width = (x2 - x1) / canvas_size[0]
                    height = (y2 - y1) / canvas_size[1]
                    
                    # Clamp normalized values to [0, 1] range
                    center_x = max(0.0, min(1.0, center_x))
                    center_y = max(0.0, min(1.0, center_y))
                    width = max(0.0, min(1.0, width))
                    height = max(0.0, min(1.0, height))
                    
                    # Skip invalid annotations (too small or zero area)
                    if width < 0.001 or height < 0.001:
                        continue
                    
                    f.write(f"{class_id} {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}\n")
                
    def save_coco_annotation(self, image_index: int, image_filename: str, 
                           canvas_size: Tuple[int, int], annotations: List[dict]):
        """Save annotation in COCO format."""
        filename = f"image_{image_index:06d}.json"
        filepath = os.path.join(self.annotations_path, 'coco', filename)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        coco_data = {
            'image': {
                'id': image_index,
                'file_name': image_filename,
                'width': canvas_size[0],
                'height': canvas_size[1]
            },
            'annotations': []
        }
        
        for ann_id, ann in enumerate(annotations):
            if ann['label'] not in self.class_map:
                continue  # Skip annotations without valid labels
                
            x1, y1, x2, y2 = ann['bbox']
            
            coco_ann = {
                'id': ann_id,
                'image_id': image_index,
                'category_id': self.class_map[ann['label']],
                'bbox': [x1, y1, x2 - x1, y2 - y1],  # COCO format: [x, y, width, height]
                'area': ann['area'],
                'iscrowd': 0
            }
            
            # Add segmentation if available
            if ann.get('type') == 'segment' and 'segmentation' in ann:
                # COCO segmentation format: [[x1, y1, x2, y2, ...]]
                points = ann['segmentation']
                flattened_points = []
                for x, y in points:
                    flattened_points.extend([x, y])
                coco_ann['segmentation'] = [flattened_points]
            
            coco_data['annotations'].append(coco_ann)
            
        with open(filepath, 'w') as f:
            json.dump(coco_data, f, indent=2)
            
    def save_cnn_annotation(self, image_index: int, image_filename: str, annotations: List[dict]):
        """Save annotation in CNN format (simple classification)."""
        filename = f"image_{image_index:06d}.json"
        filepath = os.path.join(self.annotations_path, 'cnn', filename)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # For CNN, we typically just need the class labels
        labels = [ann['label'] for ann in annotations]
        
        cnn_data = {
            'image': image_filename,
            'labels': labels,
            'primary_label': labels[0] if labels else 'unknown'
        }
        
        with open(filepath, 'w') as f:
            json.dump(cnn_data, f, indent=2)
            
    def save_rnn_annotation(self, image_index: int, image_filename: str, annotations: List[dict]):
        """Save annotation in RNN format (sequence data)."""
        filename = f"image_{image_index:06d}.json"
        filepath = os.path.join(self.annotations_path, 'rnn', filename)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # For RNN, create a sequence of object descriptions
        sequence = []
        for ann in annotations:
            x1, y1, x2, y2 = ann['bbox']
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            
            # Create a description sequence
            description = {
                'label': ann['label'],
                'position': [center_x, center_y],
                'size': [x2 - x1, y2 - y1],
                'timestamp': len(sequence)
            }
            sequence.append(description)
            
        rnn_data = {
            'image': image_filename,
            'sequence': sequence,
            'sequence_length': len(sequence)
        }
        
        with open(filepath, 'w') as f:
            json.dump(rnn_data, f, indent=2)
            
    def export_consolidated_annotations(self, export_formats: List[str]):
        """Export consolidated annotation files."""
        for format_name in export_formats:
            if format_name == 'yolo':
                self.export_yolo_config()
            elif format_name == 'coco':
                self.export_coco_dataset()
                
    def export_yolo_config(self):
        """Export YOLO dataset configuration."""
        config_path = os.path.join(self.annotations_path, 'yolo', 'dataset.yaml')
        
        config = {
            'path': os.path.abspath(self.output_path),
            'train': 'images',
            'val': 'images',  # For simplicity, using same folder
            'nc': len(self.class_names),
            'names': self.class_names
        }
        
        # Write YAML manually to avoid dependency
        with open(config_path, 'w') as f:
            f.write(f"path: {config['path']}\n")
            f.write(f"train: {config['train']}\n")
            f.write(f"val: {config['val']}\n")
            f.write(f"nc: {config['nc']}\n")
            f.write("names:\n")
            for name in config['names']:
                f.write(f"  - {name}\n")
                
        # Save class names
        classes_file = os.path.join(self.annotations_path, 'yolo', 'classes.txt')
        with open(classes_file, 'w') as f:
            for class_name in self.class_names:
                f.write(f"{class_name}\n")
                
    def export_coco_dataset(self):
        """Export complete COCO dataset file."""
        coco_dir = os.path.join(self.annotations_path, 'coco')
        output_file = os.path.join(coco_dir, 'annotations.json')
        
        # Combine all individual COCO files
        coco_dataset = {
            'info': {
                'description': 'Generated dataset by GENxCRY',
                'version': '1.0',
                'year': datetime.now().year,
                'contributor': 'RN Software',
                'date_created': datetime.now().isoformat()
            },
            'licenses': [],
            'images': [],
            'annotations': [],
            'categories': []
        }
        
        # Add categories
        for idx, class_name in enumerate(self.class_names):
            coco_dataset['categories'].append({
                'id': idx,
                'name': class_name,
                'supercategory': 'object'
            })
            
        # Combine individual annotation files
        annotation_id = 0
        for filename in os.listdir(coco_dir):
            if filename.endswith('.json') and filename != 'annotations.json':
                filepath = os.path.join(coco_dir, filename)
                
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        
                    coco_dataset['images'].append(data['image'])
                    
                    for ann in data['annotations']:
                        ann['id'] = annotation_id
                        annotation_id += 1
                        coco_dataset['annotations'].append(ann)
                except Exception:
                    continue
                    
        # Save combined dataset
        with open(output_file, 'w') as f:
            json.dump(coco_dataset, f, indent=2)
