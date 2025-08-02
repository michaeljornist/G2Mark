"""
SketchingStage class for the G2burn Laser Engraving Application.
This class manages the drawing workspace where users create their designs.
"""

import tkinter as tk
from tkinter import messagebox, filedialog
from drawing_tools import DrawingToolManager
from gcode_generator import GCodeGenerator


class SketchingStage:
    """Manages the sketching workspace for creating laser engraving designs."""
    
    def __init__(self, project_name, height_mm, length_mm, parent_window):
        """Initialize the sketching stage.
        
        Args:
            project_name (str): Name of the project
            height_mm (float): Height of the work area in millimeters
            length_mm (float): Length of the work area in millimeters
            parent_window (tk.Tk): Parent window reference
        """
        self.project_name = project_name
        self.height_mm = height_mm
        self.length_mm = length_mm
        self.parent_window = parent_window
        
        # Window and UI components
        self.window = None
        self.canvas = None
        self.status_var = None
        self.zoom_var = None
        self.coord_var = None
        
        # Workspace state
        self.zoom_level = 1.0
        self.center_x = 0
        self.center_y = 0
        self.work_area_objects = []
        self.drawing_objects = []
        
        # Pan state
        self.pan_start_x = 0
        self.pan_start_y = 0
        
        # Drawing tools manager
        self.drawing_tool_manager = None
        
        # GCode generator
        self.gcode_generator = None
        
    def show(self):
        """Display the sketching stage window."""
        self._create_window()
        self._setup_layout()
        self._setup_canvas()
        self._setup_drawing_tools()
        self._setup_gcode_generator()
        self._bind_events()
        self._initialize_work_area()
        
    def _create_window(self):
        """Create the main sketching window."""
        self.window = tk.Toplevel(self.parent_window)
        self.window.title(f"G2burn - {self.project_name}")
        
        # Set window to fullscreen
        self.window.attributes('-fullscreen', True)
        
        # Add ability to exit fullscreen with Escape key
        self.window.bind('<Escape>', lambda e: self.window.attributes('-fullscreen', False))
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        
    def _setup_layout(self):
        """Setup the main layout structure."""
        # Menu bar at the top
        self.menu_frame = tk.Frame(self.window, height=40, bg="#f0f0f0")
        self.menu_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Main content area
        self.content_frame = tk.Frame(self.window)
        self.content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Status bar at the bottom
        self.status_frame = tk.Frame(self.window, height=25, bg="#f0f0f0")
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self._create_menu_bar()
        self._create_status_bar()
        
    def _create_menu_bar(self):
        """Create the menu bar with tools and options."""
        btn_width = 10
        
        # File operations
        file_frame = tk.Frame(self.menu_frame, bg="#f0f0f0")
        file_frame.pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            file_frame, 
            text="Save", 
            width=btn_width, 
            command=self.save_project
        ).pack(side=tk.LEFT, padx=2, pady=5)
        
        tk.Button(
            file_frame, 
            text="Export", 
            width=btn_width, 
            command=self.export_project
        ).pack(side=tk.LEFT, padx=2, pady=5)
        
        # Tool buttons
        self.tools_frame = tk.Frame(self.menu_frame, bg="#f0f0f0")
        self.tools_frame.pack(side=tk.LEFT, padx=5)
        
        # View controls
        view_frame = tk.Frame(self.menu_frame, bg="#f0f0f0")
        view_frame.pack(side=tk.RIGHT, padx=5)
        
        tk.Button(
            view_frame, 
            text="Zoom In", 
            width=btn_width,
            command=lambda: self.zoom_canvas(1.25)
        ).pack(side=tk.LEFT, padx=2, pady=5)
        
        tk.Button(
            view_frame, 
            text="Zoom Out", 
            width=btn_width,
            command=lambda: self.zoom_canvas(0.8)
        ).pack(side=tk.LEFT, padx=2, pady=5)
        
        tk.Button(
            view_frame, 
            text="Reset View", 
            width=btn_width,
            command=self.reset_view
        ).pack(side=tk.LEFT, padx=2, pady=5)
        
        tk.Button(
            view_frame, 
            text="G-Code", 
            width=btn_width,
            command=self.generate_gcode
        ).pack(side=tk.LEFT, padx=2, pady=5)
        
    def _create_status_bar(self):
        """Create the status bar with indicators."""
        # Mode indicator
        self.status_var = tk.StringVar()
        self.status_var.set("Mode: Select")
        status_label = tk.Label(
            self.status_frame, 
            textvariable=self.status_var, 
            font=("Arial", 9), 
            bd=1, 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        status_label.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=2, expand=True)
        
        # Zoom indicator
        self.zoom_var = tk.StringVar()
        self.zoom_var.set("Zoom: 100%")
        zoom_label = tk.Label(
            self.status_frame, 
            textvariable=self.zoom_var, 
            font=("Arial", 9), 
            bd=1, 
            relief=tk.SUNKEN, 
            width=12
        )
        zoom_label.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=2)
        
        # Coordinates indicator
        self.coord_var = tk.StringVar()
        self.coord_var.set("X: 0mm Y: 0mm")
        coord_label = tk.Label(
            self.status_frame, 
            textvariable=self.coord_var, 
            font=("Arial", 9), 
            bd=1, 
            relief=tk.SUNKEN, 
            width=16
        )
        coord_label.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=2)
        
    def _setup_canvas(self):
        """Setup the main drawing canvas."""
        # Create canvas frame
        canvas_frame = tk.Frame(self.content_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Get screen dimensions
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        # Create canvas with dark background
        self.canvas = tk.Canvas(
            canvas_frame, 
            bg="#303030", 
            relief=tk.SUNKEN, 
            bd=0,
            highlightthickness=0, 
            width=screen_width-40, 
            height=screen_height-100
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
    def _setup_drawing_tools(self):
        """Setup the drawing tools manager."""
        self.drawing_tool_manager = DrawingToolManager(
            canvas=self.canvas,
            sketching_stage=self,
            tools_frame=self.tools_frame,
            status_var=self.status_var
        )
        
    def _setup_gcode_generator(self):
        """Setup the G-code generator."""
        self.gcode_generator = GCodeGenerator(
            canvas=self.canvas,
            sketching_stage=self
        )
        
    def _bind_events(self):
        """Bind mouse and keyboard events."""
        # Mouse wheel for zooming
        self.canvas.bind("<MouseWheel>", self._handle_mouse_zoom)  # Windows/MacOS
        self.canvas.bind("<Button-4>", self._handle_mouse_zoom)    # Linux scroll up
        self.canvas.bind("<Button-5>", self._handle_mouse_zoom)    # Linux scroll down
        
        # Middle mouse button for panning
        self.canvas.bind("<ButtonPress-2>", self._start_pan)
        self.canvas.bind("<B2-Motion>", self._pan_canvas)
        self.canvas.bind("<ButtonRelease-2>", self._end_pan)
        
        # Mouse movement for coordinate tracking
        self.canvas.bind("<Motion>", self._update_coordinates)
        
    def _initialize_work_area(self):
        """Initialize the work area display."""
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        # Calculate initial scaling to fit work area
        max_width = int(screen_width * 0.7)
        max_height = int(screen_height * 0.7)
        
        width_scale = max_width / self.length_mm
        height_scale = max_height / self.height_mm
        initial_scale = min(width_scale, height_scale)
        
        # Set initial zoom and center position
        self.zoom_level = initial_scale
        self.center_x = screen_width // 2
        self.center_y = screen_height // 2
        
        # Draw the work area
        self._draw_work_area()
        
        # Update zoom display
        zoom_percent = int(self.zoom_level * 100)
        self.zoom_var.set(f"Zoom: {zoom_percent}%")
        
    def _draw_work_area(self):
        """Draw the work area with grid and rulers."""
        # Clear previous work area objects
        for obj_id in self.work_area_objects:
            self.canvas.delete(obj_id)
        self.work_area_objects = []
        
        # Calculate current dimensions
        width = int(self.length_mm * self.zoom_level)
        height = int(self.height_mm * self.zoom_level)
        
        # Calculate top-left corner
        x1 = self.center_x - (width // 2)
        y1 = self.center_y - (height // 2)
        x2 = x1 + width
        y2 = y1 + height
        
        # Draw white background
        bg_id = self.canvas.create_rectangle(
            x1, y1, x2, y2, 
            fill="white", 
            outline="gray"
        )
        self.work_area_objects.append(bg_id)
        
        # Draw border
        border_id = self.canvas.create_rectangle(
            x1, y1, x2, y2, 
            outline="black", 
            width=2
        )
        self.work_area_objects.append(border_id)
        
        # Draw grid
        self._draw_grid(x1, y1, width, height)
        
        # Draw rulers
        self._draw_rulers(x1, y1, width, height)
        
    def _draw_grid(self, x1, y1, width, height):
        """Draw grid lines in the work area."""
        cells = 20
        x_spacing = width / cells
        y_spacing = height / cells
        
        # Vertical lines
        for i in range(1, cells):
            x = x1 + (i * x_spacing)
            line_id = self.canvas.create_line(
                x, y1, x, y1 + height, 
                fill="lightgray", 
                dash=(1, 1)
            )
            self.work_area_objects.append(line_id)
            
        # Horizontal lines
        for i in range(1, cells):
            y = y1 + (i * y_spacing)
            line_id = self.canvas.create_line(
                x1, y, x1 + width, y, 
                fill="lightgray", 
                dash=(1, 1)
            )
            self.work_area_objects.append(line_id)
            
    def _draw_rulers(self, x1, y1, width, height):
        """Draw rulers around the work area."""
        ruler_width = 20
        
        # Top ruler background
        top_ruler_id = self.canvas.create_rectangle(
            x1, y1 - ruler_width, x1 + width, y1, 
            fill="#f0f0f0", 
            outline="gray"
        )
        self.work_area_objects.append(top_ruler_id)
        
        # Left ruler background
        left_ruler_id = self.canvas.create_rectangle(
            x1 - ruler_width, y1, x1, y1 + height, 
            fill="#f0f0f0", 
            outline="gray"
        )
        self.work_area_objects.append(left_ruler_id)
        
        # Top ruler ticks and labels
        tick_spacing = width / 10
        for i in range(11):
            tick_x = x1 + (i * tick_spacing)
            
            # Tick mark
            tick_id = self.canvas.create_line(
                tick_x, y1 - 5, tick_x, y1,
                fill="black"
            )
            self.work_area_objects.append(tick_id)
            
            # Label
            mm_value = int((i / 10) * self.length_mm)
            label_id = self.canvas.create_text(
                tick_x, y1 - 10,
                text=f"{mm_value}",
                font=("Arial", 7),
                anchor="s"
            )
            self.work_area_objects.append(label_id)
            
        # Left ruler ticks and labels
        tick_spacing = height / 10
        for i in range(11):
            tick_y = y1 + (i * tick_spacing)
            
            # Tick mark
            tick_id = self.canvas.create_line(
                x1 - 5, tick_y, x1, tick_y,
                fill="black"
            )
            self.work_area_objects.append(tick_id)
            
            # Label
            mm_value = int((i / 10) * self.height_mm)
            label_id = self.canvas.create_text(
                x1 - 10, tick_y,
                text=f"{mm_value}",
                font=("Arial", 7),
                anchor="e"
            )
            self.work_area_objects.append(label_id)
            
    def zoom_canvas(self, factor):
        """Zoom the canvas by the specified factor."""
        self.zoom_level *= factor
        
        # Update zoom display
        zoom_percent = int(self.zoom_level * 100)
        self.zoom_var.set(f"Zoom: {zoom_percent}%")
        
        # Redraw everything
        self._redraw_all()
        
    def _handle_mouse_zoom(self, event):
        """Handle mouse wheel zoom events."""
        # Determine zoom direction
        if event.num == 4 or event.delta > 0:  # Zoom in
            factor = 1.1
        else:  # Zoom out
            factor = 0.9
            
        self.zoom_canvas(factor)
        
    def _start_pan(self, event):
        """Start canvas panning operation."""
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        self.canvas.config(cursor="fleur")
        
    def _pan_canvas(self, event):
        """Pan the canvas based on mouse movement."""
        dx = event.x - self.pan_start_x
        dy = event.y - self.pan_start_y
        
        # Update center position
        self.center_x += dx
        self.center_y += dy
        
        # Update pan start position
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        
        # Redraw everything
        self._redraw_all()
        
    def _end_pan(self, event):
        """End canvas panning operation."""
        self.canvas.config(cursor="")
        
    def _update_coordinates(self, event):
        """Update coordinate display based on mouse position."""
        # Calculate work area bounds
        width = int(self.length_mm * self.zoom_level)
        height = int(self.height_mm * self.zoom_level)
        x1 = self.center_x - (width // 2)
        y1 = self.center_y - (height // 2)
        
        # Check if mouse is within work area
        if (x1 <= event.x <= x1 + width and y1 <= event.y <= y1 + height):
            # Convert to mm coordinates
            mm_x = (event.x - x1) / self.zoom_level
            mm_y = (event.y - y1) / self.zoom_level
            self.coord_var.set(f"X: {mm_x:.1f}mm Y: {mm_y:.1f}mm")
        else:
            self.coord_var.set("X: -- Y: --")
            
    def _redraw_all(self):
        """Redraw all elements on the canvas."""
        # Clear canvas
        self.canvas.delete("all")
        
        # Redraw work area
        self._draw_work_area()
        
        # Redraw drawing objects
        self._redraw_drawing_objects()
        
    def _redraw_drawing_objects(self):
        """Redraw all stored drawing objects."""
        # Calculate work area bounds
        width = int(self.length_mm * self.zoom_level)
        height = int(self.height_mm * self.zoom_level)
        x1 = self.center_x - (width // 2)
        y1 = self.center_y - (height // 2)
        
        # Redraw each object
        for drawing_obj in self.drawing_objects:
            obj_type = drawing_obj['type']
            real_coords = drawing_obj['real_coords']
            properties = drawing_obj['properties']
            
            # Convert real coordinates to canvas coordinates
            canvas_coords = []
            for i in range(0, len(real_coords), 2):
                canvas_x = x1 + (real_coords[i] * self.zoom_level)
                canvas_y = y1 + (real_coords[i+1] * self.zoom_level)
                canvas_coords.extend([canvas_x, canvas_y])
                
            # Create the shape
            if obj_type == 'line':
                self.canvas.create_line(
                    canvas_coords,
                    fill=properties.get('fill', 'black'),
                    width=properties.get('width', 2),
                    tags="drawing"
                )
            elif obj_type == 'rectangle':
                self.canvas.create_rectangle(
                    canvas_coords,
                    outline=properties.get('outline', 'black'),
                    width=properties.get('width', 2),
                    fill=properties.get('fill', ''),
                    tags="drawing"
                )
                
    def reset_view(self):
        """Reset the view to initial state."""
        screen_width = self.canvas.winfo_width()
        screen_height = self.canvas.winfo_height()
        
        # Recalculate initial scaling
        max_width = int(screen_width * 0.7)
        max_height = int(screen_height * 0.7)
        
        width_scale = max_width / self.length_mm
        height_scale = max_height / self.height_mm
        initial_scale = min(width_scale, height_scale)
        
        # Reset zoom and position
        self.zoom_level = initial_scale
        self.center_x = screen_width // 2
        self.center_y = screen_height // 2
        
        # Update display
        zoom_percent = int(self.zoom_level * 100)
        self.zoom_var.set(f"Zoom: {zoom_percent}%")
        
        # Redraw everything
        self._redraw_all()
        
    def add_drawing_object(self, obj_type, real_coords, properties):
        """Add a drawing object to the workspace."""
        drawing_obj = {
            'type': obj_type,
            'real_coords': real_coords,
            'properties': properties
        }
        self.drawing_objects.append(drawing_obj)
        
    def clear_canvas(self):
        """Clear all drawings while preserving the work area."""
        self.drawing_objects = []
        self.canvas.delete("drawing")
        self.canvas.delete("temp")
        
    def get_work_area_bounds(self):
        """Get the current work area bounds in canvas coordinates."""
        width = int(self.length_mm * self.zoom_level)
        height = int(self.height_mm * self.zoom_level)
        x1 = self.center_x - (width // 2)
        y1 = self.center_y - (height // 2)
        return x1, y1, width, height
        
    def canvas_to_mm(self, canvas_x, canvas_y):
        """Convert canvas coordinates to mm coordinates."""
        x1, y1, _, _ = self.get_work_area_bounds()
        mm_x = (canvas_x - x1) / self.zoom_level
        mm_y = (canvas_y - y1) / self.zoom_level
        return mm_x, mm_y
        
    def is_point_in_work_area(self, canvas_x, canvas_y):
        """Check if a point is within the work area."""
        x1, y1, width, height = self.get_work_area_bounds()
        return (x1 <= canvas_x <= x1 + width and y1 <= canvas_y <= y1 + height)
        
    def save_project(self):
        """Save the current project."""
        messagebox.showinfo("Save", f"Project '{self.project_name}' saved.")
        # TODO: Implement actual save functionality
        
    def export_project(self):
        """Export the project to a file."""
        file_types = [
            ("G-code files", "*.gcode *.nc"),
            ("SVG files", "*.svg"),
            ("All files", "*.*")
        ]
        file_path = filedialog.asksaveasfilename(
            title="Export Project",
            defaultextension=".gcode",
            filetypes=file_types,
            initialfile=f"{self.project_name}"
        )
        if file_path:
            messagebox.showinfo("Export", f"Project exported to {file_path}")
            # TODO: Implement actual export functionality
            
    def generate_gcode(self):
        """Generate G-code from the current drawing objects."""
        if self.gcode_generator:
            self.gcode_generator.generate_and_show()
            
    def close(self):
        """Close the sketching stage."""
        if self.window:
            self.window.destroy()
