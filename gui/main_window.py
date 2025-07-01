import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import cv2
from PIL import Image, ImageTk
import numpy as np
import threading
import os
import time
from datetime import datetime


class SimpleMainWindow:
    def __init__(self, detector, camera_manager, exporter, performance_monitor):
        self.detector = detector
        self.camera_manager = camera_manager
        self.exporter = exporter
        self.performance_monitor = performance_monitor
        
        # Initialize main window
        self.root = tk.Tk()
        self.root.title("Barcode & QR Code Detection System")
        self.root.geometry("1000x700")
        
        # State variables
        self.current_image = None
        self.current_results = []
        self.camera_active = False
        
        # Excel export settings
        self.excel_export_enabled = tk.BooleanVar(value=True)
        self.excel_file_path = os.path.join("exports", "detections.xlsx")
        
        # Ensure exports directory exists
        os.makedirs("exports", exist_ok=True)
        
        self.setup_ui()
        
        # Initialize camera list after UI is ready
        self.root.after(100, self.refresh_cameras)
        
    def setup_ui(self):
        """Setup the user interface."""
        # Create main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.create_image_tab()
        self.create_camera_tab()
        
        # Status bar
        self.status_frame = ttk.Frame(main_frame)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))
        
        self.status_label = ttk.Label(self.status_frame, text="Ready")
        self.status_label.pack(side=tk.LEFT)
        
        self.detection_count_label = ttk.Label(self.status_frame, text="Detections: 0")
        self.detection_count_label.pack(side=tk.RIGHT)
    
    def create_image_tab(self):
        """Create the image processing tab."""
        self.image_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.image_frame, text="Image Processing")
        
        # Left panel for controls
        left_panel = ttk.Frame(self.image_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # Image controls
        ttk.Label(left_panel, text="Image Controls", font=("Arial", 12, "bold")).pack(pady=5)
        ttk.Button(left_panel, text="Open Image", command=self.open_image).pack(fill=tk.X, pady=2)
        ttk.Button(left_panel, text="Process Image", command=self.process_image).pack(fill=tk.X, pady=2)
        
        ttk.Separator(left_panel, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Export settings
        ttk.Label(left_panel, text="Export Options", font=("Arial", 12, "bold")).pack(pady=5)
        ttk.Checkbutton(left_panel, text="Auto Export to Excel", 
                       variable=self.excel_export_enabled).pack(anchor=tk.W)
        
        ttk.Separator(left_panel, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Results display
        ttk.Label(left_panel, text="Detection Results", font=("Arial", 12, "bold")).pack(pady=5)
        
        # Results treeview
        self.results_tree = ttk.Treeview(left_panel, columns=("Type", "Data"), height=8)
        self.results_tree.heading("#0", text="ID")
        self.results_tree.heading("Type", text="Type")
        self.results_tree.heading("Data", text="Data")
        self.results_tree.column("#0", width=30)
        self.results_tree.column("Type", width=80)
        self.results_tree.column("Data", width=200)
        self.results_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Right panel for image display
        right_panel = ttk.Frame(self.image_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Image canvas
        self.image_canvas = tk.Canvas(right_panel, bg="gray")
        self.image_canvas.pack(fill=tk.BOTH, expand=True)
        
    def create_camera_tab(self):
        """Create the camera tab."""
        self.camera_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.camera_frame, text="Live Camera")
        
        # Left panel for controls
        left_panel = ttk.Frame(self.camera_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # Camera controls
        ttk.Label(left_panel, text="Camera Controls", font=("Arial", 12, "bold")).pack(pady=5)
        
        self.camera_button = ttk.Button(left_panel, text="Start Camera", command=self.toggle_camera)
        self.camera_button.pack(fill=tk.X, pady=2)
        
        # Camera selection
        ttk.Label(left_panel, text="Camera:").pack(anchor=tk.W, pady=(10, 0))
        self.camera_var = tk.StringVar()
        self.camera_combo = ttk.Combobox(left_panel, textvariable=self.camera_var, state="readonly")
        self.camera_combo.pack(fill=tk.X, pady=2)
        
        ttk.Button(left_panel, text="Refresh Cameras", command=self.refresh_cameras).pack(fill=tk.X, pady=2)
        
        ttk.Separator(left_panel, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Detection settings
        ttk.Label(left_panel, text="Detection Settings", font=("Arial", 12, "bold")).pack(pady=5)
        
        self.continuous_detection = tk.BooleanVar(value=True)
        ttk.Checkbutton(left_panel, text="Continuous Detection", 
                       variable=self.continuous_detection).pack(anchor=tk.W)
        
        ttk.Checkbutton(left_panel, text="Auto Export to Excel", 
                       variable=self.excel_export_enabled).pack(anchor=tk.W)
        
        ttk.Separator(left_panel, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Live results
        ttk.Label(left_panel, text="Live Results", font=("Arial", 12, "bold")).pack(pady=5)
        self.live_results_text = scrolledtext.ScrolledText(left_panel, height=10, width=30)
        self.live_results_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Right panel for camera display
        right_panel = ttk.Frame(self.camera_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Camera canvas
        self.camera_canvas = tk.Canvas(right_panel, bg="black")
        self.camera_canvas.pack(fill=tk.BOTH, expand=True)
    
    def open_image(self):
        """Open an image file."""
        filename = filedialog.askopenfilename(
            title="Open Image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.gif"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            try:
                self.current_image = cv2.imread(filename)
                if self.current_image is not None:
                    self.display_image(self.current_image)
                    self.update_status(f"Loaded: {os.path.basename(filename)}")
                else:
                    messagebox.showerror("Error", "Could not load image file")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {e}")
    
    def process_image(self):
        """Process the current image for barcode/QR detection."""
        if self.current_image is None:
            messagebox.showwarning("Warning", "Please open an image first")
            return
        
        try:
            self.update_status("Processing image...")
            
            # Detect codes
            results = self.detector.detect_codes(self.current_image)
            self.current_results = results
            
            # Draw detections on image
            annotated_image = self.detector.draw_detections(self.current_image, results)
            self.display_image(annotated_image)
            
            # Update results display
            self.update_results_display(results)
            
            # Auto export to Excel if enabled
            if self.excel_export_enabled.get() and results:
                self.save_to_excel(results, "image_processing")
            
            self.update_status(f"Found {len(results)} code(s)")
            
        except Exception as e:
            messagebox.showerror("Error", f"Processing failed: {e}")
            self.update_status("Processing failed")
    
    def display_image(self, image):
        """Display an image on the canvas."""
        try:
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_image)
            
            # Resize to fit canvas
            canvas_width = self.image_canvas.winfo_width()
            canvas_height = self.image_canvas.winfo_height()
            
            if canvas_width > 1 and canvas_height > 1:
                pil_image.thumbnail((canvas_width, canvas_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage and display
            self.photo = ImageTk.PhotoImage(pil_image)
            self.image_canvas.delete("all")
            self.image_canvas.create_image(
                canvas_width // 2, canvas_height // 2, 
                anchor=tk.CENTER, image=self.photo
            )
            
        except Exception as e:
            print(f"Error displaying image: {e}")
    
    def update_results_display(self, results):
        """Update the results tree view."""
        # Clear existing items
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # Add new results
        for i, result in enumerate(results):
            data_preview = result.data[:50] + "..." if len(result.data) > 50 else result.data
            self.results_tree.insert("", tk.END, text=str(i+1), values=(result.type, data_preview))
    
    def toggle_camera(self):
        """Toggle camera on/off."""
        if not self.camera_active:
            self.start_camera()
        else:
            self.stop_camera()
    
    def start_camera(self):
        """Start camera capture."""
        try:
            if not self.camera_manager.has_available_cameras():
                messagebox.showwarning("No Cameras", "No cameras detected")
                return
            
            camera_text = self.camera_var.get()
            if not camera_text or "No cameras" in camera_text:
                messagebox.showwarning("Warning", "Please select a camera")
                return
            
            # Extract camera index
            camera_index = int(camera_text.split(":")[0])
            self.camera_manager.camera_index = camera_index
            
            if self.camera_manager.initialize_camera():
                self.camera_manager.start_capture(self.camera_frame_callback)
                self.camera_active = True
                self.camera_button.config(text="Stop Camera")
                self.update_status(f"Camera {camera_index} started")
            else:
                messagebox.showerror("Error", f"Failed to start camera {camera_index}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Camera error: {e}")
    
    def stop_camera(self):
        """Stop camera capture."""
        self.camera_manager.stop_capture()
        self.camera_active = False
        self.camera_button.config(text="Start Camera")
        self.camera_canvas.delete("all")
        self.update_status("Camera stopped")
    
    def camera_frame_callback(self, frame):
        """Process camera frames to detect multiple codes simultaneously."""
        try:
            if self.continuous_detection.get():
                # Detect codes in the frame
                results, annotated_frame = self.detector.detect_in_video_frame(frame)
                
                if results:
                    # Display detection results in the UI
                    self.update_live_results(results)
                    
                    # Auto export to Excel if enabled
                    if self.excel_export_enabled.get():
                        # Save all detected codes to Excel
                        self.save_to_excel(results, "live_camera")
                        
                        # Update status to show how many codes were detected
                        if len(results) > 1:
                            self.update_status(f"Multiple codes detected: {len(results)} items saved to Excel")
                            # Show performance stats in console for debugging
                            print(f"MULTI-DETECTION: {len(results)} codes detected and saved to Excel")
                        else:
                            self.update_status(f"Detected {len(results)} code and saved to Excel")
            else:
                annotated_frame = frame
            
            # Display frame with all detections highlighted
            self.display_camera_frame(annotated_frame)
            
        except Exception as e:
            print(f"Camera frame error: {e}")
    
    def display_camera_frame(self, frame):
        """Display camera frame."""
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_frame)
            
            canvas_width = self.camera_canvas.winfo_width()
            canvas_height = self.camera_canvas.winfo_height()
            
            if canvas_width > 1 and canvas_height > 1:
                pil_image = pil_image.resize((canvas_width, canvas_height), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(pil_image)
            self.camera_canvas.delete("all")
            self.camera_canvas.create_image(0, 0, anchor=tk.NW, image=photo)
            self.camera_canvas.image = photo
            
        except Exception as e:
            print(f"Camera display error: {e}")
    
    def update_live_results(self, results):
        """Update live results display with all detected codes."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # If multiple codes detected in one frame, show them with a special marker
        if len(results) > 1:
            self.live_results_text.insert(tk.END, f"[{timestamp}] MULTI-DETECTION: {len(results)} codes\n")
        
        # Add each detected code separately
        for i, result in enumerate(results):
            if len(results) > 1:
                # For multiple detections, number them for clarity
                result_text = f"  #{i+1}: {result.type}: {result.data[:30]}...\n"
            else:
                result_text = f"[{timestamp}] {result.type}: {result.data[:30]}...\n"
                
            self.live_results_text.insert(tk.END, result_text)
        
        # Add a blank line after multiple detections for readability
        if len(results) > 1:
            self.live_results_text.insert(tk.END, "\n")
            
        # Ensure the most recent results are visible
        self.live_results_text.see(tk.END)
        
        # Keep only last 100 lines
        lines = self.live_results_text.get(1.0, tk.END).split('\n')
        if len(lines) > 100:
            self.live_results_text.delete(1.0, tk.END)
            self.live_results_text.insert(1.0, '\n'.join(lines[-100:]))
    
    def refresh_cameras(self):
        """Refresh camera list."""
        self.update_status("Checking cameras...")
        
        cameras = self.camera_manager.list_available_cameras()
        
        if cameras:
            camera_list = [f"{i}: Camera {i}" for i in cameras]
            self.camera_combo['values'] = camera_list
            self.camera_combo.current(0)
            self.camera_button.config(state='normal')
            self.update_status(f"Found {len(cameras)} camera(s)")
        else:
            self.camera_combo['values'] = ["No cameras available"]
            self.camera_combo.set("No cameras available")
            self.camera_button.config(state='disabled')
            self.update_status("No cameras detected")
    
    def save_to_excel(self, results, source_type):
        """Save all detected results to Excel file."""
        try:
            if not results:
                return
            
            # Get current timestamp for all results in this batch
            timestamp = datetime.now().isoformat()
            
            # Add all results to the exporter
            self.exporter.add_results(results, source_type, timestamp)
            
            # Export everything to Excel
            success = self.exporter.export_to_excel(self.excel_file_path)
            
            if success:
                # Update status bar with count of codes saved
                if len(results) > 1:
                    # For multiple detections, make it more obvious in the UI
                    self.update_status(f"MULTIPLE CODES: Saved {len(results)} detections to Excel")
                    
                    # Update detection count in status bar for immediate feedback
                    total = len(self.exporter.results_history)
                    self.detection_count_label.config(text=f"Total Detections: {total}")
                else:
                    self.update_status(f"Saved {len(results)} detection to Excel")
            else:
                print("Excel export failed")
                
        except Exception as e:
            print(f"Excel save error: {e}")
    
    def change_excel_path(self):
        """Change Excel file path."""
        new_path = filedialog.asksaveasfilename(
            title="Choose Excel file location",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialdir="exports"
        )
        
        if new_path:
            self.excel_file_path = new_path
            self.excel_path_var.set(new_path)
            self.update_status(f"Excel path changed")
    
    def open_excel_file(self):
        """Open Excel file."""
        try:
            if os.path.exists(self.excel_file_path):
                os.startfile(self.excel_file_path)
                self.update_status("Opened Excel file")
            else:
                messagebox.showinfo("Info", "No Excel file created yet. Process some images first.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open Excel file: {e}")
    
    def clear_excel_data(self):
        """Clear Excel data."""
        result = messagebox.askyesno("Confirm", "Clear all Excel data?")
        if result:
            try:
                if os.path.exists(self.excel_file_path):
                    os.remove(self.excel_file_path)
                self.exporter.clear_history()
                self.update_status("Excel data cleared")
                messagebox.showinfo("Success", "Excel data cleared")
            except Exception as e:
                messagebox.showerror("Error", f"Could not clear Excel data: {e}")
    
    def update_system_info(self):
        """Update system information display."""
        try:
            info = []
            info.append("=== SYSTEM INFORMATION ===")
            info.append("")
            info.append("Core Components:")
            info.append(f"✓ OpenCV Detection Engine")
            info.append(f"✓ Camera Manager")
            info.append(f"✓ Excel Export System")
            info.append("")
            
            info.append("Export Settings:")
            info.append(f"Excel Export: {'Enabled' if self.excel_export_enabled.get() else 'Disabled'}")
            info.append(f"Excel File: {self.excel_file_path}")
            info.append("")
            
            # Detection statistics
            stats = self.exporter.get_statistics()
            info.append("Detection Statistics:")
            info.append(f"Total Detections: {stats.get('Total Detections', 0)}")
            info.append("")
            
            info.append("Camera Status:")
            cameras = self.camera_manager.list_available_cameras()
            info.append(f"Available Cameras: {len(cameras)}")
            info.append(f"Camera Active: {'Yes' if self.camera_active else 'No'}")
            
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(1.0, '\n'.join(info))
            
        except Exception as e:
            print(f"System info error: {e}")
    
    def update_status(self, message):
        """Update status bar."""
        self.status_label.config(text=message)
        
        # Update detection count
        total_detections = len(self.exporter.results_history)
        self.detection_count_label.config(text=f"Total Detections: {total_detections}")
        
        # Update system info if on settings tab
        if self.notebook.index("current") == 2:  # Settings tab
            self.update_system_info()

    def run(self):
        """Start the main application loop."""
        try:
            self.root.mainloop()
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources."""
        try:
            if self.camera_active:
                self.camera_manager.stop_capture()
                self.camera_active = False
            
            if hasattr(self, 'performance_monitor'):
                self.performance_monitor.stop_monitoring()
        except Exception as e:
            print(f"Error during cleanup: {e}")
