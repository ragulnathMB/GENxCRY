"""
Augmentation Engine
Handles all image augmentation operations.
"""

import random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from typing import Dict, List, Tuple, Optional

class AugmentationEngine:
    """Engine for applying various image augmentations."""
    
    def __init__(self, config: dict):
        self.config = config
        
    def create_background(self, size: Tuple[int, int], background_images: List[Image.Image] = None) -> Image.Image:
        """Create a background image."""
        config = self.config['noise']
        
        if config['background_replacement']['enabled'] and background_images:
            # Use custom background
            bg = random.choice(background_images)
            bg = bg.resize(size, Image.Resampling.LANCZOS)
            
        elif config['scribbled_background']['enabled']:
            # Create scribbled background
            bg = self.create_scribbled_background(size)
            
        elif config['random_texture']['enabled']:
            # Create textured background
            bg = self.create_textured_background(size)
            
        else:
            # Solid color background
            color = (random.randint(200, 255), random.randint(200, 255), random.randint(200, 255))
            bg = Image.new('RGB', size, color)
            
        # Add noise if enabled
        if config['gaussian']['enabled']:
            bg = self.add_gaussian_noise(bg, config['gaussian']['std'])
            
        if config['salt_pepper']['enabled']:
            bg = self.add_salt_pepper_noise(bg, config['salt_pepper']['amount'])
            
        return bg
        
    def create_scribbled_background(self, size: Tuple[int, int]) -> Image.Image:
        """Create a scribbled background."""
        bg = Image.new('RGB', size, (240, 240, 240))
        draw = ImageDraw.Draw(bg)
        
        # Add random scribbles
        num_scribbles = random.randint(20, 50)
        for _ in range(num_scribbles):
            # Random color - ensure it's a proper RGB tuple
            color = (random.randint(100, 200), random.randint(100, 200), random.randint(100, 200))
            
            # Random scribble
            points = []
            start_x = random.randint(0, size[0] - 1)
            start_y = random.randint(0, size[1] - 1)
            
            for i in range(random.randint(5, 15)):
                x = start_x + random.randint(-50, 50)
                y = start_y + random.randint(-50, 50)
                x = max(0, min(size[0] - 1, x))
                y = max(0, min(size[1] - 1, y))
                points.append((x, y))
                
            if len(points) > 1:
                try:
                    draw.line(points, fill=color, width=random.randint(1, 3))
                except Exception as e:
                    # Fallback to simple line if there's an issue
                    if len(points) >= 2:
                        draw.line([points[0], points[-1]], fill=color, width=1)
                
        return bg
        
    def create_textured_background(self, size: Tuple[int, int]) -> Image.Image:
        """Create a textured background."""
        # Create noise texture
        noise = np.random.randint(0, 256, (size[1], size[0], 3), dtype=np.uint8)
        bg = Image.fromarray(noise)
        
        # Blur to create texture
        bg = bg.filter(ImageFilter.GaussianBlur(radius=2))
        
        # Adjust brightness
        enhancer = ImageEnhance.Brightness(bg)
        bg = enhancer.enhance(0.8)
        
        return bg
        
    def add_gaussian_noise(self, image: Image.Image, std: float) -> Image.Image:
        """Add Gaussian noise to image."""
        img_array = np.array(image)
        noise = np.random.normal(0, std * 255, img_array.shape)
        noisy_array = np.clip(img_array + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(noisy_array)
        
    def add_salt_pepper_noise(self, image: Image.Image, amount: float) -> Image.Image:
        """Add salt and pepper noise to image."""
        img_array = np.array(image)
        
        # Salt noise
        salt = np.random.random(img_array.shape[:2]) < amount / 2
        img_array[salt] = 255
        
        # Pepper noise
        pepper = np.random.random(img_array.shape[:2]) < amount / 2
        img_array[pepper] = 0
        
        return Image.fromarray(img_array)
        
    def augment_object(self, obj_data: dict) -> dict:
        """Apply augmentations to an object."""
        image = obj_data['image'].copy()
        mask = obj_data['mask'].copy()
        
        config = self.config
        
        # Geometric transformations
        if config['geometric']['rotation']['enabled']:
            angle = random.uniform(
                config['geometric']['rotation']['min_angle'],
                config['geometric']['rotation']['max_angle']
            )
            # Handle fillcolor based on image mode
            if image.mode == 'RGBA':
                image = image.rotate(angle, expand=True, fillcolor=(0, 0, 0, 0))
            else:
                image = image.rotate(angle, expand=True, fillcolor=0)
            mask = mask.rotate(angle, expand=True, fillcolor=0)
            
        if config['geometric']['scaling']['enabled']:
            scale = random.uniform(*config['geometric']['scaling']['scale_range'])
            new_size = (int(image.width * scale), int(image.height * scale))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            mask = mask.resize(new_size, Image.Resampling.LANCZOS)
            
        if config['geometric']['flipping']['enabled']:
            if config['geometric']['flipping']['horizontal'] and random.random() < 0.5:
                image = image.transpose(Image.FLIP_LEFT_RIGHT)
                mask = mask.transpose(Image.FLIP_LEFT_RIGHT)
                
            if config['geometric']['flipping']['vertical'] and random.random() < 0.5:
                image = image.transpose(Image.FLIP_TOP_BOTTOM)
                mask = mask.transpose(Image.FLIP_TOP_BOTTOM)
                
        # Visual effects
        if config['visual']['brightness']['enabled']:
            factor = random.uniform(*config['visual']['brightness']['range'])
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1 + factor)
            
        if config['visual']['contrast']['enabled']:
            factor = random.uniform(*config['visual']['contrast']['range'])
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(factor)
            
        if config['visual']['blur']['enabled']:
            kernel_size = random.randint(*config['visual']['blur']['kernel_size'])
            if kernel_size > 1:
                image = image.filter(ImageFilter.GaussianBlur(radius=kernel_size/2))
                
        return {
            'image': image,
            'mask': mask,
            'label': obj_data['label']
        }
        
    def find_valid_position(self, background: Image.Image, obj_data: dict, 
                          existing_objects: List[dict], min_spacing: int = 20) -> Optional[Tuple[int, int]]:
        """Find a valid position for placing an object.
        
        Ensures objects are placed within reasonable bounds that won't cause
        excessive canvas expansion.
        """
        obj_width, obj_height = obj_data['image'].size
        bg_width, bg_height = background.size
        
        max_attempts = 100
        
        # Allow moderate extension beyond current background (max 50% increase)
        max_extension_factor = 0.5
        extended_width = int(bg_width * (1 + max_extension_factor))
        extended_height = int(bg_height * (1 + max_extension_factor))
        
        # Calculate reasonable bounds for object placement
        # Allow some negative positioning but not excessive
        min_x = -obj_width // 4  # Allow 25% of object to be outside left edge
        max_x = extended_width - (3 * obj_width // 4)  # Ensure 75% of object is within extended area
        min_y = -obj_height // 4  # Allow 25% of object to be outside top edge
        max_y = extended_height - (3 * obj_height // 4)  # Ensure 75% of object is within extended area
        
        # Ensure we have valid ranges
        if max_x <= min_x:
            max_x = min_x + obj_width
        if max_y <= min_y:
            max_y = min_y + obj_height
        
        for _ in range(max_attempts):
            # Place object within reasonable bounds
            x = random.randint(min_x, max_x)
            y = random.randint(min_y, max_y)
            
            # Check overlap with existing objects
            valid = True
            for existing in existing_objects:
                ex_x, ex_y = existing['position']
                ex_width, ex_height = existing['object']['image'].size
                
                # Check if rectangles overlap with minimum spacing
                if not (x + obj_width + min_spacing < ex_x or 
                       x > ex_x + ex_width + min_spacing or
                       y + obj_height + min_spacing < ex_y or
                       y > ex_y + ex_height + min_spacing):
                    valid = False
                    break
                    
            if valid:
                return (x, y)
                
        # If no valid position found, place within safe bounds
        safe_x = max(0, min(min_x + obj_width // 2, bg_width - obj_width))
        safe_y = max(0, min(min_y + obj_height // 2, bg_height - obj_height))
        return (safe_x, safe_y)
        
    def composite_image(self, background: Image.Image, objects_data: List[dict]) -> Image.Image:
        """Composite objects onto background."""
        result = background.copy()
        
        for obj_info in objects_data:
            obj_image = obj_info['object']['image']
            obj_mask = obj_info['object']['mask']
            position = obj_info['position']
            
            try:
                # Ensure proper image mode handling
                if obj_image.mode != 'RGBA':
                    obj_image = obj_image.convert('RGBA')
                    
                # Use mask as alpha channel if available
                if obj_mask and obj_mask.mode == 'L':
                    # Ensure mask is the same size as the image
                    if obj_mask.size != obj_image.size:
                        obj_mask = obj_mask.resize(obj_image.size, Image.Resampling.LANCZOS)
                    obj_image.putalpha(obj_mask)
                    
                # Paste object onto background
                if obj_image.mode == 'RGBA':
                    result.paste(obj_image, position, obj_image)
                else:
                    result.paste(obj_image, position)
                    
            except Exception as e:
                # If compositing fails, try a simpler approach
                try:
                    if obj_image.mode != result.mode:
                        obj_image = obj_image.convert(result.mode)
                    result.paste(obj_image, position)
                except:
                    # Skip this object if it can't be composited
                    continue
            
        return result.convert('RGB')
        
    def apply_final_augmentations(self, image: Image.Image) -> Image.Image:
        """Apply final image-level augmentations."""
        config = self.config['visual']
        
        # Add shadows, lighting effects, etc.
        if config['shadows']['enabled'] and random.random() < 0.3:
            image = self.add_shadow_effect(image)
            
        if config['glare']['enabled'] and random.random() < 0.2:
            image = self.add_glare_effect(image)
            
        return image
        
    def add_shadow_effect(self, image: Image.Image) -> Image.Image:
        """Add shadow effect to image."""
        try:
            # Simple shadow effect - darken random areas
            enhancer = ImageEnhance.Brightness(image)
            
            # Create a mask for shadow areas
            mask = Image.new('L', image.size, 255)
            draw = ImageDraw.Draw(mask)
            
            # Add some random dark areas
            for _ in range(random.randint(1, 3)):
                x1 = random.randint(0, image.width // 2)
                y1 = random.randint(0, image.height // 2)
                x2 = x1 + random.randint(50, 200)
                y2 = y1 + random.randint(50, 200)
                
                # Ensure coordinates are within bounds
                x1 = max(0, min(x1, image.width - 1))
                y1 = max(0, min(y1, image.height - 1))
                x2 = max(0, min(x2, image.width - 1))
                y2 = max(0, min(y2, image.height - 1))
                
                # Ensure x2 > x1 and y2 > y1
                if x2 <= x1:
                    x2 = x1 + 1
                if y2 <= y1:
                    y2 = y1 + 1
                
                # Use integer fill value for grayscale mask
                draw.ellipse([x1, y1, x2, y2], fill=128)
                
            # Apply shadow
            shadow_img = enhancer.enhance(0.7)
            return Image.composite(shadow_img, image, mask)
        except Exception as e:
            # If shadow effect fails, return original image
            return image
        
    def add_glare_effect(self, image: Image.Image) -> Image.Image:
        """Add glare effect to image."""
        try:
            # Simple glare effect - brighten random areas
            enhancer = ImageEnhance.Brightness(image)
            
            # Create a mask for glare areas
            mask = Image.new('L', image.size, 0)
            draw = ImageDraw.Draw(mask)
            
            # Add some random bright areas
            for _ in range(random.randint(1, 2)):
                x = random.randint(0, image.width - 1)
                y = random.randint(0, image.height - 1)
                radius = random.randint(30, 100)
                
                # Ensure ellipse coordinates are within bounds
                x1 = max(0, x - radius)
                y1 = max(0, y - radius)
                x2 = min(image.width - 1, x + radius)
                y2 = min(image.height - 1, y + radius)
                
                # Ensure x2 > x1 and y2 > y1
                if x2 <= x1:
                    x2 = x1 + 1
                if y2 <= y1:
                    y2 = y1 + 1
                
                # Use integer fill value for grayscale mask
                draw.ellipse([x1, y1, x2, y2], fill=128)
                
            # Apply glare
            glare_img = enhancer.enhance(1.5)
            return Image.composite(glare_img, image, mask)
        except Exception as e:
            # If glare effect fails, return original image
            return image
