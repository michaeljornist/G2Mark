"""
Utilities module for the G2burn Laser Engraving Application.
This module contains common utility functions and constants.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Tuple
import tkinter as tk
from tkinter import messagebox


class Constants:
    """Application constants."""
    
    # File extensions
    GCODE_EXTENSIONS = [".gcode", ".nc", ".txt"]
    IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"]
    PROJECT_EXTENSION = ".g2mark"
    
    # Default values
    DEFAULT_FEED_RATE = 1000  # mm/min
    DEFAULT_LASER_POWER = 255  # 0-255
    DEFAULT_TRAVEL_SPEED = 3000  # mm/min
    DEFAULT_BEAM_DIAMETER = 0.072  # mm
    
    # UI constants
    BUTTON_WIDTH = 10
    MENU_HEIGHT = 40
    STATUS_HEIGHT = 25
    
    # Colors
    WORK_AREA_BG = "white"
    CANVAS_BG = "#303030"
    MENU_BG = "#f0f0f0"
    GRID_COLOR = "lightgray"
    BORDER_COLOR = "black"
    RULER_BG = "#f0f0f0"


class FileManager:
    """Handles file operations for the application."""
    
    @staticmethod
    def save_project(project_data: Dict, file_path: str) -> bool:
        """Save project data to a file.
        
        Args:
            project_data (Dict): Project data to save
            file_path (str): Path to save the file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Add metadata
            save_data = {
                "metadata": {
                    "version": "1.0",
                    "created": datetime.now().isoformat(),
                    "application": "G2burn Laser Engraver"
                },
                "project": project_data
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2)
                
            return True
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save project:\n{str(e)}")
            return False
            
    @staticmethod
    def load_project(file_path: str) -> Dict:
        """Load project data from a file.
        
        Args:
            file_path (str): Path to the project file
            
        Returns:
            Dict: Project data, empty dict if failed
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
                
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Extract project data (handle both old and new formats)
            if "project" in data:
                return data["project"]
            else:
                return data  # Legacy format
                
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load project:\n{str(e)}")
            return {}
            
    @staticmethod
    def get_project_files(directory: str) -> List[str]:
        """Get list of project files in a directory.
        
        Args:
            directory (str): Directory to search
            
        Returns:
            List[str]: List of project file paths
        """
        if not os.path.exists(directory):
            return []
            
        project_files = []
        for file in os.listdir(directory):
            if file.endswith(Constants.PROJECT_EXTENSION):
                project_files.append(os.path.join(directory, file))
                
        return sorted(project_files)


class GeometryUtils:
    """Utility functions for geometric calculations."""
    
    @staticmethod
    def distance_between_points(x1: float, y1: float, x2: float, y2: float) -> float:
        """Calculate distance between two points.
        
        Args:
            x1, y1: First point coordinates
            x2, y2: Second point coordinates
            
        Returns:
            float: Distance between points
        """
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        
    @staticmethod
    def point_in_rectangle(px: float, py: float, rx: float, ry: float, 
                          width: float, height: float) -> bool:
        """Check if a point is inside a rectangle.
        
        Args:
            px, py: Point coordinates
            rx, ry: Rectangle top-left corner
            width, height: Rectangle dimensions
            
        Returns:
            bool: True if point is inside rectangle
        """
        return (rx <= px <= rx + width and ry <= py <= ry + height)
        
    @staticmethod
    def normalize_rectangle(x1: float, y1: float, x2: float, y2: float) -> Tuple[float, float, float, float]:
        """Normalize rectangle coordinates to ensure min/max order.
        
        Args:
            x1, y1: First corner
            x2, y2: Second corner
            
        Returns:
            Tuple[float, float, float, float]: (min_x, min_y, max_x, max_y)
        """
        min_x = min(x1, x2)
        max_x = max(x1, x2)
        min_y = min(y1, y2)
        max_y = max(y1, y2)
        return min_x, min_y, max_x, max_y
        
    @staticmethod
    def calculate_bounding_box(points: List[Tuple[float, float]]) -> Tuple[float, float, float, float]:
        """Calculate bounding box for a set of points.
        
        Args:
            points: List of (x, y) coordinate tuples
            
        Returns:
            Tuple[float, float, float, float]: (min_x, min_y, max_x, max_y)
        """
        if not points:
            return 0, 0, 0, 0
            
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        
        return min(x_coords), min(y_coords), max(x_coords), max(y_coords)


class UIUtils:
    """Utility functions for UI operations."""
    
    @staticmethod
    def center_window(window: tk.Toplevel, width: int, height: int):
        """Center a window on the screen.
        
        Args:
            window: Window to center
            width: Window width
            height: Window height
        """
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")
        
    @staticmethod
    def show_info(title: str, message: str):
        """Show an info dialog.
        
        Args:
            title: Dialog title
            message: Dialog message
        """
        messagebox.showinfo(title, message)
        
    @staticmethod
    def show_warning(title: str, message: str):
        """Show a warning dialog.
        
        Args:
            title: Dialog title
            message: Dialog message
        """
        messagebox.showwarning(title, message)
        
    @staticmethod
    def show_error(title: str, message: str):
        """Show an error dialog.
        
        Args:
            title: Dialog title
            message: Dialog message
        """
        messagebox.showerror(title, message)
        
    @staticmethod
    def ask_yes_no(title: str, message: str) -> bool:
        """Show a yes/no dialog.
        
        Args:
            title: Dialog title
            message: Dialog message
            
        Returns:
            bool: True if yes, False if no
        """
        return messagebox.askyesno(title, message)
        
    @staticmethod
    def create_tooltip(widget: tk.Widget, text: str):
        """Add a tooltip to a widget.
        
        Args:
            widget: Widget to add tooltip to
            text: Tooltip text
        """
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tooltip, text=text, background="lightyellow", 
                           relief="solid", borderwidth=1, font=("Arial", 9))
            label.pack()
            widget.tooltip = tooltip
            
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
                
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)


class ValidationUtils:
    """Utility functions for input validation."""
    
    @staticmethod
    def is_valid_float(value: str) -> bool:
        """Check if a string represents a valid float.
        
        Args:
            value: String to validate
            
        Returns:
            bool: True if valid float
        """
        try:
            float(value)
            return True
        except ValueError:
            return False
            
    @staticmethod
    def is_valid_positive_float(value: str) -> bool:
        """Check if a string represents a valid positive float.
        
        Args:
            value: String to validate
            
        Returns:
            bool: True if valid positive float
        """
        try:
            num = float(value)
            return num > 0
        except ValueError:
            return False
            
    @staticmethod
    def is_valid_int(value: str) -> bool:
        """Check if a string represents a valid integer.
        
        Args:
            value: String to validate
            
        Returns:
            bool: True if valid integer
        """
        try:
            int(value)
            return True
        except ValueError:
            return False
            
    @staticmethod
    def is_valid_positive_int(value: str) -> bool:
        """Check if a string represents a valid positive integer.
        
        Args:
            value: String to validate
            
        Returns:
            bool: True if valid positive integer
        """
        try:
            num = int(value)
            return num > 0
        except ValueError:
            return False
            
    @staticmethod
    def validate_project_name(name: str) -> Tuple[bool, str]:
        """Validate a project name.
        
        Args:
            name: Project name to validate
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if not name or not name.strip():
            return False, "Project name cannot be empty"
            
        # Check for invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            if char in name:
                return False, f"Project name cannot contain '{char}'"
                
        if len(name.strip()) > 255:
            return False, "Project name is too long (max 255 characters)"
            
        return True, ""


