import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
import time
from dataclasses import dataclass


@dataclass
class DetectionResult:
    """Data class for storing detection results."""
    data: str
    type: str
    rect: Tuple[int, int, int, int]  # (x, y, width, height)
    polygon: List[Tuple[int, int]]
    confidence: float
    detection_time: float


class OpenCVDetector:
    """
    OpenCV-based QR code detector that works without external dependencies.
    Uses OpenCV's built-in QR code detection capabilities.
    """
    
    def __init__(self):
        self.qr_detector = cv2.QRCodeDetector()
        self.detection_history = []
        
    def detect_codes(self, image: np.ndarray, roi: Optional[Tuple[int, int, int, int]] = None) -> List[DetectionResult]:
        """
        Detect and decode QR codes and barcodes in an image using OpenCV and pyzbar.
        Returns a list of DetectionResult for all found codes.
        """
        start_time = time.time()
        # Apply ROI if specified
        if roi:
            x, y, w, h = roi
            image = image[y:y+h, x:x+w]
            roi_offset = (x, y)
        else:
            roi_offset = (0, 0)
        results = []
        # --- QR CODE DETECTION (OpenCV) ---
        try:
            data, points, _ = self.qr_detector.detectAndDecode(image)
            if data and points is not None:
                polygon = [(int(p[0]) + roi_offset[0], int(p[1]) + roi_offset[1]) for p in points[0]]
                x = min([p[0] for p in polygon])
                y = min([p[1] for p in polygon])
                w = max([p[0] for p in polygon]) - x
                h = max([p[1] for p in polygon]) - y
                detection_time = time.time() - start_time
                result = DetectionResult(
                    data=data,
                    type="QRCODE",
                    rect=(x, y, w, h),
                    polygon=polygon,
                    confidence=0.9,
                    detection_time=detection_time
                )
                results.append(result)
            # Try to detect multiple QR codes using detectMulti
            success, decoded_info, points_array, _ = self.qr_detector.detectAndDecodeMulti(image)
            if success:
                for i, (data, points) in enumerate(zip(decoded_info, points_array)):
                    if data and len(data.strip()) > 0:
                        # Skip if we already found this one
                        if any(r.data == data for r in results):
                            continue
                        polygon = [(int(p[0]) + roi_offset[0], int(p[1]) + roi_offset[1]) for p in points]
                        x = min([p[0] for p in polygon])
                        y = min([p[1] for p in polygon])
                        w = max([p[0] for p in polygon]) - x
                        h = max([p[1] for p in polygon]) - y
                        detection_time = time.time() - start_time
                        result = DetectionResult(
                            data=data,
                            type="QRCODE",
                            rect=(x, y, w, h),
                            polygon=polygon,
                            confidence=0.9,
                            detection_time=detection_time
                        )
                        results.append(result)
        except Exception as e:
            print(f"QR Detection error: {e}")
        # --- BARCODE DETECTION (pyzbar) ---
        try:
            from pyzbar import pyzbar
            barcodes = pyzbar.decode(image)
            for barcode in barcodes:
                barcode_data = barcode.data.decode("utf-8")
                barcode_type = barcode.type
                (x, y, w, h) = barcode.rect
                polygon = [(point.x, point.y) for point in barcode.polygon] if barcode.polygon else [
                    (x, y), (x + w, y), (x + w, y + h), (x, y + h)]
                detection_time = time.time() - start_time
                # Avoid duplicates (e.g., QR detected by both OpenCV and pyzbar)
                if not any(r.data == barcode_data for r in results):
                    result = DetectionResult(
                        data=barcode_data,
                        type=barcode_type,
                        rect=(x, y, w, h),
                        polygon=polygon,
                        confidence=0.9,
                        detection_time=detection_time
                    )
                    results.append(result)
        except ImportError:
            pass  # pyzbar not installed, skip barcode detection
        except Exception as e:
            print(f"Barcode Detection error: {e}")
        self.detection_history.extend(results)
        return results
    
    def detect_in_video_frame(self, frame: np.ndarray, roi: Optional[Tuple[int, int, int, int]] = None) -> Tuple[List[DetectionResult], np.ndarray]:
        """
        Detect codes in video frame and return annotated frame.
        
        Args:
            frame: Video frame
            roi: Region of interest
            
        Returns:
            Tuple of (detection results, annotated frame)
        """
        results = self.detect_codes(frame, roi)
        annotated_frame = self.draw_detections(frame.copy(), results)
        
        return results, annotated_frame
    
    def draw_detections(self, image: np.ndarray, results: List[DetectionResult]) -> np.ndarray:
        """
        Draw bounding boxes and labels on detected codes with clear, readable text.
        
        Args:
            image: Input image
            results: Detection results
            
        Returns:
            Annotated image
        """
        for result in results:
            # Draw polygon with thicker lines
            polygon_points = np.array(result.polygon, dtype=np.int32)
            cv2.polylines(image, [polygon_points], True, (0, 255, 0), 3)
            
            # Draw bounding rectangle with thicker lines
            x, y, w, h = result.rect
            cv2.rectangle(image, (x, y), (x + w, y + h), (255, 0, 0), 3)
            
            # Prepare label text with better formatting
            data_display = result.data if len(result.data) <= 80 else result.data[:77] + "..."
            
            label_lines = [
                f"Type: {result.type}",
                f"Confidence: {result.confidence:.1%}",
                "Content:",
                data_display
            ]
            
            # Use larger, more readable font
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.8  # Larger font
            thickness = 2     # Thicker text
            
            # Calculate text size for background
            text_sizes = [cv2.getTextSize(line, font, font_scale, thickness)[0] for line in label_lines]
            max_width = max([size[0] for size in text_sizes])
            line_height = 25  # More spacing between lines
            total_height = len(label_lines) * line_height + 10
            
            # Position the text box (prefer above the detection, but below if no space)
            if y - total_height > 0:
                # Draw above
                bg_y = y - total_height
                text_start_y = bg_y + line_height
            else:
                # Draw below
                bg_y = y + h
                text_start_y = bg_y + line_height
            
            # Draw background rectangle with padding
            padding = 10
            cv2.rectangle(image, 
                         (x - padding, bg_y), 
                         (x + max_width + padding * 2, bg_y + total_height), 
                         (0, 0, 0), -1)
            
            # Draw border around background
            cv2.rectangle(image, 
                         (x - padding, bg_y), 
                         (x + max_width + padding * 2, bg_y + total_height), 
                         (255, 255, 255), 2)
            
            # Draw text with different colors for better readability
            colors = [
                (255, 255, 0),   # Yellow for type
                (0, 255, 255),   # Cyan for confidence  
                (255, 255, 255), # White for "Content:" label
                (0, 255, 0)      # Green for actual content
            ]
            
            for i, (line, color) in enumerate(zip(label_lines, colors)):
                text_y = text_start_y + i * line_height
                cv2.putText(image, line, (x, text_y), font, font_scale, color, thickness)
                
        return image
    
    # batch_process_images removed (not needed for minimal camera/image GUI)
    
    def get_detection_statistics(self) -> Dict:
        """
        Get statistics about detection history.
        
        Returns:
            Dictionary with detection statistics
        """
        if not self.detection_history:
            return {"total_detections": 0}
            
        types = [result.type for result in self.detection_history]
        confidences = [result.confidence for result in self.detection_history]
        times = [result.detection_time for result in self.detection_history]
        
        stats = {
            "total_detections": len(self.detection_history),
            "code_types": dict(zip(*np.unique(types, return_counts=True))),
            "average_confidence": np.mean(confidences),
            "average_detection_time": np.mean(times),
            "max_detection_time": np.max(times),
            "min_detection_time": np.min(times)
        }
        
        return stats
    
    def clear_history(self):
        """Clear detection history."""
        self.detection_history.clear()


# Create an alias for backward compatibility
BarcodeQRDetector = OpenCVDetector
