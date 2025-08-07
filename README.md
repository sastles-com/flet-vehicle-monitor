# Python Image Editor

A desktop image editor built with Python, using Flet for the GUI and PIL/Pillow for image processing.

## Features

- **Image Loading**: Support for PNG, JPG, JPEG, GIF, and BMP formats
- **Transform Operations**:
  - Resize images to custom dimensions
  - Rotate images by any angle
  - Flip horizontally or vertically
- **Filters**:
  - Blur
  - Sharpen
  - Contour
  - Emboss
  - Grayscale conversion
- **Adjustments**:
  - Brightness control
  - Contrast control
  - Saturation control
- **File Operations**:
  - Save edited images in PNG or JPEG format
  - Reset to original image

## Installation

1. Install Python 3.8 or higher
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python main.py
```

### How to Use

1. Click the folder icon in the top bar to open an image
2. Use the controls panel on the right to edit your image:
   - **Transform**: Resize, rotate, or flip your image
   - **Filters**: Apply various artistic filters
   - **Adjustments**: Fine-tune brightness, contrast, and saturation with sliders
3. Click "Reset" to revert all changes
4. Click "Save As" to save your edited image

## Requirements

- Python 3.8+
- flet 0.21.2
- Pillow 10.2.0
- numpy 1.26.4

## Controls Guide

### Transform Operations
- **Resize**: Enter width and height in pixels, then click "Resize"
- **Rotate**: Enter rotation angle in degrees, then click "Rotate"
- **Flip**: Click buttons to flip the image horizontally or vertically

### Filters
- Click any filter button to apply it instantly
- Filters can be applied multiple times for stronger effects

### Adjustments
- Use sliders to adjust in real-time:
  - Brightness: 0.5 (darker) to 2.0 (brighter)
  - Contrast: 0.5 (less) to 2.0 (more)
  - Saturation: 0 (grayscale) to 2.0 (vivid)

## Tips

- The editor maintains the original image, so you can always reset
- Adjustments are applied in real-time as you move the sliders
- Multiple filters can be combined for creative effects
- The image display automatically fits to the window while maintaining aspect ratio