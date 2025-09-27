# Sample Workflow - GENxCRY

This document provides a step-by-step example of using GENxCRY to create an AI dataset.

## Example: Creating a Vehicle Detection Dataset

### Step 1: Prepare Input Images
1. Collect 10-20 images containing vehicles (cars, trucks, motorcycles)
2. Ensure images have good variety in:
   - Vehicle types and colors
   - Lighting conditions
   - Backgrounds
   - Angles and perspectives

### Step 2: Launch GENxCRY
```bash
# Windows
run.bat

# Linux/Mac
chmod +x run.sh
./run.sh
```

### Step 3: Image Selection
1. Click "Browse Images" and select your vehicle images
2. Select annotation types:
   - ✅ Bounding Box Annotation
   - ✅ Labeling Annotation
   - ⬜ Segmentation Annotation (optional)
3. Click "Proceed to Annotation"

### Step 4: Annotation
1. For each image:
   - Select "Bounding Box" tool
   - Draw rectangles around each vehicle
   - Double-click to add labels: "car", "truck", "motorcycle"
   - Use right-click menu to edit or delete annotations
2. Navigate through all images using Previous/Next buttons
3. Click "Save & Close" when done

### Step 5: Augmentation Configuration

#### Geometric Variations
- ✅ Rotation: -30° to +30°
- ✅ Flipping: Horizontal only
- ✅ Scaling: 0.8x to 1.2x
- ✅ Translation: 10% range

#### Visual Effects
- ✅ Brightness: ±20%
- ✅ Contrast: 0.8x to 1.2x
- ✅ Blur: Kernel size 3-7
- ⬜ Advanced effects (optional)

#### Background & Noise
- ✅ Random Texture
- ✅ Scribbled Background
- ✅ Gaussian Noise: 1% std
- Add custom road/parking lot backgrounds if available

### Step 6: Dataset Generation
1. Set output directory: `./vehicle_dataset`
2. Dataset size: 1000 images
3. Export formats:
   - ✅ YOLO (for YOLOv8 training)
   - ✅ COCO (for general object detection)
4. Object mixing settings:
   - ✅ Enable mixing
   - Max objects per image: 3
   - Min spacing: 20 pixels
5. Click "Generate Dataset"

### Expected Output
```
vehicle_dataset/
├── images/
│   ├── image_000001.jpg
│   ├── image_000002.jpg
│   └── ...
├── annotations/
│   ├── yolo/
│   │   ├── image_000001.txt
│   │   ├── dataset.yaml
│   │   └── classes.txt
│   └── coco/
│       ├── image_000001.json
│       └── annotations.json
└── dataset_info.json
```

### Training with Generated Dataset

#### YOLOv8 Training
```python
from ultralytics import YOLO

# Load model
model = YOLO('yolov8n.pt')

# Train
model.train(
    data='vehicle_dataset/annotations/yolo/dataset.yaml',
    epochs=100,
    imgsz=640
)
```

#### Custom Training
Use the COCO format annotations with your preferred object detection framework.

## Tips for Better Results

1. **Quality over Quantity**: Better to have fewer well-annotated images than many poor ones
2. **Diverse Backgrounds**: Add various background images for more realistic augmentation
3. **Balanced Classes**: Ensure all vehicle types are well represented
4. **Validation Split**: Reserve some original images for validation (don't augment them)
5. **Iterative Improvement**: Start small, test your model, then generate larger datasets

## Common Issues

### Low Detection Accuracy
- Increase object spacing in mixing settings
- Reduce blur and noise levels
- Add more diverse source images

### Unrealistic Images
- Reduce geometric transformation ranges
- Use more appropriate background images
- Lower augmentation intensity

### Class Imbalance
- Manually adjust object selection during generation
- Create separate datasets for underrepresented classes
