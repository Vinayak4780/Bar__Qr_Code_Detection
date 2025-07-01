# Barcode & QR Code Detection System

A streamlined application for detecting and decoding barcodes and QR codes from images and live camera feeds with automatic Excel export.

## Features

- **Image Processing**: Load and process images to detect barcodes and QR codes
- **Live Camera**: Real-time detection from camera feeds
- **Automatic Export**: All detections are automatically saved to an Excel file
- **User-Friendly Interface**: Simple tabbed interface for different functions
- **Supported Code Types**: 
  - QR Code, Data Matrix, PDF417, Aztec
  - EAN-8, EAN-13, UPC-A, UPC-E
  - Code-39, Code-93, Code-128
  - ITF, Codabar

## Installation

1. Clone this repository or download the source code.
2. Install the required dependencies:
```
pip install -r requirements.txt
```

## Dependencies

- OpenCV (opencv-python)
- NumPy
- Pillow (PIL)
- openpyxl
- psutil

## Usage

Run the application with:
```
python main.py
```

### Image Processing Tab

1. Click "Open Image" to select an image file
2. Click "Process Image" to detect codes
3. Results will be displayed and automatically saved to Excel

### Camera Tab

1. Select a camera from the dropdown list
2. Click "Start Camera" to begin real-time detection
3. Detected codes will be displayed and automatically saved to Excel

## Project Structure

- **main.py**: Main entry point for the application
- **core/**: Core functionality
  - **opencv_detector.py**: Detection engine using OpenCV
  - **camera.py**: Camera management
  - **exporter.py**: Excel export functionality
- **gui/**: User interface
  - **main_window.py**: Main GUI implementation
- **utils/**: Utility functions
  - **performance.py**: FPS tracking and performance monitoring
- **exports/**: Directory where Excel files are saved

## Command Line Options

```
python main.py --help       # Show help information
python main.py --version    # Show version information
python main.py --check-deps # Check dependencies
```
