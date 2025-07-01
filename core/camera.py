import cv2
import threading
import time
from typing import Optional, Callable, Tuple
import numpy as np
from queue import Queue
import os


def suppress_cv2_warnings():
    """Suppress OpenCV warnings and error messages."""
    os.environ['OPENCV_LOG_LEVEL'] = 'FATAL'
    try:
        # Try to set log level - compatible with different OpenCV versions
        cv2.setLogLevel(0)
    except AttributeError:
        # Older OpenCV versions don't have setLogLevel
        pass


class CameraManager:
    """
    Advanced camera manager for handling live video streams with threading support.
    Provides smooth video capture and processing capabilities.
    """
    
    def __init__(self, camera_index: int = 0):
        # Suppress OpenCV warnings and errors for cleaner console output
        suppress_cv2_warnings()
        
        self.camera_index = camera_index
        self.cap = None
        self.is_running = False
        self.frame_queue = Queue(maxsize=2)
        self.capture_thread = None
        self.fps_counter = FPSCounter()
        self.frame_callback = None
        
        # Camera properties
        self.frame_width = 640
        self.frame_height = 480
        self.target_fps = 30
        
    def initialize_camera(self) -> bool:
        """
        Initialize camera with optimal settings.
        
        Returns:
            True if camera initialized successfully, False otherwise
        """
        # Temporarily suppress OpenCV messages
        original_log_level = None
        try:
            original_log_level = cv2.getLogLevel()
            cv2.setLogLevel(0)  # Use 0 instead of LOG_LEVEL_SILENT for compatibility
        except AttributeError:
            # Older OpenCV versions don't have these methods
            pass
        
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            
            if not self.cap.isOpened():
                return False
            
            # Set camera properties for optimal performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)
            
            # Enable auto-exposure and auto-white balance for better quality
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)
            
            # Test capture
            ret, frame = self.cap.read()
            if not ret:
                self.cap.release()
                return False
                
            return True
            
        except Exception:
            # Silently fail - errors will be handled by calling code
            return False
        finally:
            # Restore original log level if available
            try:
                if original_log_level is not None:
                    cv2.setLogLevel(original_log_level)
            except AttributeError:
                # Older OpenCV versions don't have these methods
                pass
    
    def start_capture(self, frame_callback: Optional[Callable] = None):
        """
        Start threaded video capture.
        
        Args:
            frame_callback: Optional callback function to process frames
        """
        if not self.cap or not self.cap.isOpened():
            if not self.initialize_camera():
                raise RuntimeError("Failed to initialize camera")
        
        self.frame_callback = frame_callback
        self.is_running = True
        self.capture_thread = threading.Thread(target=self._capture_loop)
        self.capture_thread.daemon = True
        self.capture_thread.start()
    
    def stop_capture(self):
        """Stop video capture and cleanup resources."""
        self.is_running = False
        
        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)
        
        if self.cap:
            self.cap.release()
            self.cap = None
    
    def _capture_loop(self):
        """Main capture loop running in separate thread."""
        while self.is_running:
            try:
                ret, frame = self.cap.read()
                
                if not ret:
                    print("Failed to read frame from camera")
                    break
                
                # Update FPS counter
                self.fps_counter.update()
                
                # Clear queue if full to prevent lag
                if self.frame_queue.full():
                    try:
                        self.frame_queue.get_nowait()
                    except:
                        pass
                
                # Add frame to queue
                try:
                    self.frame_queue.put_nowait(frame)
                except:
                    pass
                
                # Call frame callback if provided
                if self.frame_callback:
                    try:
                        self.frame_callback(frame)
                    except Exception as e:
                        print(f"Error in frame callback: {e}")
                
                # Control frame rate
                time.sleep(1.0 / self.target_fps)
                
            except Exception as e:
                print(f"Error in capture loop: {e}")
                break
    
    def get_latest_frame(self) -> Optional[np.ndarray]:
        """
        Get the latest available frame.
        
        Returns:
            Latest frame or None if no frame available
        """
        try:
            return self.frame_queue.get_nowait()
        except:
            return None
    
    def get_frame_blocking(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """
        Get frame with blocking wait.
        
        Args:
            timeout: Maximum time to wait for frame
            
        Returns:
            Frame or None if timeout
        """
        try:
            return self.frame_queue.get(timeout=timeout)
        except:
            return None
    
    def get_camera_info(self) -> dict:
        """
        Get camera information and properties.
        
        Returns:
            Dictionary with camera information
        """
        if not self.cap or not self.cap.isOpened():
            return {}
        
        try:
            info = {
                "width": int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height": int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                "fps": self.cap.get(cv2.CAP_PROP_FPS),
                "brightness": self.cap.get(cv2.CAP_PROP_BRIGHTNESS),
                "contrast": self.cap.get(cv2.CAP_PROP_CONTRAST),
                "saturation": self.cap.get(cv2.CAP_PROP_SATURATION),
                "hue": self.cap.get(cv2.CAP_PROP_HUE),
                "exposure": self.cap.get(cv2.CAP_PROP_EXPOSURE),
                "current_fps": self.fps_counter.get_fps()
            }
            return info
        except Exception as e:
            print(f"Error getting camera info: {e}")
            return {}
    
    def set_camera_property(self, property_id: int, value: float) -> bool:
        """
        Set camera property.
        
        Args:
            property_id: OpenCV property ID
            value: Property value
            
        Returns:
            True if property set successfully
        """
        if not self.cap or not self.cap.isOpened():
            return False
        
        try:
            return self.cap.set(property_id, value)
        except Exception as e:
            print(f"Error setting camera property: {e}")
            return False
    
    def list_available_cameras(self) -> list:
        """
        List all available cameras.
        
        Returns:
            List of available camera indices
        """
        available_cameras = []
        
        # Temporarily suppress all OpenCV messages
        original_log_level = None
        try:
            original_log_level = cv2.getLogLevel()
            cv2.setLogLevel(0)  # Use 0 instead of LOG_LEVEL_SILENT for compatibility
        except AttributeError:
            # Older OpenCV versions don't have these methods
            pass
        
        try:
            for i in range(10):  # Check first 10 indices
                try:
                    # Suppress OpenCV error messages for unavailable cameras
                    cap = cv2.VideoCapture(i)
                    if cap.isOpened():
                        ret, _ = cap.read()
                        if ret:
                            available_cameras.append(i)
                    cap.release()
                except Exception:
                    # Silently skip unavailable cameras
                    continue
        finally:
            # Restore original log level if available
            try:
                if original_log_level is not None:
                    cv2.setLogLevel(original_log_level)
            except AttributeError:
                # Older OpenCV versions don't have these methods
                pass
        
        return available_cameras
    
    def get_fps(self) -> float:
        """Get current FPS."""
        return self.fps_counter.get_fps()
    
    def is_camera_active(self) -> bool:
        """Check if camera is active and capturing."""
        return self.is_running and self.cap and self.cap.isOpened()
    
    def has_available_cameras(self) -> bool:
        """
        Quick check if any cameras are available.
        
        Returns:
            True if at least one camera is available
        """
        return len(self.list_available_cameras()) > 0


class FPSCounter:
    """Simple FPS counter for performance monitoring."""
    
    def __init__(self):
        self.frame_count = 0
        self.start_time = time.time()
        self.fps = 0.0
        self.last_update = time.time()
    
    def update(self):
        """Update frame count and calculate FPS."""
        self.frame_count += 1
        current_time = time.time()
        
        # Update FPS every second
        if current_time - self.last_update >= 1.0:
            elapsed_time = current_time - self.start_time
            if elapsed_time > 0:
                self.fps = self.frame_count / elapsed_time
            
            # Reset for next measurement
            self.frame_count = 0
            self.start_time = current_time
            self.last_update = current_time
    
    def get_fps(self) -> float:
        """Get current FPS."""
        return self.fps
    
    def reset(self):
        """Reset FPS counter."""
        self.frame_count = 0
        self.start_time = time.time()
        self.fps = 0.0
        self.last_update = time.time()


class ROISelector:
    """Interactive region of interest selector."""
    
    def __init__(self):
        self.start_point = None
        self.end_point = None
        self.selecting = False
        self.roi = None
    
    def mouse_callback(self, event, x, y, flags, param):
        """Mouse callback for ROI selection."""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.start_point = (x, y)
            self.selecting = True
            
        elif event == cv2.EVENT_MOUSEMOVE and self.selecting:
            self.end_point = (x, y)
            
        elif event == cv2.EVENT_LBUTTONUP:
            self.end_point = (x, y)
            self.selecting = False
            
            if self.start_point and self.end_point:
                x1, y1 = self.start_point
                x2, y2 = self.end_point
                
                # Ensure correct order
                x = min(x1, x2)
                y = min(y1, y2)
                w = abs(x2 - x1)
                h = abs(y2 - y1)
                
                self.roi = (x, y, w, h)
    
    def draw_roi(self, image: np.ndarray) -> np.ndarray:
        """Draw ROI rectangle on image."""
        if self.start_point and self.end_point:
            cv2.rectangle(image, self.start_point, self.end_point, (0, 255, 255), 2)
        return image
    
    def get_roi(self) -> Optional[Tuple[int, int, int, int]]:
        """Get selected ROI."""
        return self.roi
    
    def reset(self):
        """Reset ROI selection."""
        self.start_point = None
        self.end_point = None
        self.selecting = False
        self.roi = None