class MathUtils:
    """Mathematical utility functions."""
    
    @staticmethod
    def clamp(value: float, min_val: float, max_val: float) -> float:
        """Clamp a value between min and max.
        
        Args:
            value: Value to clamp
            min_val: Minimum value
            max_val: Maximum value
            
        Returns:
            float: Clamped value
        """
        return max(min_val, min(value, max_val))
        
    @staticmethod
    def lerp(start: float, end: float, t: float) -> float:
        """Linear interpolation between two values.
        
        Args:
            start: Start value
            end: End value
            t: Interpolation factor (0.0 to 1.0)
            
        Returns:
            float: Interpolated value
        """
        return start + (end - start) * t
        
    @staticmethod
    def round_to_precision(value: float, precision: int = 3) -> float:
        """Round a value to specified decimal places.
        
        Args:
            value: Value to round
            precision: Number of decimal places
            
        Returns:
            float: Rounded value
        """
        return round(value, precision)


class Logger:
    """Simple logging utility."""
    
    def __init__(self, name: str = "G2burn"):
        """Initialize logger.
        
        Args:
            name: Logger name
        """
        self.name = name
        self.enabled = True
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message.
        
        Args:
            message: Message to log
            level: Log level
        """
        if self.enabled:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {self.name} {level}: {message}")
            
    def info(self, message: str):
        """Log an info message."""
        self.log(message, "INFO")
        
    def warning(self, message: str):
        """Log a warning message."""
        self.log(message, "WARNING")
        
    def error(self, message: str):
        """Log an error message."""
        self.log(message, "ERROR")
        
    def set_enabled(self, enabled: bool):
        """Enable or disable logging."""
        self.enabled = enabled


# Global logger instance
logger = Logger()


def format_time_duration(seconds: float) -> str:
    """Format a duration in seconds to a human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        str: Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def get_file_size_string(size_bytes: int) -> str:
    """Convert file size in bytes to human-readable string.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        str: Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
