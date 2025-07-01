import time
import psutil
import threading
from typing import Dict
from datetime import datetime


class PerformanceMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.frame_times = []
        self.last_frame_time = time.time()
        self.frame_count = 0
        self.detection_count = 0
        self.monitoring = False
        self.monitoring_thread = None
        self.lock = threading.Lock()
        
    def start_monitoring(self):
        """Start performance monitoring."""
        self.monitoring = True
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring = False
    
    def update_fps(self):
        """Update FPS calculation with new frame."""
        current_time = time.time()
        
        with self.lock:
            self.frame_times.append(current_time)
            self.frame_count += 1
            
            # Keep only last 60 frame times for rolling FPS calculation
            if len(self.frame_times) > 60:
                self.frame_times = self.frame_times[-60:]
        
        self.last_frame_time = current_time
    
    def record_detection_time(self, detection_time: float):
        """Record detection."""
        with self.lock:
            self.detection_count += 1
    
    def get_current_fps(self) -> float:
        """Calculate current FPS based on recent frames."""
        with self.lock:
            if len(self.frame_times) < 2:
                return 0.0
            
            time_span = self.frame_times[-1] - self.frame_times[0]
            if time_span <= 0:
                return 0.0
            
            return (len(self.frame_times) - 1) / time_span
    
    def get_performance_summary(self) -> Dict:
        """Get basic performance summary."""
        with self.lock:
            fps = self.get_current_fps()
            
            summary = {
                'fps': {'current': fps},
                'detection': {'total_detections': self.detection_count}
            }
            
            return summary
    
    def reset_stats(self):
        """Reset all performance statistics."""
        with self.lock:
            self.start_time = time.time()
            self.frame_times.clear()
            self.frame_count = 0
            self.detection_count = 0
        
    def get_current_metrics(self) -> Dict:
        """Get current performance metrics."""
        return self.get_performance_summary()
