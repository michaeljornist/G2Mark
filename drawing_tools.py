"""
Drawing tools manager for the G2burn Laser Engraving Application.
This module manages different drawing tools and their interactions.
"""

import tkinter as tk
import math
from abc import ABC, abstractmethod
from PIL import Image, ImageTk


class ToolTip:
    """Simple tooltip class for buttons."""
    
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
    
    def on_enter(self, event=None):
        """Show tooltip when mouse enters widget."""
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 25
        
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(
            self.tooltip_window,
            text=self.text,
            background="lightyellow",
            relief="solid",
            borderwidth=1,
            font=("Arial", 9)
        )
        label.pack()
    
    def on_leave(self, event=None):
        """Hide tooltip when mouse leaves widget."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class DrawingTool(ABC):
    """Abstract base class for drawing tools."""
    
    def __init__(self, canvas, sketching_stage):
        """Initialize the drawing tool.
        
        Args:
            canvas (tk.Canvas): The canvas to draw on
            sketching_stage (SketchingStage): Reference to the sketching stage
        """
        self.canvas = canvas
        self.sketching_stage = sketching_stage
        self.is_active = False
        
        # Snap settings
        self.snap_enabled = True
        self.snap_radius_mm = 2.0  # Snap radius in millimeters
        self.snap_radius_pixels = 10  # Will be calculated based on zoom
        
    def _update_snap_radius(self):
        """Update snap radius in pixels based on current zoom level."""
        self.snap_radius_pixels = self.snap_radius_mm * self.sketching_stage.zoom_level
        
    def _find_nearest_reference_point(self, canvas_x, canvas_y):
        """Find the nearest reference point within snap radius.
        
        Args:
            canvas_x (float): Mouse X position in canvas coordinates
            canvas_y (float): Mouse Y position in canvas coordinates
            
        Returns:
            tuple: (snap_x, snap_y) if point found, None otherwise
        """
        self._update_snap_radius()
        
        # Get work area bounds for coordinate conversion
        x1, y1, _, _ = self.sketching_stage.get_work_area_bounds()
        
        nearest_point = None
        min_distance = float('inf')
        
        # Search through all drawing objects for reference points
        for drawing_obj in self.sketching_stage.drawing_objects:
            if drawing_obj['type'] == 'reference_point':
                real_coords = drawing_obj['real_coords']
                
                # Convert real coordinates to canvas coordinates
                ref_canvas_x = x1 + (real_coords[0] * self.sketching_stage.zoom_level)
                ref_canvas_y = y1 + (real_coords[1] * self.sketching_stage.zoom_level)
                
                # Calculate distance
                distance = ((canvas_x - ref_canvas_x) ** 2 + (canvas_y - ref_canvas_y) ** 2) ** 0.5
                
                # Check if within snap radius and closer than previous points
                if distance <= self.snap_radius_pixels and distance < min_distance:
                    min_distance = distance
                    nearest_point = (ref_canvas_x, ref_canvas_y)
                    
        return nearest_point
        
    def _apply_snap(self, canvas_x, canvas_y):
        """Apply snapping to mouse coordinates if near a reference point.
        
        Args:
            canvas_x (float): Original mouse X position
            canvas_y (float): Original mouse Y position
            
        Returns:
            tuple: (snapped_x, snapped_y) coordinates
        """
        if not self.snap_enabled:
            return canvas_x, canvas_y
            
        snap_point = self._find_nearest_reference_point(canvas_x, canvas_y)
        if snap_point:
            return snap_point
        else:
            return canvas_x, canvas_y
            
    def _draw_snap_indicator(self, canvas_x, canvas_y):
        """Draw a visual indicator when snapping to a point.
        
        Args:
            canvas_x (float): Snap point X coordinate
            canvas_y (float): Snap point Y coordinate
        """
        # Remove previous snap indicator
        self.canvas.delete("snap_indicator")
        
        # Draw snap indicator circle
        radius = 5
        self.canvas.create_oval(
            canvas_x - radius, canvas_y - radius,
            canvas_x + radius, canvas_y + radius,
            outline="red", width=2, tags="snap_indicator temp"
        )
        
    @abstractmethod
    def activate(self):
        """Activate this drawing tool."""
        pass
        
    @abstractmethod
    def deactivate(self):
        """Deactivate this drawing tool."""
        pass
        
    @abstractmethod
    def get_cursor(self):
        """Get the cursor for this tool."""
        pass
        
    @abstractmethod
    def get_status_text(self):
        """Get the status text for this tool."""
        pass


class SelectTool(DrawingTool):
    """Tool for selecting and manipulating objects."""
    
    def activate(self):
        """Activate the select tool."""
        self.is_active = True
        self.canvas.config(cursor="")
        
        # Clear any existing bindings
        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")
        
    def deactivate(self):
        """Deactivate the select tool."""
        self.is_active = False
        
    def get_cursor(self):
        """Get the cursor for this tool."""
        return ""
        
    def get_status_text(self):
        """Get the status text for this tool."""
        return "Select - Click to select objects"


class LineTool(DrawingTool):
    """Tool for drawing lines."""
    
    def __init__(self, canvas, sketching_stage):
        """Initialize the line tool."""
        super().__init__(canvas, sketching_stage)
        self.is_first_click = True
        self.start_x = 0
        self.start_y = 0
        self.preview_line_id = None
        
        # Line information
        self.line_length_mm = 0.0
        self.line_angle_deg = 0.0
        self.line_width_mm = 0.1  # Default 0.1mm width for laser cutting
        self.current_mm_x = 0.0
        self.current_mm_y = 0.0
        
        # Line info display
        self.line_info_id = None
        
        # Edit mode
        self.edit_mode = None  # None, 'length', 'angle', or 'width'
        self.edit_value = ""  # String for editing
        self.info_display_id = None
        
    def activate(self):
        """Activate the line tool."""
        self.is_active = True
        self.is_first_click = True
        self.canvas.config(cursor="crosshair")
        
        # Clear any existing bindings
        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")
        self.canvas.unbind("<Tab>")
        self.canvas.unbind("<Return>")
        self.canvas.unbind("<Escape>")
        self.canvas.unbind("<Key>")
        
        # Bind events for line drawing
        self.canvas.bind("<Button-1>", self._handle_click)
        
        # Keyboard event bindings for editing line properties
        self.canvas.bind("<Tab>", self._handle_tab)
        self.canvas.bind("<Return>", self._handle_enter)
        self.canvas.bind("<Escape>", self._handle_escape)
        self.canvas.bind("<Key>", self._handle_key)
        
        # Preserve the original motion handler for coordinate tracking
        original_motion = self.canvas.bind("<Motion>")
        self.canvas.bind("<Motion>", lambda e: self._handle_motion(e, original_motion))
        
    def deactivate(self):
        """Deactivate the line tool."""
        self.is_active = False
        self.canvas.delete("temp")
        self.canvas.delete("snap_indicator")
        self.canvas.delete("line_info")
        self.is_first_click = True
        self.preview_line_id = None
        self.line_info_id = None
        self.edit_mode = None
        self.edit_value = ""
        
        # Unbind keyboard events
        self.canvas.unbind("<Tab>")
        self.canvas.unbind("<Return>")
        self.canvas.unbind("<Escape>")
        self.canvas.unbind("<Key>")
        
    def get_cursor(self):
        """Get the cursor for this tool."""
        return "crosshair"
        
    def get_status_text(self):
        """Get the status text for this tool."""
        return "Drawing Line - Click to place points"
        
    def _handle_click(self, event):
        """Handle mouse clicks for line drawing."""
        # Only draw if clicking within work area
        if not self.sketching_stage.is_point_in_work_area(event.x, event.y):
            return
            
        # Apply snapping to click position
        snapped_x, snapped_y = self._apply_snap(event.x, event.y)
            
        if self.is_first_click:
            # First click: Store starting point
            self.start_x, self.start_y = snapped_x, snapped_y
            
            # Create a temporary point marker
            self.canvas.create_oval(
                self.start_x-3, self.start_y-3, 
                self.start_x+3, self.start_y+3, 
                fill="gray", outline="black", tags="temp"
            )
            
            self.is_first_click = False
            
        else:
            # Second click: Use the finish line method
            # Set the final coordinates for calculations
            final_x, final_y = self._apply_snap(event.x, event.y)
            self._calculate_line_info(final_x, final_y)
            self._finish_line()
            
    def _handle_motion(self, event, original_handler):
        """Handle mouse motion for line preview."""
        # Apply snapping to motion coordinates
        snapped_x, snapped_y = self._apply_snap(event.x, event.y)
        
        # Show snap indicator if we're snapping
        if (snapped_x, snapped_y) != (event.x, event.y):
            self._draw_snap_indicator(snapped_x, snapped_y)
        else:
            self.canvas.delete("snap_indicator")
        
        # Update line preview with snapped coordinates
        self._update_preview(snapped_x, snapped_y)
        
        # Call original motion handler for coordinate tracking
        if original_handler and hasattr(self.sketching_stage, '_update_coordinates'):
            # Create a mock event with snapped coordinates for accurate display
            mock_event = type('MockEvent', (), {'x': snapped_x, 'y': snapped_y})()
            self.sketching_stage._update_coordinates(mock_event)
            
    def _update_preview(self, x, y):
        """Update the preview line as mouse moves.
        
        Args:
            x (float): X coordinate (potentially snapped)
            y (float): Y coordinate (potentially snapped)
        """
        # Only show preview if waiting for second click
        if not self.is_first_click:
            # Delete previous preview line and info
            if self.preview_line_id:
                self.canvas.delete(self.preview_line_id)
                
            # Calculate display width based on zoom level
            display_width = max(1, int(self.line_width_mm * self.sketching_stage.zoom_level))
            
            # Create new preview line with proper width
            self.preview_line_id = self.canvas.create_line(
                self.start_x, self.start_y, x, y, 
                fill="gray", width=display_width, dash=(4, 2), tags="temp"
            )
            
            # Calculate line length and angle
            self._calculate_line_info(x, y)
            
            # Show line information
            self._update_line_info_display()
            
    def _update_preview_with_width(self):
        """Update the preview line with new width."""
        if not self.is_first_click and self.preview_line_id:
            # Get current preview coordinates
            coords = self.canvas.coords(self.preview_line_id)
            if len(coords) >= 4:
                # Delete old preview
                self.canvas.delete(self.preview_line_id)
                
                # Calculate display width based on zoom level
                display_width = max(1, int(self.line_width_mm * self.sketching_stage.zoom_level))
                
                # Create new preview with updated width
                self.preview_line_id = self.canvas.create_line(
                    coords[0], coords[1], coords[2], coords[3], 
                    fill="gray", width=display_width, dash=(4, 2), tags="temp"
                )
            
    def _calculate_line_info(self, end_x, end_y):
        """Calculate length and angle of the current line.
        
        Args:
            end_x (float): Current end X coordinate
            end_y (float): Current end Y coordinate
        """
        # Convert canvas coordinates to real mm coordinates
        start_mm_x, start_mm_y = self.sketching_stage.canvas_to_mm(self.start_x, self.start_y)
        self.current_mm_x, self.current_mm_y = self.sketching_stage.canvas_to_mm(end_x, end_y)
        
        # Calculate length in mm
        dx = self.current_mm_x - start_mm_x
        dy = self.current_mm_y - start_mm_y
        self.line_length_mm = (dx**2 + dy**2)**0.5
        
        # Calculate angle in degrees
        if dx == 0:
            # Vertical line
            self.line_angle_deg = 90 if dy < 0 else 270
        else:
            # Calculate the angle from horizontal
            angle_rad = math.atan2(-dy, dx)  # Negative dy because canvas y is inverted
            self.line_angle_deg = math.degrees(angle_rad)
            
        # Normalize angle to 0-360 degrees
        self.line_angle_deg = (self.line_angle_deg + 360) % 360
        
    def _update_line_info_display(self):
        """Update or create the line information display."""
        # Remove existing info display
        self.canvas.delete("line_info")
        
        # Set display text based on edit mode
        if self.edit_mode == 'length':
            length_text = self.edit_value + "▋"  # Add cursor
            angle_text = f"Angle: {self.line_angle_deg:.1f}°"
            width_text = f"Width: {self.line_width_mm:.2f}mm"
        elif self.edit_mode == 'angle':
            length_text = f"Length: {self.line_length_mm:.1f}mm"
            angle_text = self.edit_value + "▋"  # Add cursor
            width_text = f"Width: {self.line_width_mm:.2f}mm"
        elif self.edit_mode == 'width':
            length_text = f"Length: {self.line_length_mm:.1f}mm"
            angle_text = f"Angle: {self.line_angle_deg:.1f}°"
            width_text = self.edit_value + "▋"  # Add cursor
        else:
            length_text = f"Length: {self.line_length_mm:.1f}mm"
            angle_text = f"Angle: {self.line_angle_deg:.1f}°"
            width_text = f"Width: {self.line_width_mm:.2f}mm"
        
        # Status text with instructions
        status_text = "Tab: Edit values | Enter: Confirm | Esc: Cancel"
        
        # Calculate position for the info display (center bottom of canvas)
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        x_pos = canvas_width // 2
        y_pos = canvas_height - 50  # Slightly higher for 3 lines
        
        # Create text items
        self.info_display_id = self.canvas.create_text(
            x_pos, y_pos, 
            text=f"{length_text}   {angle_text}   {width_text}\n{status_text}",
            fill="black", font=("Arial", 10), justify=tk.CENTER,
            tags="line_info temp"
        )
        
        # Create background rectangle for better visibility
        bbox = self.canvas.bbox(self.info_display_id)
        if bbox:
            padding = 10
            self.canvas.create_rectangle(
                bbox[0] - padding, bbox[1] - padding,
                bbox[2] + padding, bbox[3] + padding,
                fill="lightyellow", outline="gray",
                tags="line_info temp"
            )
            # Move text to front
            self.canvas.tag_raise(self.info_display_id)
            self.canvas.tag_raise(self.info_display_id)
    
    def _handle_tab(self, event):
        """Handle tab key press to switch between editing modes."""
        if not self.is_first_click:  # Only when drawing a line
            if self.edit_mode is None:
                # Enter length edit mode
                self.edit_mode = 'length'
                self.edit_value = f"{self.line_length_mm:.1f}"
            elif self.edit_mode == 'length':
                # Switch to angle edit mode
                self.edit_mode = 'angle'
                self.edit_value = f"{self.line_angle_deg:.1f}"
            elif self.edit_mode == 'angle':
                # Switch to width edit mode
                self.edit_mode = 'width'
                self.edit_value = f"{self.line_width_mm:.2f}"
            elif self.edit_mode == 'width':
                # Back to length edit mode
                self.edit_mode = 'length'
                self.edit_value = f"{self.line_length_mm:.1f}"
                
            self._update_line_info_display()
            return "break"  # Prevent default tab behavior
        
    def _handle_enter(self, event):
        """Handle enter key press to confirm edits or create line."""
        if not self.is_first_click:  # Only when drawing a line
            if self.edit_mode == 'length':
                # Apply length change
                try:
                    new_length = float(self.edit_value)
                    if new_length > 0:
                        self._apply_new_length(new_length)
                except ValueError:
                    pass  # Invalid input, ignore
                    
                # Switch to angle edit mode
                self.edit_mode = 'angle'
                self.edit_value = f"{self.line_angle_deg:.1f}"
                self._update_line_info_display()
                
            elif self.edit_mode == 'angle':
                # Apply angle change
                try:
                    new_angle = float(self.edit_value)
                    self._apply_new_angle(new_angle)
                except ValueError:
                    pass  # Invalid input, ignore
                    
                # Switch to width edit mode
                self.edit_mode = 'width'
                self.edit_value = f"{self.line_width_mm:.2f}"
                self._update_line_info_display()
                
            elif self.edit_mode == 'width':
                # Apply width change
                try:
                    new_width = float(self.edit_value)
                    if new_width > 0:
                        self.line_width_mm = new_width
                        self._update_preview_with_width()
                except ValueError:
                    pass  # Invalid input, ignore
                    
                # Exit edit mode
                self.edit_mode = None
                self._update_line_info_display()
                
            else:
                # Not in edit mode, create the line
                self._finish_line()
                
            return "break"  # Prevent default enter behavior
        
    def _handle_escape(self, event):
        """Handle escape key press to cancel edits or drawing."""
        if not self.is_first_click:  # Only when drawing a line
            if self.edit_mode:
                # Cancel edit mode
                self.edit_mode = None
                self._update_line_info_display()
            else:
                # Cancel line drawing
                self.canvas.delete("temp")
                self.canvas.delete("line_info")
                self.is_first_click = True
                self.preview_line_id = None
                
            return "break"  # Prevent default escape behavior
            
    def _handle_key(self, event):
        """Handle regular key presses during edit mode."""
        if self.edit_mode and not self.is_first_click:
            if event.keysym == 'BackSpace':
                # Handle backspace
                self.edit_value = self.edit_value[:-1] if self.edit_value else ""
            elif event.keysym in ('Right', 'Left', 'Up', 'Down'):
                # Ignore arrow keys
                pass
            elif event.char and (event.char.isdigit() or event.char in '.,-'):
                # Accept digits and decimal point for editing
                self.edit_value += event.char
                
            self._update_line_info_display()
            return "break"  # Prevent default key behavior
            
    def _apply_new_length(self, new_length):
        """Apply a new length to the line being drawn.
        
        Args:
            new_length (float): The new length in mm
        """
        # Get angle in radians
        angle_rad = math.radians(self.line_angle_deg)
        
        # Calculate new endpoint coordinates
        start_mm_x, start_mm_y = self.sketching_stage.canvas_to_mm(self.start_x, self.start_y)
        new_end_mm_x = start_mm_x + (new_length * math.cos(angle_rad))
        new_end_mm_y = start_mm_y - (new_length * math.sin(angle_rad))  # Subtract for canvas coordinates
        
        # Convert back to canvas coordinates
        x1, y1, _, _ = self.sketching_stage.get_work_area_bounds()
        new_end_canvas_x = x1 + (new_end_mm_x * self.sketching_stage.zoom_level)
        new_end_canvas_y = y1 + (new_end_mm_y * self.sketching_stage.zoom_level)
        
        # Update line length
        self.line_length_mm = new_length
        
        # Calculate display width based on zoom level
        display_width = max(1, int(self.line_width_mm * self.sketching_stage.zoom_level))
        
        # Update preview with real width
        self.canvas.delete(self.preview_line_id)
        self.preview_line_id = self.canvas.create_line(
            self.start_x, self.start_y, new_end_canvas_x, new_end_canvas_y,
            fill="gray", width=display_width, dash=(4, 2), tags="temp"
        )
        
    def _apply_new_angle(self, new_angle):
        """Apply a new angle to the line being drawn.
        
        Args:
            new_angle (float): The new angle in degrees
        """
        # Normalize angle
        new_angle = (new_angle + 360) % 360
        
        # Convert to radians
        angle_rad = math.radians(new_angle)
        
        # Calculate new endpoint coordinates
        start_mm_x, start_mm_y = self.sketching_stage.canvas_to_mm(self.start_x, self.start_y)
        new_end_mm_x = start_mm_x + (self.line_length_mm * math.cos(angle_rad))
        new_end_mm_y = start_mm_y - (self.line_length_mm * math.sin(angle_rad))  # Subtract for canvas coordinates
        
        # Convert back to canvas coordinates
        x1, y1, _, _ = self.sketching_stage.get_work_area_bounds()
        new_end_canvas_x = x1 + (new_end_mm_x * self.sketching_stage.zoom_level)
        new_end_canvas_y = y1 + (new_end_mm_y * self.sketching_stage.zoom_level)
        
        # Update line angle
        self.line_angle_deg = new_angle
        
        # Calculate display width based on zoom level
        display_width = max(1, int(self.line_width_mm * self.sketching_stage.zoom_level))
        
        # Update preview with real width
        self.canvas.delete(self.preview_line_id)
        self.preview_line_id = self.canvas.create_line(
            self.start_x, self.start_y, new_end_canvas_x, new_end_canvas_y,
            fill="gray", width=display_width, dash=(4, 2), tags="temp"
        )
        
    def _finish_line(self):
        """Finish line creation with current parameters."""
        # Calculate endpoint based on current length and angle
        angle_rad = math.radians(self.line_angle_deg)
        start_mm_x, start_mm_y = self.sketching_stage.canvas_to_mm(self.start_x, self.start_y)
        end_mm_x = start_mm_x + (self.line_length_mm * math.cos(angle_rad))
        end_mm_y = start_mm_y - (self.line_length_mm * math.sin(angle_rad))  # Subtract for canvas coordinates
        
        # Convert back to canvas coordinates
        x1, y1, _, _ = self.sketching_stage.get_work_area_bounds()
        end_canvas_x = x1 + (end_mm_x * self.sketching_stage.zoom_level)
        end_canvas_y = y1 + (end_mm_y * self.sketching_stage.zoom_level)
        
        # Calculate display width based on zoom level
        display_width = max(1, int(self.line_width_mm * self.sketching_stage.zoom_level))
        
        # Create the final line with real-world width
        self.canvas.create_line(
            self.start_x, self.start_y, end_canvas_x, end_canvas_y,
            fill="black", width=display_width, tags="drawing"
        )
        
        # Store the drawing object with width in mm
        self.sketching_stage.add_drawing_object(
            'line',
            [start_mm_x, start_mm_y, end_mm_x, end_mm_y],
            {'fill': 'black', 'width_mm': self.line_width_mm}
        )
        
        # Add reference points at the ends of the line
        self.sketching_stage.add_drawing_object(
            'reference_point',
            [start_mm_x, start_mm_y],
            {'color': 'blue'}
        )
        self.sketching_stage.add_drawing_object(
            'reference_point',
            [end_mm_x, end_mm_y],
            {'color': 'blue'}
        )
        
        # Clean up and reset
        self.canvas.delete("temp")
        self.canvas.delete("line_info")
        self.is_first_click = True
        self.preview_line_id = None
        self.edit_mode = None


class RectangleTool(DrawingTool):
    """Tool for drawing rectangles."""
    
    def __init__(self, canvas, sketching_stage):
        """Initialize the rectangle tool."""
        super().__init__(canvas, sketching_stage)
        self.is_first_click = True
        self.start_x = 0
        self.start_y = 0
        self.preview_rect_id = None
        self.info_display_id = None
        
        # Rectangle properties
        self.rect_width_mm = 10.0  # Default width in mm
        self.rect_height_mm = 10.0  # Default height in mm
        self.line_width_mm = 0.1  # Default line width in mm
        
        # Interactive editing properties
        self.edit_mode = None  # Can be 'width', 'height', 'line_width', or None
        self.edit_value = ""  # String representation of value being edited
        self.current_mm_x = 0  # Current end position
        self.current_mm_y = 0  # Current end position
        
    def activate(self):
        """Activate the rectangle tool."""
        self.is_active = True
        self.is_first_click = True
        self.canvas.config(cursor="crosshair")
        
        # Clear any existing bindings
        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")
        
        # Bind events for rectangle drawing (like line tool)
        self.canvas.bind("<Button-1>", self._handle_click)
        
        # Bind keyboard events for interactive editing
        self.canvas.focus_set()  # Allow canvas to receive keyboard events
        self.canvas.bind("<Tab>", self._handle_tab)
        self.canvas.bind("<Return>", self._handle_enter)
        self.canvas.bind("<Escape>", self._handle_escape)
        self.canvas.bind("<Key>", self._handle_key)
        
        # Preserve the original motion handler for coordinate tracking
        original_motion = self.canvas.bind("<Motion>")
        self.canvas.bind("<Motion>", lambda e: self._handle_motion(e, original_motion))
        
    def deactivate(self):
        """Deactivate the rectangle tool."""
        self.is_active = False
        self.canvas.delete("temp")
        self.canvas.delete("snap_indicator")
        self.canvas.delete("rect_info")
        self.is_first_click = True
        self.preview_rect_id = None
        self.info_display_id = None
        self.edit_mode = None
        self.edit_value = ""
        self.start_x = 0
        self.start_y = 0
        
        # Unbind keyboard events
        self.canvas.unbind("<Tab>")
        self.canvas.unbind("<Return>")
        self.canvas.unbind("<Escape>")
        self.canvas.unbind("<Key>")
        
    def get_cursor(self):
        """Get the cursor for this tool."""
        return "crosshair"
        
    def get_status_text(self):
        """Get the status text for this tool."""
        return "Drawing Rectangle - Click to place corners"
        
    def _handle_click(self, event):
        """Handle mouse clicks for rectangle drawing."""
        # Only draw if clicking within work area
        if not self.sketching_stage.is_point_in_work_area(event.x, event.y):
            return
            
        # Apply snapping to click position
        snapped_x, snapped_y = self._apply_snap(event.x, event.y)
            
        if self.is_first_click:
            # First click: Store starting corner
            self.start_x, self.start_y = snapped_x, snapped_y
            
            # Create a temporary point marker
            self.canvas.create_oval(
                self.start_x-3, self.start_y-3, 
                self.start_x+3, self.start_y+3, 
                fill="gray", outline="black", tags="temp"
            )
            
            self.is_first_click = False
            
        else:
            # Second click: Use the finish rectangle method
            # Set the final coordinates for calculations
            final_x, final_y = self._apply_snap(event.x, event.y)
            self._calculate_rect_info(final_x, final_y)
            self._finish_rectangle()
            
    def _handle_motion(self, event, original_handler):
        """Handle mouse motion for rectangle preview."""
        # Apply snapping to motion coordinates
        snapped_x, snapped_y = self._apply_snap(event.x, event.y)
        
        # Show snap indicator if we're snapping
        if (snapped_x, snapped_y) != (event.x, event.y):
            self._draw_snap_indicator(snapped_x, snapped_y)
        else:
            self.canvas.delete("snap_indicator")
        
        # Update rectangle preview with snapped coordinates
        self._update_preview(snapped_x, snapped_y)
        
        # Call original motion handler for coordinate tracking
        if original_handler and hasattr(self.sketching_stage, '_update_coordinates'):
            # Create a mock event with snapped coordinates for accurate display
            mock_event = type('MockEvent', (), {'x': snapped_x, 'y': snapped_y})()
            self.sketching_stage._update_coordinates(mock_event)
            
    def _update_preview(self, x, y):
        """Update the preview rectangle as mouse moves.
        
        Args:
            x (float): X coordinate (potentially snapped)
            y (float): Y coordinate (potentially snapped)
        """
        # Only show preview if waiting for second click
        if not self.is_first_click:
            # Delete previous preview rectangle
            if self.preview_rect_id:
                self.canvas.delete(self.preview_rect_id)
                
            # Calculate display width based on zoom level
            display_width = max(1, int(self.line_width_mm * self.sketching_stage.zoom_level))
                
            # Create new preview rectangle with proper line width
            self.preview_rect_id = self.canvas.create_rectangle(
                self.start_x, self.start_y, x, y, 
                outline="gray", width=display_width, dash=(4, 2), tags="temp"
            )
            
            # Calculate rectangle dimensions
            self._calculate_rect_info(x, y)
            
            # Show rectangle information
            self._update_rect_info_display()
            
    def _update_preview_with_width(self):
        """Update the preview rectangle with new line width."""
        if not self.is_first_click and self.preview_rect_id:
            # Get current preview coordinates
            coords = self.canvas.coords(self.preview_rect_id)
            if len(coords) >= 4:
                # Delete old preview
                self.canvas.delete(self.preview_rect_id)
                
                # Calculate display width based on zoom level
                display_width = max(1, int(self.line_width_mm * self.sketching_stage.zoom_level))
                
                # Create new preview with updated width
                self.preview_rect_id = self.canvas.create_rectangle(
                    coords[0], coords[1], coords[2], coords[3], 
                    outline="gray", width=display_width, dash=(4, 2), tags="temp"
                )
                
    def _calculate_rect_info(self, end_x, end_y):
        """Calculate width and height of the current rectangle.
        
        Args:
            end_x (float): Current end X coordinate
            end_y (float): Current end Y coordinate
        """
        # Convert canvas coordinates to real mm coordinates
        start_mm_x, start_mm_y = self.sketching_stage.canvas_to_mm(self.start_x, self.start_y)
        self.current_mm_x, self.current_mm_y = self.sketching_stage.canvas_to_mm(end_x, end_y)
        
        # Calculate width and height in mm
        self.rect_width_mm = abs(self.current_mm_x - start_mm_x)
        self.rect_height_mm = abs(self.current_mm_y - start_mm_y)
        
    def _update_rect_info_display(self):
        """Update or create the rectangle information display."""
        # Remove existing info display
        self.canvas.delete("rect_info")
        
        # Set display text based on edit mode
        if self.edit_mode == 'width':
            width_text = self.edit_value + "▋"  # Add cursor
            height_text = f"Height: {self.rect_height_mm:.1f}mm"
            line_width_text = f"Line Width: {self.line_width_mm:.2f}mm"
        elif self.edit_mode == 'height':
            width_text = f"Width: {self.rect_width_mm:.1f}mm"
            height_text = self.edit_value + "▋"  # Add cursor
            line_width_text = f"Line Width: {self.line_width_mm:.2f}mm"
        elif self.edit_mode == 'line_width':
            width_text = f"Width: {self.rect_width_mm:.1f}mm"
            height_text = f"Height: {self.rect_height_mm:.1f}mm"
            line_width_text = self.edit_value + "▋"  # Add cursor
        else:
            width_text = f"Width: {self.rect_width_mm:.1f}mm"
            height_text = f"Height: {self.rect_height_mm:.1f}mm"
            line_width_text = f"Line Width: {self.line_width_mm:.2f}mm"
        
        # Status text with instructions
        status_text = "Tab: Edit values | Enter: Confirm | Esc: Cancel"
        
        # Calculate position for the info display (center bottom of canvas)
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        x_pos = canvas_width // 2
        y_pos = canvas_height - 50  # Slightly higher for 3 lines
        
        # Create text items
        self.info_display_id = self.canvas.create_text(
            x_pos, y_pos, 
            text=f"{width_text}   {height_text}   {line_width_text}\n{status_text}",
            fill="black", font=("Arial", 10), justify=tk.CENTER,
            tags="rect_info temp"
        )
        
        # Create background rectangle for better visibility
        bbox = self.canvas.bbox(self.info_display_id)
        if bbox:
            padding = 10
            self.canvas.create_rectangle(
                bbox[0] - padding, bbox[1] - padding,
                bbox[2] + padding, bbox[3] + padding,
                fill="lightyellow", outline="gray",
                tags="rect_info temp"
            )
            # Move text to front
            self.canvas.tag_raise(self.info_display_id)
            self.canvas.tag_raise(self.info_display_id)
    
    def _handle_tab(self, event):
        """Handle tab key press to switch between editing modes."""
        if not self.is_first_click:  # Only when drawing a rectangle
            if self.edit_mode is None:
                # Enter width edit mode
                self.edit_mode = 'width'
                self.edit_value = f"{self.rect_width_mm:.1f}"
            elif self.edit_mode == 'width':
                # Switch to height edit mode
                self.edit_mode = 'height'
                self.edit_value = f"{self.rect_height_mm:.1f}"
            elif self.edit_mode == 'height':
                # Switch to line width edit mode
                self.edit_mode = 'line_width'
                self.edit_value = f"{self.line_width_mm:.2f}"
            elif self.edit_mode == 'line_width':
                # Back to width edit mode
                self.edit_mode = 'width'
                self.edit_value = f"{self.rect_width_mm:.1f}"
                
            self._update_rect_info_display()
            return "break"  # Prevent default tab behavior
        
    def _handle_enter(self, event):
        """Handle enter key press to confirm edits or create rectangle."""
        if not self.is_first_click:  # Only when drawing a rectangle
            if self.edit_mode == 'width':
                # Apply width change
                try:
                    new_width = float(self.edit_value)
                    if new_width > 0:
                        self._apply_new_width(new_width)
                except ValueError:
                    pass  # Invalid input, ignore
                    
                # Switch to height edit mode
                self.edit_mode = 'height'
                self.edit_value = f"{self.rect_height_mm:.1f}"
                self._update_rect_info_display()
                
            elif self.edit_mode == 'height':
                # Apply height change
                try:
                    new_height = float(self.edit_value)
                    if new_height > 0:
                        self._apply_new_height(new_height)
                except ValueError:
                    pass  # Invalid input, ignore
                    
                # Switch to line width edit mode
                self.edit_mode = 'line_width'
                self.edit_value = f"{self.line_width_mm:.2f}"
                self._update_rect_info_display()
                
            elif self.edit_mode == 'line_width':
                # Apply line width change
                try:
                    new_line_width = float(self.edit_value)
                    if new_line_width > 0:
                        self.line_width_mm = new_line_width
                        self._update_preview_with_width()
                except ValueError:
                    pass  # Invalid input, ignore
                    
                # Exit edit mode
                self.edit_mode = None
                self._update_rect_info_display()
                
            else:
                # Not in edit mode, create the rectangle
                self._finish_rectangle()
                
            return "break"  # Prevent default enter behavior
        
    def _handle_escape(self, event):
        """Handle escape key press to cancel edits or drawing."""
        if not self.is_first_click:  # Only when drawing a rectangle
            if self.edit_mode:
                # Cancel edit mode
                self.edit_mode = None
                self._update_rect_info_display()
            else:
                # Cancel rectangle drawing
                self.canvas.delete("temp")
                self.canvas.delete("rect_info")
                self.is_first_click = True
                self.preview_rect_id = None
                
            return "break"  # Prevent default escape behavior
            
    def _handle_key(self, event):
        """Handle regular key presses during edit mode."""
        if self.edit_mode and not self.is_first_click:
            if event.keysym == 'BackSpace':
                # Handle backspace
                self.edit_value = self.edit_value[:-1] if self.edit_value else ""
            elif event.keysym in ('Right', 'Left', 'Up', 'Down'):
                # Ignore arrow keys
                pass
            elif event.char and (event.char.isdigit() or event.char in '.,-'):
                # Accept digits and decimal point for editing
                self.edit_value += event.char
                
            self._update_rect_info_display()
            return "break"  # Prevent default key behavior
            
    def _apply_new_width(self, new_width):
        """Apply a new width to the rectangle being drawn.
        
        Args:
            new_width (float): The new width in mm
        """
        # Calculate new endpoint coordinates
        start_mm_x, start_mm_y = self.sketching_stage.canvas_to_mm(self.start_x, self.start_y)
        
        # Determine direction based on current position
        if self.current_mm_x >= start_mm_x:
            new_end_mm_x = start_mm_x + new_width
        else:
            new_end_mm_x = start_mm_x - new_width
            
        # Keep the same height
        new_end_mm_y = self.current_mm_y
        
        # Convert back to canvas coordinates
        x1, y1, _, _ = self.sketching_stage.get_work_area_bounds()
        new_end_canvas_x = x1 + (new_end_mm_x * self.sketching_stage.zoom_level)
        new_end_canvas_y = y1 + (new_end_mm_y * self.sketching_stage.zoom_level)
        
        # Update rectangle width
        self.rect_width_mm = new_width
        self.current_mm_x = new_end_mm_x
        
        # Calculate display width based on zoom level
        display_width = max(1, int(self.line_width_mm * self.sketching_stage.zoom_level))
        
        # Update preview with real width
        self.canvas.delete(self.preview_rect_id)
        self.preview_rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, new_end_canvas_x, new_end_canvas_y,
            outline="gray", width=display_width, dash=(4, 2), tags="temp"
        )
        
    def _apply_new_height(self, new_height):
        """Apply a new height to the rectangle being drawn.
        
        Args:
            new_height (float): The new height in mm
        """
        # Calculate new endpoint coordinates
        start_mm_x, start_mm_y = self.sketching_stage.canvas_to_mm(self.start_x, self.start_y)
        
        # Keep the same width
        new_end_mm_x = self.current_mm_x
        
        # Determine direction based on current position
        if self.current_mm_y >= start_mm_y:
            new_end_mm_y = start_mm_y + new_height
        else:
            new_end_mm_y = start_mm_y - new_height
        
        # Convert back to canvas coordinates
        x1, y1, _, _ = self.sketching_stage.get_work_area_bounds()
        new_end_canvas_x = x1 + (new_end_mm_x * self.sketching_stage.zoom_level)
        new_end_canvas_y = y1 + (new_end_mm_y * self.sketching_stage.zoom_level)
        
        # Update rectangle height
        self.rect_height_mm = new_height
        self.current_mm_y = new_end_mm_y
        
        # Calculate display width based on zoom level
        display_width = max(1, int(self.line_width_mm * self.sketching_stage.zoom_level))
        
        # Update preview with real width
        self.canvas.delete(self.preview_rect_id)
        self.preview_rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, new_end_canvas_x, new_end_canvas_y,
            outline="gray", width=display_width, dash=(4, 2), tags="temp"
        )
        
    def _finish_rectangle(self):
        """Finish rectangle creation with current parameters."""
        # Calculate endpoint based on current width and height
        start_mm_x, start_mm_y = self.sketching_stage.canvas_to_mm(self.start_x, self.start_y)
        
        # Determine end coordinates based on current position
        if self.current_mm_x >= start_mm_x:
            end_mm_x = start_mm_x + self.rect_width_mm
        else:
            end_mm_x = start_mm_x - self.rect_width_mm
            
        if self.current_mm_y >= start_mm_y:
            end_mm_y = start_mm_y + self.rect_height_mm
        else:
            end_mm_y = start_mm_y - self.rect_height_mm
        
        # Convert back to canvas coordinates
        x1, y1, _, _ = self.sketching_stage.get_work_area_bounds()
        end_canvas_x = x1 + (end_mm_x * self.sketching_stage.zoom_level)
        end_canvas_y = y1 + (end_mm_y * self.sketching_stage.zoom_level)
        
        # Calculate display width based on zoom level
        display_width = max(1, int(self.line_width_mm * self.sketching_stage.zoom_level))
        
        # Create the final rectangle with real-world line width
        self.canvas.create_rectangle(
            self.start_x, self.start_y, end_canvas_x, end_canvas_y,
            outline="black", width=display_width, tags="drawing"
        )
        
        # Store the drawing object with line width in mm
        self.sketching_stage.add_drawing_object(
            'rectangle',
            [start_mm_x, start_mm_y, end_mm_x, end_mm_y],
            {'outline': 'black', 'width_mm': self.line_width_mm, 'fill': ''}
        )
        
        # Add reference points at the corners of the rectangle
        self.sketching_stage.add_drawing_object(
            'reference_point',
            [start_mm_x, start_mm_y],
            {'color': 'blue'}
        )
        self.sketching_stage.add_drawing_object(
            'reference_point',
            [end_mm_x, start_mm_y],
            {'color': 'blue'}
        )
        self.sketching_stage.add_drawing_object(
            'reference_point',
            [end_mm_x, end_mm_y],
            {'color': 'blue'}
        )
        self.sketching_stage.add_drawing_object(
            'reference_point',
            [start_mm_x, end_mm_y],
            {'color': 'blue'}
        )
        
        # Clean up and reset
        self.canvas.delete("temp")
        self.canvas.delete("rect_info")
        self.is_first_click = True
        self.preview_rect_id = None
        self.edit_mode = None


class ImageTool(DrawingTool):
    """Tool for placing and scaling images."""
    
    def __init__(self, canvas, sketching_stage):
        """Initialize the image tool."""
        super().__init__(canvas, sketching_stage)
        self.loaded_image = None
        self.image_file_path = None
        self.placing_image = False
        self.preview_image_id = None
        self.info_display_id = None
        
        # Image properties
        self.image_width_mm = 20.0  # Default width in mm
        self.image_height_mm = 20.0  # Default height in mm
        self.image_x_mm = 0.0  # Position in mm
        self.image_y_mm = 0.0  # Position in mm
        
        # Interactive editing properties
        self.edit_mode = None  # Can be 'width', 'height', or None
        self.edit_value = ""  # String representation of value being edited
        
        # Selection and resizing
        self.selected_image = None  # Currently selected image object
        self.resize_handles = []  # List of resize handle IDs
        self.dragging_handle = None  # Which handle is being dragged
        self.original_mouse_pos = None  # Original mouse position when dragging started
        
    def activate(self):
        """Activate the image tool."""
        self.is_active = True
        self.canvas.config(cursor="dotbox")  # Change cursor to indicate image tool
        
        # Clear any existing bindings
        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")
        
        # Bind events for image interaction
        self.canvas.bind("<Button-1>", self._handle_click)
        self.canvas.bind("<B1-Motion>", self._handle_drag)
        self.canvas.bind("<ButtonRelease-1>", self._handle_release)
        
        # Bind keyboard events for interactive editing
        self.canvas.focus_set()
        self.canvas.bind("<Tab>", self._handle_tab)
        self.canvas.bind("<Return>", self._handle_enter)
        self.canvas.bind("<Escape>", self._handle_escape)
        self.canvas.bind("<Key>", self._handle_key)
        
        # Preserve the original motion handler for coordinate tracking
        original_motion = self.canvas.bind("<Motion>")
        self.canvas.bind("<Motion>", lambda e: self._handle_motion(e, original_motion))
        
    def deactivate(self):
        """Deactivate the image tool."""
        self.is_active = False
        self.canvas.delete("temp")
        self.canvas.delete("image_info")
        self._clear_selection()  # Clear any selected image and handles
        self.placing_image = False
        self.preview_image_id = None
        self.info_display_id = None
        self.edit_mode = None
        self.edit_value = ""
        
        # Unbind keyboard events
        self.canvas.unbind("<Tab>")
        self.canvas.unbind("<Return>")
        self.canvas.unbind("<Escape>")
        self.canvas.unbind("<Key>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")
        
    def get_cursor(self):
        """Get the cursor for this tool."""
        return "crosshair"
        
    def get_status_text(self):
        """Get the status text for this tool."""
        if self.selected_image:
            return "Image Selected - Drag corner handles to resize"
        else:
            return "Image Tool - Click empty area to add image, click existing image to select"
            
    def _load_image(self):
        """Load an image file."""
        from tkinter import filedialog
        from PIL import Image, ImageTk
        
        file_types = [
            ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff"),
            ("PNG files", "*.png"),
            ("JPEG files", "*.jpg *.jpeg"),
            ("All files", "*.*")
        ]
        
        file_path = filedialog.askopenfilename(
            title="Select Image File",
            filetypes=file_types
        )
        
        if file_path:
            try:
                # Load the image
                self.loaded_image = Image.open(file_path)
                self.image_file_path = file_path
                
                # Calculate initial size maintaining aspect ratio
                original_width, original_height = self.loaded_image.size
                aspect_ratio = original_width / original_height
                
                # Set default size (20mm width, height based on aspect ratio)
                self.image_width_mm = 20.0
                self.image_height_mm = self.image_width_mm / aspect_ratio
                
                return True
                
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("Error Loading Image", f"Could not load image:\n{str(e)}")
                return False
        return False
        
    def _handle_click(self, event):
        """Handle mouse clicks for image placement and selection."""
        # Only work if clicking within work area
        if not self.sketching_stage.is_point_in_work_area(event.x, event.y):
            return
            
        # First check if we clicked on a resize handle (if an image is already selected)
        if self.selected_image:
            handle_index = self._find_handle_at_position(event.x, event.y)
            if handle_index is not None:
                # Start dragging a handle
                self.dragging_handle = handle_index
                self.original_mouse_pos = (event.x, event.y)
                return
            else:
                # Check if clicking on the selected image itself (for moving)
                clicked_same_image = self._find_image_at_position(event.x, event.y) == self.selected_image
                if clicked_same_image:
                    # Start dragging the image itself
                    self.dragging_handle = "move"  # Special value for moving
                    self.original_mouse_pos = (event.x, event.y)
                    return
        
        # Check if we clicked on an existing image
        clicked_image = self._find_image_at_position(event.x, event.y)
        
        if clicked_image:
            # Clicked on an existing image - select it and show resize handles
            self._select_image(clicked_image, event.x, event.y)
        else:
            # Clicked on empty area - suggest adding new image
            self._clear_selection()
            self._suggest_new_image(event.x, event.y)
            
    def _handle_motion(self, event, original_handler):
        """Handle mouse motion for image preview and cursor feedback."""
        # Check if we're hovering over a handle and change cursor accordingly
        if self.selected_image:
            handle_index = self._find_handle_at_position(event.x, event.y)
            if handle_index is not None:
                # Change cursor to indicate resizing
                if handle_index in [0, 2]:  # Top-left or bottom-right
                    self.canvas.config(cursor="size_nw_se")
                else:  # Top-right or bottom-left
                    self.canvas.config(cursor="size_ne_sw")
            else:
                # Check if hovering over the image itself
                clicked_image = self._find_image_at_position(event.x, event.y)
                if clicked_image:
                    self.canvas.config(cursor="hand2")  # Hand cursor for moving
                else:
                    self.canvas.config(cursor="dotbox")  # Default image tool cursor
        else:
            self.canvas.config(cursor="dotbox")  # Default image tool cursor
        
        # Handle image preview if placing
        if self.placing_image and self.loaded_image:
            self._update_preview(event.x, event.y)
        
        # Call original motion handler for coordinate tracking
        if original_handler and hasattr(self.sketching_stage, '_update_coordinates'):
            self.sketching_stage._update_coordinates(event)
            
    def _update_preview(self, x, y):
        """Update the preview image as mouse moves."""
        if self.placing_image and self.loaded_image:
            # Delete previous preview
            if self.preview_image_id:
                self.canvas.delete(self.preview_image_id)
                
            # Convert position to mm
            mm_x, mm_y = self.sketching_stage.canvas_to_mm(x, y)
            
            # Calculate display size based on zoom
            display_width = max(1, int(self.image_width_mm * self.sketching_stage.zoom_level))
            display_height = max(1, int(self.image_height_mm * self.sketching_stage.zoom_level))
            
            # Resize image for preview
            try:
                preview_image = self.loaded_image.resize((display_width, display_height), Image.Resampling.LANCZOS)
                self.preview_photo = ImageTk.PhotoImage(preview_image)
                
                # Create preview image
                self.preview_image_id = self.canvas.create_image(
                    x, y, anchor="center", image=self.preview_photo, tags="temp"
                )
                
                # Set current position for info display
                self.image_x_mm = mm_x
                self.image_y_mm = mm_y
                
                # Show image information
                self._update_image_info_display()
                
            except Exception as e:
                print(f"Error creating preview: {e}")
                
    def _update_image_info_display(self):
        """Update or create the image information display."""
        # Remove existing info display
        self.canvas.delete("image_info")
        
        # Set display text based on edit mode
        if self.edit_mode == 'width':
            width_text = self.edit_value + "▋"  # Add cursor
            height_text = f"Height: {self.image_height_mm:.1f}mm"
        elif self.edit_mode == 'height':
            width_text = f"Width: {self.image_width_mm:.1f}mm"
            height_text = self.edit_value + "▋"  # Add cursor
        else:
            width_text = f"Width: {self.image_width_mm:.1f}mm"
            height_text = f"Height: {self.image_height_mm:.1f}mm"
        
        # Status text with instructions
        status_text = "Click to place | Tab: Edit size | Enter: Confirm | Esc: Cancel"
        
        # Calculate position for the info display (center bottom of canvas)
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        x_pos = canvas_width // 2
        y_pos = canvas_height - 50
        
        # Create text items
        self.info_display_id = self.canvas.create_text(
            x_pos, y_pos, 
            text=f"{width_text}   {height_text}\n{status_text}",
            fill="black", font=("Arial", 10), justify=tk.CENTER,
            tags="image_info temp"
        )
        
        # Create background rectangle for better visibility
        bbox = self.canvas.bbox(self.info_display_id)
        if bbox:
            padding = 10
            self.canvas.create_rectangle(
                bbox[0] - padding, bbox[1] - padding,
                bbox[2] + padding, bbox[3] + padding,
                fill="lightyellow", outline="gray",
                tags="image_info temp"
            )
            # Move text to front
            self.canvas.tag_raise(self.info_display_id)
            
    def _handle_tab(self, event):
        """Handle tab key press to switch between editing modes."""
        if self.placing_image:
            if self.edit_mode is None:
                # Enter width edit mode
                self.edit_mode = 'width'
                self.edit_value = f"{self.image_width_mm:.1f}"
            elif self.edit_mode == 'width':
                # Switch to height edit mode
                self.edit_mode = 'height'
                self.edit_value = f"{self.image_height_mm:.1f}"
            elif self.edit_mode == 'height':
                # Back to width edit mode
                self.edit_mode = 'width'
                self.edit_value = f"{self.image_width_mm:.1f}"
                
            self._update_image_info_display()
            return "break"
        
    def _handle_enter(self, event):
        """Handle enter key press to confirm edits."""
        if self.placing_image:
            if self.edit_mode == 'width':
                # Apply width change
                try:
                    new_width = float(self.edit_value)
                    if new_width > 0:
                        # Maintain aspect ratio
                        aspect_ratio = self.image_width_mm / self.image_height_mm
                        self.image_width_mm = new_width
                        self.image_height_mm = new_width / aspect_ratio
                        
                        # Update preview if it exists
                        if self.preview_image_id:
                            coords = self.canvas.coords(self.preview_image_id)
                            if coords:
                                self._update_preview(coords[0], coords[1])
                except ValueError:
                    pass
                    
                # Switch to height edit mode
                self.edit_mode = 'height'
                self.edit_value = f"{self.image_height_mm:.1f}"
                self._update_image_info_display()
                
            elif self.edit_mode == 'height':
                # Apply height change
                try:
                    new_height = float(self.edit_value)
                    if new_height > 0:
                        # Maintain aspect ratio
                        aspect_ratio = self.image_width_mm / self.image_height_mm
                        self.image_height_mm = new_height
                        self.image_width_mm = new_height * aspect_ratio
                        
                        # Update preview if it exists
                        if self.preview_image_id:
                            coords = self.canvas.coords(self.preview_image_id)
                            if coords:
                                self._update_preview(coords[0], coords[1])
                except ValueError:
                    pass
                    
                # Exit edit mode
                self.edit_mode = None
                self._update_image_info_display()
                
            return "break"
        
    def _handle_escape(self, event):
        """Handle escape key press to cancel edits or placement."""
        if self.placing_image:
            if self.edit_mode:
                # Cancel edit mode
                self.edit_mode = None
                self._update_image_info_display()
            else:
                # Cancel image placement
                self.canvas.delete("temp")
                self.canvas.delete("image_info")
                self.placing_image = False
                self.preview_image_id = None
                
            return "break"
            
    def _handle_key(self, event):
        """Handle regular key presses during edit mode."""
        if self.edit_mode and self.placing_image:
            if event.keysym == 'BackSpace':
                # Handle backspace
                self.edit_value = self.edit_value[:-1] if self.edit_value else ""
            elif event.keysym in ('Right', 'Left', 'Up', 'Down'):
                # Ignore arrow keys
                pass
            elif event.char and (event.char.isdigit() or event.char in '.,-'):
                # Accept digits and decimal point for editing
                self.edit_value += event.char
                
            self._update_image_info_display()
            return "break"
            
    def _place_image(self):
        """Place the image at the current position."""
        if not self.loaded_image:
            return
            
        # Calculate display size
        display_width = max(1, int(self.image_width_mm * self.sketching_stage.zoom_level))
        display_height = max(1, int(self.image_height_mm * self.sketching_stage.zoom_level))
        
        # Convert mm position to canvas coordinates
        x1, y1, _, _ = self.sketching_stage.get_work_area_bounds()
        canvas_x = x1 + (self.image_x_mm * self.sketching_stage.zoom_level)
        canvas_y = y1 + (self.image_y_mm * self.sketching_stage.zoom_level)
        
        try:
            # Resize image for display
            display_image = self.loaded_image.resize((display_width, display_height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(display_image)
            
            # Create the image on canvas
            image_id = self.canvas.create_image(
                canvas_x, canvas_y, anchor="center", image=photo, tags="drawing"
            )
            
            # Store reference to prevent garbage collection
            setattr(self.canvas, f"image_ref_{image_id}", photo)
            
            # Store the drawing object
            self.sketching_stage.add_drawing_object(
                'image',
                [self.image_x_mm, self.image_y_mm],  # Center position
                {
                    'file_path': self.image_file_path,
                    'width_mm': self.image_width_mm,
                    'height_mm': self.image_height_mm,
                    'anchor': 'center'
                }
            )
            
            # Add reference point at center
            self.sketching_stage.add_drawing_object(
                'reference_point',
                [self.image_x_mm, self.image_y_mm],
                {'color': 'green'}
            )
            
            # Clean up and continue placing (user can place multiple copies)
            self.canvas.delete("temp")
            self.canvas.delete("image_info")
            self.preview_image_id = None
            self.edit_mode = None
            
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error Placing Image", f"Could not place image:\n{str(e)}")
            
    def _find_image_at_position(self, canvas_x, canvas_y):
        """Find an image object at the given canvas position.
        
        Args:
            canvas_x (float): X coordinate on canvas
            canvas_y (float): Y coordinate on canvas
            
        Returns:
            dict: Image drawing object if found, None otherwise
        """
        # Convert canvas coordinates to mm
        mm_x, mm_y = self.sketching_stage.canvas_to_mm(canvas_x, canvas_y)
        
        # Add detection radius (10 pixels converted to mm)
        detection_radius_mm = 10.0 / self.sketching_stage.zoom_level
        
        # Search through all drawing objects for images
        for drawing_obj in self.sketching_stage.drawing_objects:
            if drawing_obj['type'] == 'image':
                real_coords = drawing_obj['real_coords']
                properties = drawing_obj['properties']
                
                if len(real_coords) >= 2:
                    # Get image center and dimensions
                    center_x, center_y = real_coords[0], real_coords[1]
                    width_mm = properties.get('width_mm', 20.0)
                    height_mm = properties.get('height_mm', 20.0)
                    
                    # Expand bounds by detection radius
                    left = center_x - (width_mm / 2) - detection_radius_mm
                    right = center_x + (width_mm / 2) + detection_radius_mm
                    top = center_y - (height_mm / 2) - detection_radius_mm
                    bottom = center_y + (height_mm / 2) + detection_radius_mm
                    
                    if left <= mm_x <= right and top <= mm_y <= bottom:
                        return drawing_obj
        
        return None
        
    def _find_handle_at_position(self, canvas_x, canvas_y):
        """Find a resize handle at the given canvas position.
        
        Args:
            canvas_x (float): X coordinate on canvas
            canvas_y (float): Y coordinate on canvas
            
        Returns:
            int: Handle index if found, None otherwise
        """
        if not self.selected_image or not self.resize_handles:
            return None
            
        detection_radius = 15  # 15 pixel radius for handle detection
        
        real_coords = self.selected_image['real_coords']
        properties = self.selected_image['properties']
        
        if len(real_coords) >= 2:
            # Get image center and dimensions
            center_x_mm, center_y_mm = real_coords[0], real_coords[1]
            width_mm = properties.get('width_mm', 20.0)
            height_mm = properties.get('height_mm', 20.0)
            
            # Calculate corner positions in mm
            left_mm = center_x_mm - width_mm / 2
            right_mm = center_x_mm + width_mm / 2
            top_mm = center_y_mm - height_mm / 2
            bottom_mm = center_y_mm + height_mm / 2
            
            # Convert to canvas coordinates
            x1, y1, _, _ = self.sketching_stage.get_work_area_bounds()
            
            corners = [
                (left_mm, top_mm),      # Top-left (index 0)
                (right_mm, top_mm),     # Top-right (index 1)
                (right_mm, bottom_mm),  # Bottom-right (index 2)
                (left_mm, bottom_mm)    # Bottom-left (index 3)
            ]
            
            # Check each corner handle
            for i, (corner_x_mm, corner_y_mm) in enumerate(corners):
                handle_canvas_x = x1 + (corner_x_mm * self.sketching_stage.zoom_level)
                handle_canvas_y = y1 + (corner_y_mm * self.sketching_stage.zoom_level)
                
                # Calculate distance from click to handle center
                distance = ((canvas_x - handle_canvas_x) ** 2 + (canvas_y - handle_canvas_y) ** 2) ** 0.5
                
                if distance <= detection_radius:
                    return i
        
        return None
        
    def _suggest_new_image(self, canvas_x, canvas_y):
        """Suggest adding a new image at the clicked position.
        
        Args:
            canvas_x (float): X coordinate on canvas
            canvas_y (float): Y coordinate on canvas
        """
        from tkinter import messagebox
        
        # Ask user if they want to add a new image
        result = messagebox.askyesno(
            "Add Image", 
            "No image found at this location.\nWould you like to add a new image here?"
        )
        
        if result:
            # Load and place new image
            if self._load_image():
                # Convert click position to mm coordinates
                self.image_x_mm, self.image_y_mm = self.sketching_stage.canvas_to_mm(canvas_x, canvas_y)
                # Place the image
                self._place_image()
                
    def _select_image(self, image_obj, canvas_x, canvas_y):
        """Select an image and show resize handles.
        
        Args:
            image_obj (dict): The image drawing object to select
            canvas_x (float): X coordinate where clicked
            canvas_y (float): Y coordinate where clicked
        """
        # Clear any previous selection
        self._clear_selection()
        
        # Set selected image
        self.selected_image = image_obj
        
        # Show resize handles
        self._show_resize_handles()
        
    def _clear_selection(self):
        """Clear the current image selection and hide resize handles."""
        self.selected_image = None
        self._hide_resize_handles()
        
    def _show_resize_handles(self):
        """Show resize handles around the selected image."""
        if not self.selected_image:
            return
            
        real_coords = self.selected_image['real_coords']
        properties = self.selected_image['properties']
        
        if len(real_coords) >= 2:
            # Get image center and dimensions
            center_x_mm, center_y_mm = real_coords[0], real_coords[1]
            width_mm = properties.get('width_mm', 20.0)
            height_mm = properties.get('height_mm', 20.0)
            
            # Calculate corner positions in mm
            left_mm = center_x_mm - width_mm / 2
            right_mm = center_x_mm + width_mm / 2
            top_mm = center_y_mm - height_mm / 2
            bottom_mm = center_y_mm + height_mm / 2
            
            # Convert to canvas coordinates
            x1, y1, _, _ = self.sketching_stage.get_work_area_bounds()
            
            corners = [
                (left_mm, top_mm),      # Top-left
                (right_mm, top_mm),     # Top-right
                (right_mm, bottom_mm),  # Bottom-right
                (left_mm, bottom_mm)    # Bottom-left
            ]
            
            # Create resize handles at corners
            handle_size = 6
            for i, (corner_x_mm, corner_y_mm) in enumerate(corners):
                canvas_x = x1 + (corner_x_mm * self.sketching_stage.zoom_level)
                canvas_y = y1 + (corner_y_mm * self.sketching_stage.zoom_level)
                
                handle_id = self.canvas.create_rectangle(
                    canvas_x - handle_size, canvas_y - handle_size,
                    canvas_x + handle_size, canvas_y + handle_size,
                    fill="blue", outline="darkblue", width=2,
                    tags="image_handles temp"
                )
                self.resize_handles.append(handle_id)
                
    def _hide_resize_handles(self):
        """Hide resize handles."""
        self.canvas.delete("image_handles")
        self.resize_handles = []
        
    def _handle_drag(self, event):
        """Handle mouse drag for resizing or moving selected image."""
        if self.selected_image and self.dragging_handle is not None:
            if self.dragging_handle == "move":
                # Handle image moving
                self._move_image(event.x, event.y)
            else:
                # Handle image resizing
                self._resize_image(event.x, event.y)
                
    def _move_image(self, canvas_x, canvas_y):
        """Move the selected image to a new position.
        
        Args:
            canvas_x (float): Current mouse X coordinate
            canvas_y (float): Current mouse Y coordinate
        """
        if not self.selected_image or not self.original_mouse_pos:
            return
            
        # Calculate movement delta in canvas coordinates
        delta_x = canvas_x - self.original_mouse_pos[0]
        delta_y = canvas_y - self.original_mouse_pos[1]
        
        # Convert delta to mm
        delta_mm_x = delta_x / self.sketching_stage.zoom_level
        delta_mm_y = delta_y / self.sketching_stage.zoom_level
        
        # Update image position
        real_coords = self.selected_image['real_coords']
        real_coords[0] += delta_mm_x  # Update center X
        real_coords[1] += delta_mm_y  # Update center Y
        
        # Update the original mouse position for next delta calculation
        self.original_mouse_pos = (canvas_x, canvas_y)
        
        # Clear existing drawing objects from canvas and redraw all
        self.canvas.delete("drawing")  # Remove all visual drawing objects
        self.sketching_stage._redraw_drawing_objects()  # Redraw with updated positions
        
        # Update the handles to show new position
        self._update_resize_handles()
            
    def _handle_release(self, event):
        """Handle mouse release to finish resizing."""
        if self.dragging_handle is not None:
            # Finalize the resize operation
            self._finalize_resize()
        
        self.dragging_handle = None
        self.original_mouse_pos = None
        
    def _resize_image(self, canvas_x, canvas_y):
        """Resize the selected image based on drag position.
        
        Args:
            canvas_x (float): Current mouse X coordinate
            canvas_y (float): Current mouse Y coordinate
        """
        if not self.selected_image or self.dragging_handle is None or self.original_mouse_pos is None:
            return
            
        # Convert current position to mm
        current_mm_x, current_mm_y = self.sketching_stage.canvas_to_mm(canvas_x, canvas_y)
        
        # Get image properties
        real_coords = self.selected_image['real_coords']
        properties = self.selected_image['properties']
        
        center_x_mm, center_y_mm = real_coords[0], real_coords[1]
        original_width_mm = properties.get('width_mm', 20.0)
        original_height_mm = properties.get('height_mm', 20.0)
        
        # Calculate new dimensions based on which handle is being dragged
        # Handle indexes: 0=top-left, 1=top-right, 2=bottom-right, 3=bottom-left
        
        if self.dragging_handle == 0:  # Top-left
            # Distance from center to new top-left corner
            new_half_width = abs(center_x_mm - current_mm_x)
            new_half_height = abs(center_y_mm - current_mm_y)
        elif self.dragging_handle == 1:  # Top-right
            new_half_width = abs(current_mm_x - center_x_mm)
            new_half_height = abs(center_y_mm - current_mm_y)
        elif self.dragging_handle == 2:  # Bottom-right
            new_half_width = abs(current_mm_x - center_x_mm)
            new_half_height = abs(current_mm_y - center_y_mm)
        else:  # Bottom-left (handle 3)
            new_half_width = abs(center_x_mm - current_mm_x)
            new_half_height = abs(current_mm_y - center_y_mm)
        
        # Calculate new full dimensions (minimum 1mm)
        new_width_mm = max(1.0, new_half_width * 2)
        new_height_mm = max(1.0, new_half_height * 2)
        
        # Update the image properties temporarily (for preview)
        properties['width_mm'] = new_width_mm
        properties['height_mm'] = new_height_mm
        
        # Clear existing drawing objects from canvas and redraw all
        self.canvas.delete("drawing")  # Remove all visual drawing objects
        self.sketching_stage._redraw_drawing_objects()  # Redraw with updated dimensions
        
        # Update the handles to show new size
        self._update_resize_handles()
        
    def _finalize_resize(self):
        """Finalize the resize operation by updating the canvas display."""
        if self.selected_image:
            # The properties have already been updated during dragging
            # Clear and redraw the canvas with final dimensions
            self.canvas.delete("drawing")  # Remove all visual drawing objects
            self.sketching_stage._redraw_drawing_objects()  # Redraw with final dimensions
            self._show_resize_handles()  # Refresh handles
            
    def _update_resize_handles(self):
        """Update resize handle positions based on current image size."""
        self._hide_resize_handles()
        self._show_resize_handles()


class OriginTool(DrawingTool):
    """Tool for placing the origin point."""
    
    def __init__(self, canvas, sketching_stage):
        """Initialize the origin tool."""
        super().__init__(canvas, sketching_stage)
        self.origin_x_mm = 0.0
        self.origin_y_mm = 0.0
        
    def activate(self):
        """Activate the origin tool."""
        self.is_active = True
        self.canvas.config(cursor="crosshair")
        
        # Clear any existing bindings
        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")
        
        # Bind events for origin placement
        self.canvas.bind("<Button-1>", self._handle_click)
        
        # Preserve the original motion handler for coordinate tracking
        original_motion = self.canvas.bind("<Motion>")
        self.canvas.bind("<Motion>", lambda e: self._handle_motion(e, original_motion))
        
    def deactivate(self):
        """Deactivate the origin tool."""
        self.is_active = False
        self.canvas.delete("temp")
        self.canvas.delete("snap_indicator")
        
    def get_cursor(self):
        """Get the cursor for this tool."""
        return "crosshair"
        
    def get_status_text(self):
        """Get the status text for this tool."""
        return "Place Origin - Click to set the origin point (0,0)"
        
    def _handle_click(self, event):
        """Handle mouse clicks for origin placement."""
        # Only place if clicking within work area
        if not self.sketching_stage.is_point_in_work_area(event.x, event.y):
            return
            
        # Apply snapping to click position
        snapped_x, snapped_y = self._apply_snap(event.x, event.y)
        
        # Convert click position to mm coordinates
        self.origin_x_mm, self.origin_y_mm = self.sketching_stage.canvas_to_mm(snapped_x, snapped_y)
        
        # Place the origin marker
        self._place_origin(snapped_x, snapped_y)
        
    def _handle_motion(self, event, original_handler):
        """Handle mouse motion for origin preview."""
        # Only show preview if within work area
        if not self.sketching_stage.is_point_in_work_area(event.x, event.y):
            self.canvas.delete("origin_preview")
            return
            
        # Apply snapping to motion coordinates
        snapped_x, snapped_y = self._apply_snap(event.x, event.y)
        
        # Show snap indicator if we're snapping
        if (snapped_x, snapped_y) != (event.x, event.y):
            self._draw_snap_indicator(snapped_x, snapped_y)
        else:
            self.canvas.delete("snap_indicator")
        
        # Show preview of origin marker
        self._update_preview(snapped_x, snapped_y)
        
        # Call original motion handler for coordinate tracking
        if original_handler and hasattr(self.sketching_stage, '_update_coordinates'):
            # Create a mock event with snapped coordinates for accurate display
            mock_event = type('MockEvent', (), {'x': snapped_x, 'y': snapped_y})()
            self.sketching_stage._update_coordinates(mock_event)
            
    def _update_preview(self, canvas_x, canvas_y):
        """Update the preview origin marker as mouse moves.
        
        Args:
            canvas_x (float): X coordinate (potentially snapped)
            canvas_y (float): Y coordinate (potentially snapped)
        """
        # Delete previous preview
        self.canvas.delete("origin_preview")
        
        # Create preview origin marker
        self._draw_origin_marker(canvas_x, canvas_y, preview=True)
        
    def _place_origin(self, canvas_x, canvas_y):
        """Place the origin marker permanently.
        
        Args:
            canvas_x (float): Canvas X coordinate
            canvas_y (float): Canvas Y coordinate
        """
        # Remove any existing origin markers (only one origin allowed)
        self._remove_existing_origin()
        
        # Create the permanent origin marker on canvas
        self._draw_origin_marker(canvas_x, canvas_y, preview=False)
        
        # Store the origin as a drawing object
        self.sketching_stage.add_drawing_object(
            'origin',
            [self.origin_x_mm, self.origin_y_mm],
            {'color': 'green', 'type': 'origin'}
        )
        
        # Clean up preview
        self.canvas.delete("temp")
        self.canvas.delete("snap_indicator")
        self.canvas.delete("origin_preview")
        
        # Show confirmation message
        from tkinter import messagebox
        messagebox.showinfo(
            "Origin Placed", 
            f"Origin set at coordinates:\nX: {self.origin_x_mm:.2f}mm\nY: {self.origin_y_mm:.2f}mm"
        )
        
    def _draw_origin_marker(self, canvas_x, canvas_y, preview=False):
        """Draw the origin marker (green dot with smaller red center).
        
        Args:
            canvas_x (float): Canvas X coordinate
            canvas_y (float): Canvas Y coordinate
            preview (bool): Whether this is a preview or permanent marker
        """
        tag = "origin_preview temp" if preview else "origin drawing"
        
        # Draw outer green circle (larger)
        green_radius = 8
        green_circle = self.canvas.create_oval(
            canvas_x - green_radius, canvas_y - green_radius,
            canvas_x + green_radius, canvas_y + green_radius,
            fill="green", outline="darkgreen", width=2,
            tags=tag
        )
        
        # Draw inner red circle (smaller)
        red_radius = 3
        red_circle = self.canvas.create_oval(
            canvas_x - red_radius, canvas_y - red_radius,
            canvas_x + red_radius, canvas_y + red_radius,
            fill="red", outline="darkred", width=1,
            tags=tag
        )
        
        # Add crosshairs for precise positioning
        crosshair_length = 12
        
        # Horizontal crosshair
        self.canvas.create_line(
            canvas_x - crosshair_length, canvas_y,
            canvas_x + crosshair_length, canvas_y,
            fill="white", width=1, tags=tag
        )
        
        # Vertical crosshair
        self.canvas.create_line(
            canvas_x, canvas_y - crosshair_length,
            canvas_x, canvas_y + crosshair_length,
            fill="white", width=1, tags=tag
        )
        
    def _remove_existing_origin(self):
        """Remove any existing origin markers from canvas and drawing objects."""
        # Remove from canvas
        self.canvas.delete("origin")
        
        # Remove from drawing objects list
        self.sketching_stage.drawing_objects = [
            obj for obj in self.sketching_stage.drawing_objects 
            if obj['type'] != 'origin'
        ]
        
    def get_current_origin(self):
        """Get the current origin coordinates.
        
        Returns:
            tuple: (x_mm, y_mm) or None if no origin is set
        """
        # Look for origin in drawing objects
        for obj in self.sketching_stage.drawing_objects:
            if obj['type'] == 'origin':
                coords = obj['real_coords']
                if len(coords) >= 2:
                    return coords[0], coords[1]
        return None


class CircleTool(DrawingTool):
    """Tool for drawing circles."""
    
    def __init__(self, canvas, sketching_stage):
        """Initialize the circle tool."""
        super().__init__(canvas, sketching_stage)
        self.is_first_click = True
        self.center_x = 0
        self.center_y = 0
        self.preview_circle_id = None
        self.info_display_id = None
        
        # Circle properties
        self.radius_mm = 5.0  # Default radius in mm
        self.line_width_mm = 0.1  # Default line width in mm
        
        # Interactive editing properties
        self.edit_mode = None  # Can be 'radius', 'line_width', or None
        self.edit_value = ""  # String representation of value being edited
        self.current_mm_x = 0  # Current edge position
        self.current_mm_y = 0  # Current edge position
        
    def activate(self):
        """Activate the circle tool."""
        self.is_active = True
        self.is_first_click = True
        self.canvas.config(cursor="crosshair")
        
        # Clear any existing bindings
        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")
        
        # Bind events for circle drawing
        self.canvas.bind("<Button-1>", self._handle_click)
        
        # Bind keyboard events for interactive editing
        self.canvas.focus_set()
        self.canvas.bind("<Tab>", self._handle_tab)
        self.canvas.bind("<Return>", self._handle_enter)
        self.canvas.bind("<Escape>", self._handle_escape)
        self.canvas.bind("<Key>", self._handle_key)
        
        # Preserve the original motion handler for coordinate tracking
        original_motion = self.canvas.bind("<Motion>")
        self.canvas.bind("<Motion>", lambda e: self._handle_motion(e, original_motion))
        
    def deactivate(self):
        """Deactivate the circle tool."""
        self.is_active = False
        self.canvas.delete("temp")
        self.canvas.delete("snap_indicator")
        self.canvas.delete("circle_info")
        self.is_first_click = True
        self.preview_circle_id = None
        self.info_display_id = None
        self.edit_mode = None
        self.edit_value = ""
        self.center_x = 0
        self.center_y = 0
        
        # Unbind keyboard events
        self.canvas.unbind("<Tab>")
        self.canvas.unbind("<Return>")
        self.canvas.unbind("<Escape>")
        self.canvas.unbind("<Key>")
        
    def get_cursor(self):
        """Get the cursor for this tool."""
        return "crosshair"
        
    def get_status_text(self):
        """Get the status text for this tool."""
        return "Drawing Circle - Click to place center, then radius"
        
    def _handle_click(self, event):
        """Handle mouse clicks for circle drawing."""
        # Only draw if clicking within work area
        if not self.sketching_stage.is_point_in_work_area(event.x, event.y):
            return
            
        # Apply snapping to click position
        snapped_x, snapped_y = self._apply_snap(event.x, event.y)
            
        if self.is_first_click:
            # First click: Store center point
            self.center_x, self.center_y = snapped_x, snapped_y
            
            # Create a temporary point marker
            self.canvas.create_oval(
                self.center_x-3, self.center_y-3, 
                self.center_x+3, self.center_y+3, 
                fill="gray", outline="black", tags="temp"
            )
            
            self.is_first_click = False
            
        else:
            # Second click: Use the finish circle method
            # Set the final coordinates for calculations
            final_x, final_y = self._apply_snap(event.x, event.y)
            self._calculate_circle_info(final_x, final_y)
            self._finish_circle()
            
    def _handle_motion(self, event, original_handler):
        """Handle mouse motion for circle preview."""
        # Apply snapping to motion coordinates
        snapped_x, snapped_y = self._apply_snap(event.x, event.y)
        
        # Show snap indicator if we're snapping
        if (snapped_x, snapped_y) != (event.x, event.y):
            self._draw_snap_indicator(snapped_x, snapped_y)
        else:
            self.canvas.delete("snap_indicator")
        
        # Update circle preview with snapped coordinates
        self._update_preview(snapped_x, snapped_y)
        
        # Call original motion handler for coordinate tracking
        if original_handler and hasattr(self.sketching_stage, '_update_coordinates'):
            # Create a mock event with snapped coordinates for accurate display
            mock_event = type('MockEvent', (), {'x': snapped_x, 'y': snapped_y})()
            self.sketching_stage._update_coordinates(mock_event)
            
    def _update_preview(self, x, y):
        """Update the preview circle as mouse moves.
        
        Args:
            x (float): X coordinate (potentially snapped)
            y (float): Y coordinate (potentially snapped)
        """
        # Only show preview if waiting for second click
        if not self.is_first_click:
            # Delete previous preview circle
            if self.preview_circle_id:
                self.canvas.delete(self.preview_circle_id)
                
            # Calculate display width based on zoom level
            display_width = max(1, int(self.line_width_mm * self.sketching_stage.zoom_level))
            
            # Calculate radius in canvas coordinates
            canvas_radius = self.radius_mm * self.sketching_stage.zoom_level
                
            # Create new preview circle with proper line width
            self.preview_circle_id = self.canvas.create_oval(
                self.center_x - canvas_radius, self.center_y - canvas_radius,
                self.center_x + canvas_radius, self.center_y + canvas_radius,
                outline="gray", width=display_width, dash=(4, 2), tags="temp"
            )
            
            # Calculate circle radius
            self._calculate_circle_info(x, y)
            
            # Show circle information
            self._update_circle_info_display()
            
    def _update_preview_with_width(self):
        """Update the preview circle with new line width."""
        if not self.is_first_click and self.preview_circle_id:
            # Delete old preview
            self.canvas.delete(self.preview_circle_id)
            
            # Calculate display width based on zoom level
            display_width = max(1, int(self.line_width_mm * self.sketching_stage.zoom_level))
            
            # Calculate radius in canvas coordinates
            canvas_radius = self.radius_mm * self.sketching_stage.zoom_level
            
            # Create new preview with updated width
            self.preview_circle_id = self.canvas.create_oval(
                self.center_x - canvas_radius, self.center_y - canvas_radius,
                self.center_x + canvas_radius, self.center_y + canvas_radius,
                outline="gray", width=display_width, dash=(4, 2), tags="temp"
            )
                
    def _calculate_circle_info(self, edge_x, edge_y):
        """Calculate radius of the current circle.
        
        Args:
            edge_x (float): Current edge X coordinate
            edge_y (float): Current edge Y coordinate
        """
        # Convert canvas coordinates to real mm coordinates
        center_mm_x, center_mm_y = self.sketching_stage.canvas_to_mm(self.center_x, self.center_y)
        self.current_mm_x, self.current_mm_y = self.sketching_stage.canvas_to_mm(edge_x, edge_y)
        
        # Calculate radius in mm
        dx = self.current_mm_x - center_mm_x
        dy = self.current_mm_y - center_mm_y
        self.radius_mm = (dx**2 + dy**2)**0.5
        
    def _update_circle_info_display(self):
        """Update or create the circle information display."""
        # Remove existing info display
        self.canvas.delete("circle_info")
        
        # Set display text based on edit mode
        if self.edit_mode == 'radius':
            radius_text = self.edit_value + "▋"  # Add cursor
            line_width_text = f"Line Width: {self.line_width_mm:.2f}mm"
        elif self.edit_mode == 'line_width':
            radius_text = f"Radius: {self.radius_mm:.1f}mm"
            line_width_text = self.edit_value + "▋"  # Add cursor
        else:
            radius_text = f"Radius: {self.radius_mm:.1f}mm"
            line_width_text = f"Line Width: {self.line_width_mm:.2f}mm"
        
        # Status text with instructions
        status_text = "Tab: Edit values | Enter: Confirm | Esc: Cancel"
        
        # Calculate position for the info display (center bottom of canvas)
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        x_pos = canvas_width // 2
        y_pos = canvas_height - 50
        
        # Create text items
        self.info_display_id = self.canvas.create_text(
            x_pos, y_pos, 
            text=f"{radius_text}   {line_width_text}\n{status_text}",
            fill="black", font=("Arial", 10), justify=tk.CENTER,
            tags="circle_info temp"
        )
        
        # Create background rectangle for better visibility
        bbox = self.canvas.bbox(self.info_display_id)
        if bbox:
            padding = 10
            self.canvas.create_rectangle(
                bbox[0] - padding, bbox[1] - padding,
                bbox[2] + padding, bbox[3] + padding,
                fill="lightyellow", outline="gray",
                tags="circle_info temp"
            )
            # Move text to front
            self.canvas.tag_raise(self.info_display_id)
    
    def _handle_tab(self, event):
        """Handle tab key press to switch between editing modes."""
        if not self.is_first_click:  # Only when drawing a circle
            if self.edit_mode is None:
                # Enter radius edit mode
                self.edit_mode = 'radius'
                self.edit_value = f"{self.radius_mm:.1f}"
            elif self.edit_mode == 'radius':
                # Switch to line width edit mode
                self.edit_mode = 'line_width'
                self.edit_value = f"{self.line_width_mm:.2f}"
            elif self.edit_mode == 'line_width':
                # Back to radius edit mode
                self.edit_mode = 'radius'
                self.edit_value = f"{self.radius_mm:.1f}"
                
            self._update_circle_info_display()
            return "break"  # Prevent default tab behavior
        
    def _handle_enter(self, event):
        """Handle enter key press to confirm edits or create circle."""
        if not self.is_first_click:  # Only when drawing a circle
            if self.edit_mode == 'radius':
                # Apply radius change
                try:
                    new_radius = float(self.edit_value)
                    if new_radius > 0:
                        self._apply_new_radius(new_radius)
                except ValueError:
                    pass  # Invalid input, ignore
                    
                # Switch to line width edit mode
                self.edit_mode = 'line_width'
                self.edit_value = f"{self.line_width_mm:.2f}"
                self._update_circle_info_display()
                
            elif self.edit_mode == 'line_width':
                # Apply line width change
                try:
                    new_line_width = float(self.edit_value)
                    if new_line_width > 0:
                        self.line_width_mm = new_line_width
                        self._update_preview_with_width()
                except ValueError:
                    pass  # Invalid input, ignore
                    
                # Exit edit mode
                self.edit_mode = None
                self._update_circle_info_display()
                
            else:
                # Not in edit mode, create the circle
                self._finish_circle()
                
            return "break"  # Prevent default enter behavior
        
    def _handle_escape(self, event):
        """Handle escape key press to cancel edits or drawing."""
        if not self.is_first_click:  # Only when drawing a circle
            if self.edit_mode:
                # Cancel edit mode
                self.edit_mode = None
                self._update_circle_info_display()
            else:
                # Cancel circle drawing
                self.canvas.delete("temp")
                self.canvas.delete("circle_info")
                self.is_first_click = True
                self.preview_circle_id = None
                
            return "break"  # Prevent default escape behavior
            
    def _handle_key(self, event):
        """Handle regular key presses during edit mode."""
        if self.edit_mode and not self.is_first_click:
            if event.keysym == 'BackSpace':
                # Handle backspace
                self.edit_value = self.edit_value[:-1] if self.edit_value else ""
            elif event.keysym in ('Right', 'Left', 'Up', 'Down'):
                # Ignore arrow keys
                pass
            elif event.char and (event.char.isdigit() or event.char in '.,-'):
                # Accept digits and decimal point for editing
                self.edit_value += event.char
                
            self._update_circle_info_display()
            return "break"  # Prevent default key behavior
            
    def _apply_new_radius(self, new_radius):
        """Apply a new radius to the circle being drawn.
        
        Args:
            new_radius (float): The new radius in mm
        """
        # Update circle radius
        self.radius_mm = new_radius
        
        # Calculate display width based on zoom level
        display_width = max(1, int(self.line_width_mm * self.sketching_stage.zoom_level))
        
        # Calculate radius in canvas coordinates
        canvas_radius = self.radius_mm * self.sketching_stage.zoom_level
        
        # Update preview with real width
        self.canvas.delete(self.preview_circle_id)
        self.preview_circle_id = self.canvas.create_oval(
            self.center_x - canvas_radius, self.center_y - canvas_radius,
            self.center_x + canvas_radius, self.center_y + canvas_radius,
            outline="gray", width=display_width, dash=(4, 2), tags="temp"
        )
        
    def _finish_circle(self):
        """Finish circle creation with current parameters."""
        # Calculate display width based on zoom level
        display_width = max(1, int(self.line_width_mm * self.sketching_stage.zoom_level))
        
        # Calculate radius in canvas coordinates
        canvas_radius = self.radius_mm * self.sketching_stage.zoom_level
        
        # Create the final circle with real-world line width
        self.canvas.create_oval(
            self.center_x - canvas_radius, self.center_y - canvas_radius,
            self.center_x + canvas_radius, self.center_y + canvas_radius,
            outline="black", width=display_width, tags="drawing"
        )
        
        # Get center in mm coordinates
        center_mm_x, center_mm_y = self.sketching_stage.canvas_to_mm(self.center_x, self.center_y)
        
        # Store the drawing object with line width in mm
        self.sketching_stage.add_drawing_object(
            'circle',
            [center_mm_x, center_mm_y, self.radius_mm],  # center_x, center_y, radius
            {'outline': 'black', 'width_mm': self.line_width_mm, 'fill': ''}
        )
        
        # Add reference point at center
        self.sketching_stage.add_drawing_object(
            'reference_point',
            [center_mm_x, center_mm_y],
            {'color': 'blue'}
        )
        
        # Add reference points at cardinal directions on circumference
        import math
        for angle in [0, 90, 180, 270]:  # Right, Top, Left, Bottom
            angle_rad = math.radians(angle)
            ref_x = center_mm_x + self.radius_mm * math.cos(angle_rad)
            ref_y = center_mm_y + self.radius_mm * math.sin(angle_rad)
            self.sketching_stage.add_drawing_object(
                'reference_point',
                [ref_x, ref_y],
                {'color': 'blue'}
            )
        
        # Clean up and reset
        self.canvas.delete("temp")
        self.canvas.delete("circle_info")
        self.is_first_click = True
        self.preview_circle_id = None
        self.edit_mode = None


class DrawingToolManager:
    """Manages drawing tools and their states."""
    
    def __init__(self, canvas, sketching_stage, tools_frame, status_var):
        """Initialize the drawing tool manager.
        
        Args:
            canvas (tk.Canvas): The canvas to draw on
            sketching_stage (SketchingStage): Reference to the sketching stage
            tools_frame (tk.Frame): Frame to place tool buttons
            status_var (tk.StringVar): Status variable to update
        """
        self.canvas = canvas
        self.sketching_stage = sketching_stage
        self.tools_frame = tools_frame
        self.status_var = status_var
        
        # Initialize tools
        self.tools = {
            'select': SelectTool(canvas, sketching_stage),
            'line': LineTool(canvas, sketching_stage),
            'rectangle': RectangleTool(canvas, sketching_stage),
            'circle': CircleTool(canvas, sketching_stage),
            'image': ImageTool(canvas, sketching_stage),
            'origin': OriginTool(canvas, sketching_stage)
        }
        
        self.current_tool = None
        self.tool_buttons = {}
        
        # Store icon references to prevent garbage collection
        self.line_icon = None
        self.rectangle_icon = None
        self.circle_icon = None
        self.image_icon = None
        self.origin_icon = None
        
        # Create tool buttons
        self._create_tool_buttons()
        
        # Start with select tool
        self.set_active_tool('select')
        
    def _load_icon(self, icon_name, size=(20, 20)):
        """Load an icon image for buttons.
        
        Args:
            icon_name (str): Name of the icon file (without .png extension)
            size (tuple): Size to resize the icon to (width, height)
            
        Returns:
            ImageTk.PhotoImage or None: The loaded icon or None if failed
        """
        try:
            icon_path = f"/Users/michaeljornist/Desktop/CS/G2burn/icons/{icon_name}.png"
            image = Image.open(icon_path)
            image = image.resize(size, Image.Resampling.LANCZOS)
            photo_image = ImageTk.PhotoImage(image)
            return photo_image
        except Exception as e:
            print(f"Could not load icon {icon_name}: {e}")
            return None
        
    def _create_tool_buttons(self):
        """Create buttons for each tool with compact sizing."""
        # Use compact sizing for all buttons
        btn_width = 40   # Compact size
        btn_height = 40  # Compact size
        icon_size = 35   # Smaller icons
        text_width = 7   # Smaller text buttons
        font_size = 8    # Smaller font
        
        # Select tool button (text for now)
        self.tool_buttons['select'] = tk.Button(
            self.tools_frame,
            text="Select",
            width=text_width,
            font=("Arial", font_size),
            command=lambda: self.set_active_tool('select')
        )
        self.tool_buttons['select'].pack(side=tk.LEFT, padx=1, pady=2)
        
        # Line tool button with icon
        try:
            line_icon_path = "/Users/michaeljornist/Desktop/CS/G2burn/icons/line.png"
            line_image = Image.open(line_icon_path)
            line_image = line_image.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
            self.line_icon = ImageTk.PhotoImage(line_image)
            
            self.tool_buttons['line'] = tk.Button(
                self.tools_frame,
                image=self.line_icon,
                width=btn_width,
                height=btn_height,
                relief='flat',
                borderwidth=0,
                highlightthickness=0,
                padx=0,
                pady=0,
                bg='#f0f0f0',
                activebackground='#e0e0e0',
                command=lambda: self.set_active_tool('line')
            )
            # Add tooltip
            ToolTip(self.tool_buttons['line'], "Line Tool\nDraw lines between two points")
        except Exception as e:
            print(f"Could not load line icon: {e}")
            # Fallback to text
            self.tool_buttons['line'] = tk.Button(
                self.tools_frame,
                text="Line",
                width=text_width,
                font=("Arial", font_size),
                command=lambda: self.set_active_tool('line')
            )
        self.tool_buttons['line'].pack(side=tk.LEFT, padx=1, pady=2)
        
        # Rectangle tool button with icon
        try:
            rectangle_icon_path = "/Users/michaeljornist/Desktop/CS/G2burn/icons/rectangle.png"
            rectangle_image = Image.open(rectangle_icon_path)
            rectangle_image = rectangle_image.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
            self.rectangle_icon = ImageTk.PhotoImage(rectangle_image)
            
            self.tool_buttons['rectangle'] = tk.Button(
                self.tools_frame,
                image=self.rectangle_icon,
                width=btn_width,
                height=btn_height,
                relief='flat',
                borderwidth=0,
                highlightthickness=0,
                padx=0,
                pady=0,
                bg='#f0f0f0',
                activebackground='#e0e0e0',
                command=lambda: self.set_active_tool('rectangle')
            )
            # Add tooltip
            ToolTip(self.tool_buttons['rectangle'], "Rectangle Tool\nDraw rectangles with two clicks")
        except Exception as e:
            print(f"Could not load rectangle icon: {e}")
            # Fallback to text
            self.tool_buttons['rectangle'] = tk.Button(
                self.tools_frame,
                text="Rectangle",
                width=text_width,
                font=("Arial", font_size),
                command=lambda: self.set_active_tool('rectangle')
            )
        self.tool_buttons['rectangle'].pack(side=tk.LEFT, padx=1, pady=2)
        
        # Circle tool button with icon
        try:
            circle_icon_path = "/Users/michaeljornist/Desktop/CS/G2burn/icons/circle.png"
            circle_image = Image.open(circle_icon_path)
            circle_image = circle_image.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
            self.circle_icon = ImageTk.PhotoImage(circle_image)
            
            self.tool_buttons['circle'] = tk.Button(
                self.tools_frame,
                image=self.circle_icon,
                width=btn_width,
                height=btn_height,
                relief='flat',
                borderwidth=0,
                highlightthickness=0,
                padx=0,
                pady=0,
                bg='#f0f0f0',
                activebackground='#e0e0e0',
                command=lambda: self.set_active_tool('circle')
            )
            # Add tooltip
            ToolTip(self.tool_buttons['circle'], "Circle Tool\nDraw circles by center and radius")
        except Exception as e:
            print(f"Could not load circle icon: {e}")
            # Fallback to text
            self.tool_buttons['circle'] = tk.Button(
                self.tools_frame,
                text="Circle",
                width=text_width,
                font=("Arial", font_size),
                command=lambda: self.set_active_tool('circle')
            )
        self.tool_buttons['circle'].pack(side=tk.LEFT, padx=1, pady=2)
        
        # Image tool button with icon
        try:
            image_icon_path = "/Users/michaeljornist/Desktop/CS/G2burn/icons/add_image.png"
            image_image = Image.open(image_icon_path)
            image_image = image_image.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
            self.image_icon = ImageTk.PhotoImage(image_image)
            
            self.tool_buttons['image'] = tk.Button(
                self.tools_frame,
                image=self.image_icon,
                width=btn_width,
                height=btn_height,
                relief='flat',
                borderwidth=0,
                highlightthickness=0,
                padx=0,
                pady=0,
                bg='#f0f0f0',
                activebackground='#e0e0e0',
                command=lambda: self.set_active_tool('image')
            )
            # Add tooltip
            ToolTip(self.tool_buttons['image'], "Image Tool\nAdd images to your design")
        except Exception as e:
            print(f"Could not load image icon: {e}")
            # Fallback to text
            self.tool_buttons['image'] = tk.Button(
                self.tools_frame,
                text="Image",
                width=text_width,
                font=("Arial", font_size),
                command=lambda: self.set_active_tool('image')
            )
        self.tool_buttons['image'].pack(side=tk.LEFT, padx=1, pady=2)
        
        # Origin tool button with icon
        origin_icon = self._load_icon("place_origin", (icon_size, icon_size))
        if origin_icon:
            self.origin_icon = origin_icon
            self.tool_buttons['origin'] = tk.Button(
                self.tools_frame,
                image=self.origin_icon,
                width=btn_width,
                height=btn_height,
                relief='flat',
                borderwidth=0,
                highlightthickness=0,
                padx=0,
                pady=0,
                bg='#FFE6E6',  # Light red background
                activebackground='#FFD6D6',
                command=lambda: self.set_active_tool('origin')
            )
        else:
            # Fallback to text
            self.tool_buttons['origin'] = tk.Button(
                self.tools_frame,
                text="Origin",
                width=text_width,
                font=("Arial", font_size),
                command=lambda: self.set_active_tool('origin'),
                bg="#FFE6E6"  # Light red background
            )
        self.tool_buttons['origin'].pack(side=tk.LEFT, padx=1, pady=2)
        # Add tooltip
        ToolTip(self.tool_buttons['origin'], "Origin Tool\nSet the origin point (0,0)")
        
        # Home/Fit button to reset view (zoom to fit whole work area)
        home_btn = tk.Button(
            self.tools_frame,
            text="🏠",
            width=text_width,
            font=("Arial", font_size),
            command=self.sketching_stage.reset_view,
            bg="#E6F3FF"  # Light blue background
        )
        home_btn.pack(side=tk.LEFT, padx=1, pady=2)
        # Add tooltip
        ToolTip(home_btn, "Fit to View\nZoom out to see entire work area")
        
        # Snap toggle button (text for now)
        self.snap_btn = tk.Button(
            self.tools_frame,
            text="Snap",
            width=text_width,
            font=("Arial", font_size),
            command=self.toggle_snap,
            bg="#90EE90"  # Light green when enabled
        )
        self.snap_btn.pack(side=tk.LEFT, padx=1, pady=2)
        
    def toggle_snap(self):
        """Toggle snap-to-point functionality for all tools."""
        # Toggle snap for all tools
        snap_enabled = not self.tools['line'].snap_enabled
        
        for tool in self.tools.values():
            tool.snap_enabled = snap_enabled
            
        # Update button appearance
        if snap_enabled:
            self.snap_btn.config(text="Snap: ON", bg="#90EE90")  # Light green
        else:
            self.snap_btn.config(text="Snap: OFF", bg="#FFB6C1")  # Light red
            
        # Clear any existing snap indicators
        self.canvas.delete("snap_indicator")
        
    def set_active_tool(self, tool_name):
        """Set the active drawing tool.
        
        Args:
            tool_name (str): Name of the tool to activate
        """
        # Deactivate current tool
        if self.current_tool:
            self.current_tool.deactivate()
            
        # Clear temporary elements
        self.canvas.delete("temp")
        
        # Activate new tool
        if tool_name in self.tools:
            self.current_tool = self.tools[tool_name]
            self.current_tool.activate()
            
            # Update status
            self.status_var.set(f"Mode: {self.current_tool.get_status_text()}")
            
            # Update button appearances
            self._update_button_appearance(tool_name)
            
    def _update_button_appearance(self, active_tool):
        """Update button appearances to show active tool.
        
        Args:
            active_tool (str): Name of the currently active tool
        """
        for tool_name, button in self.tool_buttons.items():
            if tool_name == active_tool:
                # Active button - highlighted with border and different background
                if hasattr(button, 'image') and button.image:
                    # Icon button - blue border and light blue background
                    button.config(
                        relief='solid', 
                        bg="#b8d4f1",  # Light blue background
                        borderwidth=2,
                        highlightthickness=2,
                        highlightcolor="#0078d4",  # Blue border
                        highlightbackground="#0078d4"
                    )
                else:
                    # Text button - blue border and light blue background
                    button.config(
                        relief='solid', 
                        bg="#b8d4f1",  # Light blue background
                        borderwidth=2,
                        highlightthickness=2,
                        highlightcolor="#0078d4",  # Blue border
                        highlightbackground="#0078d4"
                    )
            else:
                # Inactive button - normal flat appearance
                if hasattr(button, 'image') and button.image:
                    # Icon button - flat with light gray background
                    button.config(
                        relief='flat', 
                        bg="#f0f0f0", 
                        borderwidth=1,
                        highlightthickness=0
                    )
                else:
                    # Text button - raised with default background
                    button.config(
                        relief='raised', 
                        bg="#f0f0f0",
                        borderwidth=1,
                        highlightthickness=0
                    )
                
    def get_current_tool(self):
        """Get the currently active tool.
        
        Returns:
            DrawingTool: The currently active tool, or None
        """
        return self.current_tool
