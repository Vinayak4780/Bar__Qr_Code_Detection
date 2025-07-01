import sys
import os
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Core imports
    from core.opencv_detector import BarcodeQRDetector
    from core.camera import CameraManager
    from core.exporter import ResultExporter
    from utils.performance import PerformanceMonitor
    from gui.main_window import SimpleMainWindow as MainWindow
    
    # Standard library imports
    from tkinter import messagebox
    import signal
    import atexit
    
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please ensure all dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)


class BarcodeQRApplication:
    """Main application class that coordinates all components."""
    
    def __init__(self):
        self.detector = None
        self.camera_manager = None
        self.exporter = None
        self.performance_monitor = None
        self.main_window = None
        self.initialized = False
        
        # Register cleanup handlers
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def initialize(self):
        """Initialize all application components."""
        try:
            print("Initializing Barcode & QR Code Detection System...")
            
            # Initialize core components
            self.detector = BarcodeQRDetector()
            print("✓ Detection engine initialized")
            
            self.camera_manager = CameraManager()
            print("✓ Camera manager initialized")
            
            self.exporter = ResultExporter()
            print("✓ Export system initialized")
            
            self.performance_monitor = PerformanceMonitor()
            print("✓ Performance monitor initialized")
            
            # Create output directories
            self.create_directories()
            
            self.initialized = True
            print("✓ Application initialization complete")
            
        except Exception as e:
            print(f"✗ Initialization failed: {e}")
            raise
    
    def create_directories(self):
        """Create necessary output directory."""
        try:
            os.makedirs('exports', exist_ok=True)
            print("✓ Directory created/verified: exports")
        except Exception as e:
            print(f"Warning: Could not create exports directory: {e}")
    
    def run_gui(self):
        """Run the main GUI application."""
        if not self.initialized:
            self.initialize()
        
        try:
            # Create and run main window
            self.main_window = MainWindow(
                detector=self.detector,
                camera_manager=self.camera_manager,
                exporter=self.exporter,
                performance_monitor=self.performance_monitor
            )
            
            print("Starting GUI application...")
            self.main_window.run()
            
        except Exception as e:
            print(f"GUI application error: {e}")
            messagebox.showerror("Application Error", f"An error occurred: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources."""
        if not self.initialized:
            return
        
        print("\nCleaning up application resources...")
        
        try:
            if self.camera_manager and self.camera_manager.is_camera_active():
                self.camera_manager.stop_capture()
            
            if self.performance_monitor:
                self.performance_monitor.stop_monitoring()
            
            print("✓ Cleanup completed")
            
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    def signal_handler(self, signum, frame):
        """Handle system signals gracefully."""
        print(f"\nReceived signal {signum}, shutting down gracefully...")
        self.cleanup()
        sys.exit(0)


def check_dependencies():
    """Check if all required dependencies are available."""
    required_modules = [
        ('cv2', 'opencv-python'),
        ('PIL', 'pillow'),
        ('numpy', 'numpy'),
        ('psutil', 'psutil'),
        ('openpyxl', 'openpyxl')
    ]
    
    missing_modules = []
    
    for module_name, package_name in required_modules:
        try:
            __import__(module_name)
        except ImportError:
            missing_modules.append(package_name)
    
    if missing_modules:
        print("Missing required dependencies:")
        for module in missing_modules:
            print(f"  - {module}")
        print("\nInstall missing dependencies with:")
        print("pip install " + " ".join(missing_modules))
        return False
    
    return True


def show_help():
    """Show command line help."""
    help_text = """
Barcode & QR Code Detection System

Usage:
    python main.py [options]

Options:
    --help, -h      Show this help message
    --version       Show version information
    --check-deps    Check dependencies

Features:
    • Image processing with enhancement options
    • Live camera feed processing with real-time detection
    • Automatic Excel export of all detections
    • Support for QR codes and various barcode formats
    
Usage:
    1. Process images: Open an image file and detect codes
    2. Use camera: Detect codes in real-time from camera feed
    3. All detections are automatically saved to Excel
    """
    print(help_text.strip())


def show_version():
    """Show version information."""
    version_info = """
Barcode & QR Code Detection System
Version: 1.0.0
Build Date: 2025-07-01

Dependencies:
    • OpenCV 4.x
    • tkinter
    • NumPy
    • Pillow
    • psutil
    • openpyxl
    """
    print(version_info.strip())


def main():
    """Main entry point."""
    # Parse command line arguments
    args = sys.argv[1:]
    
    if '--help' in args or '-h' in args:
        show_help()
        return
    
    if '--version' in args:
        show_version()
        return
    
    if '--check-deps' in args:
        print("Checking dependencies...")
        if check_dependencies():
            print("✓ All dependencies are installed")
        else:
            print("✗ Some dependencies are missing")
        return
    
    # Check dependencies before proceeding
    if not check_dependencies():
        print("\nPlease install missing dependencies before running the application.")
        return
    
    # Create and run application
    app = BarcodeQRApplication()
    
    try:
        app.run_gui()
    
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        print(f"Application error: {e}")
    finally:
        app.cleanup()


if __name__ == "__main__":
    main()
