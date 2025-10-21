"""
SketchingStage class for the G2burn Laser Engraving Application.
This class manages the drawing workspace where users create their designs.
"""

import tkinter as tk
from tkinter import messagebox, filedialog
from drawing_tools import DrawingToolManager
from sketching_layers import SketchingLayers
from gcode_generator import GCodeGenerator
from PIL import Image, ImageDraw, ImageTk
import tempfile
import os
import numpy as np


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
        
        # Undo system
        self.object_counter = 0  # Unique ID counter for each drawing operation
        self.undo_stack = []     # Stack to track operation IDs for undo
        
        # Pan state
        self.pan_start_x = 0
        self.pan_start_y = 0
        
        # Drawing tools manager
        self.drawing_tool_manager = None
        
        # GCode generator
        self.gcode_generator = None
        
        # Store icon images to prevent garbage collection
        self.icon_images = {}
        
        # Advanced settings
        self.flip_colors = False  # Toggle for color inversion
        
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
            
            # Store reference to prevent garbage collection
            self.icon_images[icon_name] = photo_image
            return photo_image
        except Exception as e:
            print(f"Could not load icon {icon_name}: {e}")
            return None
        
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
        
        # Set window to take up most of the screen (90% of screen size) but not fullscreen
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        # Calculate window size (90% of screen)
        window_width = int(screen_width * 0.9)
        window_height = int(screen_height * 0.9)
        
        # Center the window
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # Set geometry
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Make window resizable
        self.window.resizable(True, True)
        
        # Set minimum size
        self.window.minsize(800, 600)
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        
    def _setup_layout(self):
        """Setup the main layout structure."""
        # Menu bar at the top
        self.menu_frame = tk.Frame(self.window, bg="#f0f0f0")
        self.menu_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Main content area (will contain left toolbar and workspace)
        self.content_frame = tk.Frame(self.window)
        self.content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Left toolbar frame (for drawing tools)
        self.left_toolbar_frame = tk.Frame(self.content_frame, width=80, bg="#e0e0e0")
        self.left_toolbar_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.left_toolbar_frame.pack_propagate(False)  # Maintain fixed width
        
        # Right workspace frame (canvas + layers panel)
        self.workspace_frame = tk.Frame(self.content_frame)
        self.workspace_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Status bar at the bottom
        self.status_frame = tk.Frame(self.window, height=25, bg="#f0f0f0")
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self._create_menu_bar()
        self._create_left_toolbar()
        self._create_status_bar()
    
    def _create_menu_bar(self):
        """Create the menu bar with file operations and view controls only."""
        btn_width = 9  # Slightly smaller buttons to fit more
        
        # File operations
        file_frame = tk.Frame(self.menu_frame, bg="#f0f0f0")
        file_frame.pack(side=tk.LEFT, padx=3)
        
        tk.Button(
            file_frame, 
            text="Save", 
            width=btn_width, 
            font=("Arial", 9),
            command=self.save_project
        ).pack(side=tk.LEFT, padx=1, pady=3)
        
        tk.Button(
            file_frame, 
            text="Export", 
            width=btn_width, 
            font=("Arial", 9),
            command=self.export_project
        ).pack(side=tk.LEFT, padx=1, pady=3)
        
        tk.Button(
            file_frame, 
            text="Hi-Res PNG", 
            width=btn_width, 
            font=("Arial", 9),
            command=self.export_high_res_png
        ).pack(side=tk.LEFT, padx=1, pady=3)
        
        tk.Button(
            file_frame, 
            text="Hi-Res v2", 
            width=btn_width, 
            font=("Arial", 9),
            command=self.export_high_res_png_v2
        ).pack(side=tk.LEFT, padx=1, pady=3)
        
        # View controls
        view_frame = tk.Frame(self.menu_frame, bg="#f0f0f0")
        view_frame.pack(side=tk.LEFT, padx=3)
        
        # Icon size for view buttons (match tool buttons)
        icon_size = (35, 35)  # Match the tool button icon size
        btn_width = 40
        btn_height = 40
        
        # Zoom In button with icon
        zoom_in_icon = self._load_icon("zoom_in", icon_size)
        if zoom_in_icon:
            zoom_in_btn = tk.Button(
                view_frame,
                image=zoom_in_icon,
                width=btn_width,
                height=btn_height,
                relief='flat',
                borderwidth=0,
                highlightthickness=0,
                padx=0,
                pady=0,
                bg='#f0f0f0',
                activebackground='#e0e0e0',
                command=lambda: self.zoom_canvas(1.25)
            )
        else:
            # Fallback to text
            zoom_in_btn = tk.Button(
                view_frame, 
                text="Zoom In", 
                width=btn_width,
                font=("Arial", 9),
                command=lambda: self.zoom_canvas(1.25)
            )
        zoom_in_btn.pack(side=tk.LEFT, padx=1, pady=3)
        
        # Zoom Out button with icon
        zoom_out_icon = self._load_icon("zoom_out", icon_size)
        if zoom_out_icon:
            zoom_out_btn = tk.Button(
                view_frame,
                image=zoom_out_icon,
                width=btn_width,
                height=btn_height,
                relief='flat',
                borderwidth=0,
                highlightthickness=0,
                padx=0,
                pady=0,
                bg='#f0f0f0',
                activebackground='#e0e0e0',
                command=lambda: self.zoom_canvas(0.8)
            )
        else:
            # Fallback to text
            zoom_out_btn = tk.Button(
                view_frame, 
                text="Zoom Out", 
                width=btn_width,
                font=("Arial", 9),
                command=lambda: self.zoom_canvas(0.8)
            )
        zoom_out_btn.pack(side=tk.LEFT, padx=1, pady=3)
        
        # Clear button with icon
        clear_icon = self._load_icon("clear", icon_size)
        if clear_icon:
            clear_btn = tk.Button(
                view_frame,
                image=clear_icon,
                width=btn_width,
                height=btn_height,
                relief='flat',
                borderwidth=0,
                highlightthickness=0,
                padx=0,
                pady=0,
                bg='#f0f0f0',
                activebackground='#e0e0e0',
                command=self.clear_canvas
            )
        else:
            # Fallback to text
            clear_btn = tk.Button(
                view_frame, 
                text="Clear", 
                width=btn_width,
                font=("Arial", 9),
                command=self.clear_canvas
            )
        clear_btn.pack(side=tk.LEFT, padx=1, pady=3)
        
        tk.Button(
            view_frame, 
            text="Reset View", 
            width=btn_width,
            font=("Arial", 9),
            command=self.reset_view
        ).pack(side=tk.LEFT, padx=1, pady=3)
        
        tk.Button(
            view_frame, 
            text="G-Code", 
            width=btn_width,
            font=("Arial", 9),
            command=self.generate_gcode
        ).pack(side=tk.LEFT, padx=1, pady=3)
        
        tk.Button(
            view_frame, 
            text="Engrave", 
            width=btn_width,
            font=("Arial", 9),
            command=self.start_engrave_workflow
        ).pack(side=tk.LEFT, padx=1, pady=3)
        
        # Advanced settings button
        tk.Button(
            view_frame, 
            text="Advanced", 
            width=btn_width,
            font=("Arial", 9),
            command=self.show_advanced_settings
        ).pack(side=tk.LEFT, padx=1, pady=3)
        
    def _create_left_toolbar(self):
        """Create the left toolbar with drawing tools arranged vertically."""
        # Title for the toolbar
        toolbar_title = tk.Label(
            self.left_toolbar_frame, 
            text="Tools", 
            font=("Arial", 10, "bold"), 
            bg="#e0e0e0"
        )
        toolbar_title.pack(pady=(5, 10))
        
        # Tools frame container (will be populated by DrawingToolManager)
        self.tools_frame = tk.Frame(self.left_toolbar_frame, bg="#e0e0e0")
        self.tools_frame.pack(fill=tk.BOTH, expand=True, padx=5)
        
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
        """Setup the main drawing canvas with workspace layout."""
        # Create main workspace frame (canvas + layers panel)
        self.workspace_frame = tk.Frame(self.content_frame)
        self.workspace_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create canvas frame (left side)
        canvas_frame = tk.Frame(self.workspace_frame)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create layers panel frame (right side) - start with thin width
        self.layers_frame = tk.Frame(self.workspace_frame, width=150, bg="#e0e0e0")
        self.layers_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        self.layers_frame.pack_propagate(False)  # Maintain fixed width
        
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
            width=screen_width-300, 
            height=screen_height-100
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
    def _setup_drawing_tools(self):
        """Setup the drawing tools manager and layers system."""
        self.drawing_tool_manager = DrawingToolManager(
            canvas=self.canvas,
            sketching_stage=self,
            tools_frame=self.tools_frame,
            status_var=self.status_var
        )
        
        # Setup layers system
        self.layers = SketchingLayers(parent_frame=self.layers_frame, sketching_stage=self)
        
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
        
        # Keyboard shortcuts - bind to window for global access
        self.window.bind("<Command-z>", self._handle_undo)  # Mac
        self.window.bind("<Control-z>", self._handle_undo)  # Windows/Linux
        self.window.focus_set()  # Allow window to receive keyboard events
        
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
        """Redraw all stored drawing objects that are on visible layers."""
        # Calculate work area bounds
        width = int(self.length_mm * self.zoom_level)
        height = int(self.height_mm * self.zoom_level)
        x1 = self.center_x - (width // 2)
        y1 = self.center_y - (height // 2)
        
        # Redraw each object if its layer is visible
        for drawing_obj in self.drawing_objects:
            # Check if object's layer is visible
            layer_id = drawing_obj.get('layer_id', 'default')
            if hasattr(self, 'layers') and not self.layers.is_layer_visible(layer_id):
                continue  # Skip objects on hidden layers
            
            obj_type = drawing_obj['type']
            real_coords = drawing_obj['real_coords']
            properties = drawing_obj['properties']
            
            # Handle circle objects separately (they have different coordinate format)
            if obj_type == 'circle':
                if len(real_coords) >= 3:  # center_x, center_y, radius
                    center_x_mm, center_y_mm, radius_mm = real_coords[0], real_coords[1], real_coords[2]
                    
                    # Convert center to canvas coordinates
                    center_canvas_x = x1 + (center_x_mm * self.zoom_level)
                    center_canvas_y = y1 + (center_y_mm * self.zoom_level)
                    
                    # Calculate display radius and line width
                    display_radius = radius_mm * self.zoom_level
                    width_mm = properties.get('width_mm', 0.1)
                    display_width = max(1, int(width_mm * self.zoom_level))
                    
                    # Create circle
                    self.canvas.create_oval(
                        center_canvas_x - display_radius, center_canvas_y - display_radius,
                        center_canvas_x + display_radius, center_canvas_y + display_radius,
                        outline=properties.get('outline', 'black'),
                        width=display_width,
                        fill=properties.get('fill', ''),
                        tags="drawing"
                    )
                continue  # Skip the general coordinate processing for circles
            
            # Convert real coordinates to canvas coordinates for other shapes
            canvas_coords = []
            for i in range(0, len(real_coords), 2):
                canvas_x = x1 + (real_coords[i] * self.zoom_level)
                canvas_y = y1 + (real_coords[i+1] * self.zoom_level)
                canvas_coords.extend([canvas_x, canvas_y])
                
            # Create the shape
            if obj_type == 'line':
                # Calculate display width based on real width and zoom
                width_mm = properties.get('width_mm', 0.1)  # Default 0.1mm if not specified
                display_width = max(1, int(width_mm * self.zoom_level))
                
                self.canvas.create_line(
                    canvas_coords,
                    fill=properties.get('fill', 'black'),
                    width=display_width,
                    tags="drawing"
                )
            elif obj_type == 'rectangle':
                # Calculate display width for rectangle border
                width_mm = properties.get('width_mm', 0.1)  # Default 0.1mm if not specified
                display_width = max(1, int(width_mm * self.zoom_level))
                
                self.canvas.create_rectangle(
                    canvas_coords,
                    outline=properties.get('outline', 'black'),
                    width=display_width,
                    fill=properties.get('fill', ''),
                    tags="drawing"
                )
            elif obj_type == 'image':
                # Handle image objects
                try:
                    from PIL import Image, ImageTk
                    
                    # Get image properties
                    file_path = properties.get('file_path')
                    width_mm = properties.get('width_mm', 20.0)
                    height_mm = properties.get('height_mm', 20.0)
                    
                    if file_path:
                        # Load and resize image
                        pil_image = Image.open(file_path)
                        display_width = max(1, int(width_mm * self.zoom_level))
                        display_height = max(1, int(height_mm * self.zoom_level))
                        
                        display_image = pil_image.resize((display_width, display_height), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(display_image)
                        
                        # Create image on canvas
                        image_id = self.canvas.create_image(
                            canvas_coords[0], canvas_coords[1],
                            anchor=properties.get('anchor', 'center'),
                            image=photo,
                            tags="drawing"
                        )
                        
                        # Store reference to prevent garbage collection
                        setattr(self.canvas, f"image_ref_{image_id}", photo)
                        
                except Exception as e:
                    print(f"Error redrawing image: {e}")
                    # Draw a placeholder rectangle if image fails to load
                    placeholder_width = max(1, int(properties.get('width_mm', 20.0) * self.zoom_level))
                    placeholder_height = max(1, int(properties.get('height_mm', 20.0) * self.zoom_level))
                    
                    self.canvas.create_rectangle(
                        canvas_coords[0] - placeholder_width//2,
                        canvas_coords[1] - placeholder_height//2,
                        canvas_coords[0] + placeholder_width//2,
                        canvas_coords[1] + placeholder_height//2,
                        outline="red", width=1, fill="", dash=(2, 2),
                        tags="drawing"
                    )
                    self.canvas.create_text(
                        canvas_coords[0], canvas_coords[1],
                        text="Image\nMissing", fill="red", font=("Arial", 8),
                        tags="drawing"
                    )
                    
            elif obj_type == 'reference_point':
                # Draw reference points as small circles
                point_x, point_y = canvas_coords[0], canvas_coords[1]
                radius = 3
                color = properties.get('color', 'blue')
                
                self.canvas.create_oval(
                    point_x - radius, point_y - radius,
                    point_x + radius, point_y + radius,
                    fill=color, outline=color, width=1,
                    tags="drawing reference_point"
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
        
    def add_drawing_object(self, obj_type, real_coords, properties, operation_id=None):
        """Add a drawing object to the workspace with unique ID for undo support."""
        # Generate operation ID if not provided
        if operation_id is None:
            operation_id = self._get_next_operation_id()
            # Only add to undo stack for single operations (when no operation_id is provided)
            self.undo_stack.append(operation_id)
            print(f"Added single operation ID {operation_id} to undo stack")
        
        drawing_obj = {
            'type': obj_type,
            'real_coords': real_coords,
            'properties': properties,
            'layer_id': self.layers.get_active_layer_id() if hasattr(self, 'layers') else 'default',
            'operation_id': operation_id  # Unique ID for this drawing operation
        }
        self.drawing_objects.append(drawing_obj)
        
        # Update layers panel if it exists
        if hasattr(self, 'layers'):
            self.layers.refresh_layer_objects()
            
    def _get_next_operation_id(self):
        """Get the next unique operation ID."""
        self.object_counter += 1
        return self.object_counter
        
    def _handle_undo(self, event=None):
        """Handle undo keyboard shortcut."""
        self.undo_last_operation()
        
    def undo_last_operation(self):
        """Undo the last drawing operation by removing all objects with the latest operation ID."""
        if not self.undo_stack:
            print("No operations to undo")
            self.status_var.set("Mode: No operations to undo")
            return
            
        # Get the latest operation ID
        last_operation_id = self.undo_stack.pop()
        print(f"Undoing operation ID: {last_operation_id}")
        
        # Remove all objects with this operation ID
        objects_before = len(self.drawing_objects)
        self.drawing_objects = [obj for obj in self.drawing_objects 
                               if obj.get('operation_id') != last_operation_id]
        objects_after = len(self.drawing_objects)
        objects_removed = objects_before - objects_after
        
        print(f"Removed {objects_removed} objects with operation ID {last_operation_id}")
        
        # Refresh the display
        self._redraw_all()
        
        # Update layers panel if it exists
        if hasattr(self, 'layers'):
            self.layers.refresh_layer_objects()
            
        # Update status
        self.status_var.set(f"Mode: Undid operation {last_operation_id} ({objects_removed} objects)")
        
        # Clear the status message after 2 seconds
        self.window.after(2000, lambda: self.status_var.set("Mode: Select"))
        
    def clear_canvas(self):
        """Clear all drawings while preserving the work area."""
        self.drawing_objects = []
        self.canvas.delete("drawing")
        self.canvas.delete("temp")
        self.canvas.delete("snap_indicator")
        
        # Reset undo system
        self.undo_stack = []
        self.object_counter = 0
        print("Canvas cleared - undo system reset")
        
        # Refresh layers panel if it exists
        if hasattr(self, 'layers'):
            self.layers.refresh_layer_objects()
        
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
    
    def refresh_display(self):
        """Refresh the display to reflect layer visibility changes."""
        self._redraw_all()
    
    def get_objects_by_layer(self, layer_id):
        """Get all objects belonging to a specific layer."""
        return [obj for obj in self.drawing_objects if obj.get('layer_id', 'default') == layer_id]
    
    def update_object_layer(self, object_index, new_layer_id):
        """Update the layer assignment of a specific object."""
        if 0 <= object_index < len(self.drawing_objects):
            self.drawing_objects[object_index]['layer_id'] = new_layer_id
            self.refresh_display()
            if hasattr(self, 'layers'):
                self.layers.refresh_layer_objects()
    
    def delete_objects_by_layer(self, layer_id):
        """Delete all objects belonging to a specific layer."""
        self.drawing_objects = [obj for obj in self.drawing_objects if obj.get('layer_id', 'default') != layer_id]
        self.refresh_display()
        if hasattr(self, 'layers'):
            self.layers.refresh_layer_objects()
        
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
            
    def generate_gcode(self, power_percent=None, speed_mmmin=None, profile_name=None):
        """Generate G-code from the current drawing objects.
        
        Args:
            power_percent (int, optional): Laser power percentage (1-100)
            speed_mmmin (int, optional): Feed rate in mm/min (0-6000)
            profile_name (str, optional): Name of the profile being used
        """
        if self.gcode_generator:
            # First, find the origin point
            origin_point = self._find_origin_point()
            if origin_point is None:
                messagebox.showwarning(
                    "No Origin Found", 
                    "Please place an origin point using the Origin tool before generating G-Code."
                )
                return
            
            # Export high-resolution PNG temporarily for processing
            temp_image_path = self._export_temp_high_res_image()
            if temp_image_path is None:
                messagebox.showerror("Export Error", "Failed to create temporary high-resolution image.")
                return
            
            # Convert origin from mm to pixels (assuming 0.072mm per pixel)
            pixels_per_mm = 1 / 0.072
            origin_pixels = (
                int(origin_point[0] * pixels_per_mm),
                int(origin_point[1] * pixels_per_mm)
            )
            
            # Apply power and speed settings if provided
            if power_percent is not None and speed_mmmin is not None:
                # Convert power percentage to laser controller range (0-255)
                laser_power = int((power_percent / 100.0) * 255)
                self.gcode_generator.laser_power = laser_power
                self.gcode_generator.travel_speed = speed_mmmin
                print(f"Using profile settings - Power: {power_percent}% ({laser_power}/255), Speed: {speed_mmmin} mm/min")
            
            # Generate instructions from the image
            instructions = self.gcode_generator.generate_instructions_from_image(temp_image_path, origin_pixels)
            
            if instructions:
                # Get image height for coordinate conversion
                from PIL import Image
                temp_image = Image.open(temp_image_path)
                image_height_pixels = temp_image.height
                temp_image.close()
                
                # Convert instructions to G-Code commands
                gcode_commands = self.gcode_generator.convert_instructions_to_gcode(
                    instructions, origin_pixels, image_height_pixels
                )
                
                # Show preview window with profile information
                window_title = f"G-Code Preview"
                if profile_name:
                    window_title += f" - {profile_name}"
                
                self.gcode_generator.show_preview_window(
                    temp_image_path, gcode_commands, origin_pixels, 
                    window_title=window_title, 
                    profile_info=f"Power: {power_percent}%, Speed: {speed_mmmin} mm/min" if power_percent and speed_mmmin else None
                )
            
            # Note: Don't clean up temp file immediately as preview window needs it
            # The file will be cleaned up when the system clears temp files
                
    def _find_origin_point(self):
        """Find the origin point from drawing objects.
        
        Returns:
            tuple: Origin coordinates as (x, y) in mm, or None if not found
        """
        print(f"Looking for origin point in {len(self.drawing_objects)} drawing objects")
        for i, drawing_obj in enumerate(self.drawing_objects):
            print(f"Object {i}: type='{drawing_obj['type']}', coords={drawing_obj['real_coords']}")
            if drawing_obj['type'] == 'origin':
                real_coords = drawing_obj['real_coords']
                if len(real_coords) >= 2:
                    print(f"Found origin at: ({real_coords[0]}, {real_coords[1]})")
                    return (real_coords[0], real_coords[1])
        print("No origin point found")
        return None
        
    def start_engrave_workflow(self):
        """Start the engrave workflow - select laser, then profile, then generate G-code."""
        # Load machines data
        machines_data = self._load_machines_data()
        if not machines_data or not machines_data.get("machines"):
            messagebox.showerror("No Machines", "No laser machines found. Please add a machine first.")
            return
        
        # Show laser selection window
        self._show_laser_selection_window(machines_data)
        
    def _load_machines_data(self):
        """Load machines data from laser.json file."""
        import json
        import os
        
        try:
            data_file = os.path.join(os.path.dirname(__file__), "DATA", "laser.json")
            with open(data_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading machines data: {e}")
            return {"machines": []}
    
    def _show_laser_selection_window(self, machines_data):
        """Show window to select a laser machine."""
        # Create laser selection window
        laser_window = tk.Toplevel(self.window)
        laser_window.title("Select Laser Machine - G2burn")
        laser_window.geometry("600x400")
        laser_window.configure(bg="#1a1a1a")
        
        # Center the window
        self._center_window_on_parent(laser_window, 600, 400)
        
        # Make window modal
        laser_window.transient(self.window)
        laser_window.grab_set()
        
        # Main frame
        main_frame = tk.Frame(laser_window, bg="#1a1a1a", padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_label = tk.Label(
            main_frame,
            text="Select Laser Machine",
            font=("Helvetica Neue", 20, "bold"),
            bg="#1a1a1a",
            fg="#ffffff"
        )
        header_label.pack(pady=(0, 20))
        
        # Description
        desc_label = tk.Label(
            main_frame,
            text="Choose the laser machine you want to use for engraving:",
            font=("Helvetica Neue", 12),
            bg="#1a1a1a",
            fg="#8e8e93"
        )
        desc_label.pack(pady=(0, 20))
        
        # Machines list frame
        machines_frame = tk.Frame(main_frame, bg="#1a1a1a")
        machines_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Create machine selection cards
        selected_machine = tk.StringVar()
        
        for i, machine in enumerate(machines_data.get("machines", [])):
            self._create_machine_selection_card(machines_frame, machine, selected_machine, i)
        
        # Buttons frame
        button_frame = tk.Frame(main_frame, bg="#1a1a1a")
        button_frame.pack(fill=tk.X)
        
        # Cancel button
        cancel_btn = tk.Label(
            button_frame,
            text="Cancel",
            font=("Helvetica Neue", 11, "bold"),
            bg="#636366",
            fg="#ffffff",
            padx=20,
            pady=8,
            cursor="hand2"
        )
        cancel_btn.pack(side=tk.LEFT)
        cancel_btn.bind("<Button-1>", lambda e: laser_window.destroy())
        cancel_btn.bind("<Enter>", lambda e: cancel_btn.configure(bg="#48484a"))
        cancel_btn.bind("<Leave>", lambda e: cancel_btn.configure(bg="#636366"))
        
        # Next button
        next_btn = tk.Label(
            button_frame,
            text="Next →",
            font=("Helvetica Neue", 11, "bold"),
            bg="#007AFF",
            fg="#ffffff",
            padx=20,
            pady=8,
            cursor="hand2"
        )
        next_btn.pack(side=tk.RIGHT)
        next_btn.bind("<Button-1>", lambda e: self._proceed_to_profile_selection(laser_window, selected_machine.get(), machines_data))
        next_btn.bind("<Enter>", lambda e: next_btn.configure(bg="#0056CC"))
        next_btn.bind("<Leave>", lambda e: next_btn.configure(bg="#007AFF"))
        
    def _create_machine_selection_card(self, parent, machine, selected_var, index):
        """Create a selectable machine card."""
        # Card frame
        card_frame = tk.Frame(parent, bg="#2a2a2a", relief=tk.FLAT, bd=0)
        card_frame.pack(fill=tk.X, pady=5, padx=5, ipady=15, ipadx=15)
        
        # Radio button for selection
        radio_btn = tk.Radiobutton(
            card_frame,
            text="",
            variable=selected_var,
            value=machine.get("id"),
            bg="#2a2a2a",
            activebackground="#2a2a2a",
            selectcolor="#007AFF",
            fg="#ffffff"
        )
        radio_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Machine info frame
        info_frame = tk.Frame(card_frame, bg="#2a2a2a")
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Machine name
        name_label = tk.Label(
            info_frame,
            text=machine.get("name", "Unknown Machine"),
            font=("Helvetica Neue", 14, "bold"),
            bg="#2a2a2a",
            fg="#ffffff"
        )
        name_label.pack(anchor=tk.W)
        
        # Machine details
        type_text = f"Type: {machine.get('type', 'Unknown')}"
        work_area = machine.get("work_area", {})
        area_text = f"Work Area: {work_area.get('width_mm', 0)}×{work_area.get('height_mm', 0)}mm"
        
        details_label = tk.Label(
            info_frame,
            text=f"{type_text} • {area_text}",
            font=("Helvetica Neue", 10),
            bg="#2a2a2a",
            fg="#8e8e93"
        )
        details_label.pack(anchor=tk.W)
        
        # Status
        status = machine.get("status", "unknown")
        status_color = "#30D158" if status == "connected" else "#FF453A"
        status_label = tk.Label(
            info_frame,
            text=f"● {status.title()}",
            font=("Helvetica Neue", 10, "bold"),
            bg="#2a2a2a",
            fg=status_color
        )
        status_label.pack(anchor=tk.W, pady=(2, 0))
        
        # Make card clickable
        def select_machine(e):
            selected_var.set(machine.get("id"))
        
        card_frame.bind("<Button-1>", select_machine)
        info_frame.bind("<Button-1>", select_machine)
        name_label.bind("<Button-1>", select_machine)
        details_label.bind("<Button-1>", select_machine)
        status_label.bind("<Button-1>", select_machine)
    
    def _proceed_to_profile_selection(self, laser_window, selected_machine_id, machines_data):
        """Proceed to profile selection after laser is chosen."""
        if not selected_machine_id:
            messagebox.showwarning("No Selection", "Please select a laser machine first.")
            return
        
        # Find the selected machine
        selected_machine = None
        for machine in machines_data.get("machines", []):
            if machine.get("id") == selected_machine_id:
                selected_machine = machine
                break
        
        if not selected_machine:
            messagebox.showerror("Error", "Selected machine not found.")
            return
        
        # Close laser selection window
        laser_window.destroy()
        
        # Show profile selection window
        self._show_profile_selection_window(selected_machine)
    
    def _show_profile_selection_window(self, machine):
        """Show window to select a profile for the chosen machine."""
        # Create profile selection window
        profile_window = tk.Toplevel(self.window)
        profile_window.title(f"Select Profile - {machine.get('name')} - G2burn")
        profile_window.geometry("700x500")
        profile_window.configure(bg="#1a1a1a")
        
        # Center the window
        self._center_window_on_parent(profile_window, 700, 500)
        
        # Make window modal
        profile_window.transient(self.window)
        profile_window.grab_set()
        
        # Main frame
        main_frame = tk.Frame(profile_window, bg="#1a1a1a", padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_label = tk.Label(
            main_frame,
            text=f"Select Profile for {machine.get('name')}",
            font=("Helvetica Neue", 18, "bold"),
            bg="#1a1a1a",
            fg="#ffffff"
        )
        header_label.pack(pady=(0, 10))
        
        # Machine info
        machine_info_label = tk.Label(
            main_frame,
            text=f"{machine.get('type')} • {machine.get('work_area', {}).get('width_mm', 0)}×{machine.get('work_area', {}).get('height_mm', 0)}mm",
            font=("Helvetica Neue", 11),
            bg="#1a1a1a",
            fg="#8e8e93"
        )
        machine_info_label.pack(pady=(0, 20))
        
        # Profiles list frame with scrollbar
        profiles_outer_frame = tk.Frame(main_frame, bg="#1a1a1a")
        profiles_outer_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Create scrollable frame
        canvas = tk.Canvas(profiles_outer_frame, bg="#1a1a1a", highlightthickness=0)
        scrollbar = tk.Scrollbar(profiles_outer_frame, orient="vertical", command=canvas.yview,
                                bg="#2a2a2a", troughcolor="#1a1a1a", activebackground="#404040")
        scrollable_frame = tk.Frame(canvas, bg="#1a1a1a")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Selected profile variable
        selected_profile = tk.StringVar()
        
        # Display profiles
        profiles = machine.get("profiles", [])
        if profiles:
            for i, profile in enumerate(profiles):
                self._create_profile_selection_card(scrollable_frame, profile, selected_profile, i)
        else:
            # No profiles message
            no_profiles_label = tk.Label(
                scrollable_frame,
                text="No profiles found for this machine.\nPlease add a profile first.",
                font=("Helvetica Neue", 12),
                bg="#1a1a1a",
                fg="#8e8e93",
                justify=tk.CENTER
            )
            no_profiles_label.pack(pady=50)
        
        # Pack scrollable components
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Buttons frame
        button_frame = tk.Frame(main_frame, bg="#1a1a1a")
        button_frame.pack(fill=tk.X)
        
        # Back button
        back_btn = tk.Label(
            button_frame,
            text="← Back",
            font=("Helvetica Neue", 11, "bold"),
            bg="#636366",
            fg="#ffffff",
            padx=20,
            pady=8,
            cursor="hand2"
        )
        back_btn.pack(side=tk.LEFT)
        back_btn.bind("<Button-1>", lambda e: self._go_back_to_laser_selection(profile_window))
        back_btn.bind("<Enter>", lambda e: back_btn.configure(bg="#48484a"))
        back_btn.bind("<Leave>", lambda e: back_btn.configure(bg="#636366"))
        
        # Generate button
        generate_btn = tk.Label(
            button_frame,
            text="Generate G-Code",
            font=("Helvetica Neue", 11, "bold"),
            bg="#30D158",
            fg="#ffffff",
            padx=20,
            pady=8,
            cursor="hand2"
        )
        generate_btn.pack(side=tk.RIGHT)
        generate_btn.bind("<Button-1>", lambda e: self._proceed_to_gcode_generation(profile_window, selected_profile.get(), machine))
        generate_btn.bind("<Enter>", lambda e: generate_btn.configure(bg="#28A745"))
        generate_btn.bind("<Leave>", lambda e: generate_btn.configure(bg="#30D158"))
    
    def _create_profile_selection_card(self, parent, profile, selected_var, index):
        """Create a selectable profile card."""
        # Card frame
        card_frame = tk.Frame(parent, bg="#2a2a2a", relief=tk.FLAT, bd=0)
        card_frame.pack(fill=tk.X, pady=5, padx=5, ipady=15, ipadx=15)
        
        # Radio button for selection
        radio_btn = tk.Radiobutton(
            card_frame,
            text="",
            variable=selected_var,
            value=profile.get("id"),
            bg="#2a2a2a",
            activebackground="#2a2a2a",
            selectcolor="#007AFF",
            fg="#ffffff"
        )
        radio_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        # Profile info frame
        info_frame = tk.Frame(card_frame, bg="#2a2a2a")
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Profile name and type
        name_label = tk.Label(
            info_frame,
            text=profile.get("name", "Unknown Profile"),
            font=("Helvetica Neue", 14, "bold"),
            bg="#2a2a2a",
            fg="#ffffff"
        )
        name_label.pack(anchor=tk.W)
        
        # Profile type with color coding
        profile_type = profile.get("type", "unknown")
        type_colors = {
            "cutting1mm": "#FF453A",
            "cutting2mm": "#FF9500", 
            "cutting4mm": "#FFCC00",
            "engrave": "#30D158"
        }
        type_color = type_colors.get(profile_type, "#8e8e93")
        
        type_label = tk.Label(
            info_frame,
            text=f"Type: {profile_type.replace('cutting', 'Cutting ').replace('mm', 'mm')}",
            font=("Helvetica Neue", 11, "bold"),
            bg="#2a2a2a",
            fg=type_color
        )
        type_label.pack(anchor=tk.W, pady=(2, 0))
        
        # Surface and settings
        surface_text = f"Surface: {profile.get('surface', 'Unknown')}"
        settings_text = f"Power: {profile.get('power', 0)}% • Speed: {profile.get('speed', 0)} mm/min"
        
        surface_label = tk.Label(
            info_frame,
            text=surface_text,
            font=("Helvetica Neue", 10),
            bg="#2a2a2a",
            fg="#8e8e93"
        )
        surface_label.pack(anchor=tk.W, pady=(2, 0))
        
        settings_label = tk.Label(
            info_frame,
            text=settings_text,
            font=("Helvetica Neue", 10),
            bg="#2a2a2a",
            fg="#8e8e93"
        )
        settings_label.pack(anchor=tk.W, pady=(2, 0))
        
        # Make card clickable
        def select_profile(e):
            selected_var.set(profile.get("id"))
        
        card_frame.bind("<Button-1>", select_profile)
        info_frame.bind("<Button-1>", select_profile)
        name_label.bind("<Button-1>", select_profile)
        type_label.bind("<Button-1>", select_profile)
        surface_label.bind("<Button-1>", select_profile)
        settings_label.bind("<Button-1>", select_profile)
    
    def _go_back_to_laser_selection(self, profile_window):
        """Go back to laser selection from profile selection."""
        profile_window.destroy()
        machines_data = self._load_machines_data()
        self._show_laser_selection_window(machines_data)
    
    def _proceed_to_gcode_generation(self, profile_window, selected_profile_id, machine):
        """Proceed to G-code generation with selected profile."""
        if not selected_profile_id:
            messagebox.showwarning("No Selection", "Please select a profile first.")
            return
        
        # Find the selected profile
        selected_profile = None
        for profile in machine.get("profiles", []):
            if profile.get("id") == selected_profile_id:
                selected_profile = profile
                break
        
        if not selected_profile:
            messagebox.showerror("Error", "Selected profile not found.")
            return
        
        # Close profile selection window
        profile_window.destroy()
        
        # Generate G-code with profile settings
        power_percent = selected_profile.get("power", 50)
        speed_mmmin = selected_profile.get("speed", 1000)
        profile_name = f"{machine.get('name')} - {selected_profile.get('name')}"
        
        print(f"Starting G-code generation with profile: {profile_name}")
        print(f"Settings: Power {power_percent}%, Speed {speed_mmmin} mm/min")
        
        # Call the modified generate_gcode function with profile parameters
        self.generate_gcode(power_percent, speed_mmmin, profile_name)
    
    def _center_window_on_parent(self, window, width, height):
        """Center a window on its parent."""
        window.update_idletasks()
        parent_x = self.window.winfo_x()
        parent_y = self.window.winfo_y()
        parent_width = self.window.winfo_width()
        parent_height = self.window.winfo_height()
        
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        
        window.geometry(f"{width}x{height}+{x}+{y}")
        
    # def _find_origin_point(self):
    #     """Find the origin point from drawing objects.
        
    #     Returns:
    #         tuple: Origin coordinates as (x, y) in mm, or None if not found
    #     """
    #     for drawing_obj in self.drawing_objects:
    #         if drawing_obj['type'] == 'origin':
    #             real_coords = drawing_obj['real_coords']
        
    def show_advanced_settings(self):
        """Show advanced settings window with various options."""
        # Create new window
        settings_window = tk.Toplevel(self.window)
        settings_window.title("Advanced Settings - G2burn")
        settings_window.geometry("400x300")
        settings_window.resizable(False, False)
        
        # Center the window
        settings_window.update_idletasks()
        x = (settings_window.winfo_screenwidth() // 2) - (200)
        y = (settings_window.winfo_screenheight() // 2) - (150)
        settings_window.geometry(f"400x300+{x}+{y}")
        
        # Main frame with padding
        main_frame = tk.Frame(settings_window, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(main_frame, text="Advanced Settings", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Color Processing section
        color_frame = tk.LabelFrame(main_frame, text="Color Processing", font=("Arial", 10, "bold"), padx=10, pady=10)
        color_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Flip colors toggle
        self.flip_colors_var = tk.BooleanVar(value=self.flip_colors)
        flip_colors_check = tk.Checkbutton(
            color_frame,
            text="Flip Colors (Invert Black/White)",
            variable=self.flip_colors_var,
            font=("Arial", 10),
            command=self._toggle_flip_colors
        )
        flip_colors_check.pack(anchor=tk.W, pady=5)
        
        # Description label
        desc_label = tk.Label(
            color_frame,
            text="When enabled, white areas become black and black areas become white\nin the exported image and G-Code generation.",
            font=("Arial", 9),
            fg="gray",
            justify=tk.LEFT
        )
        desc_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Status indicator
        self.flip_status_label = tk.Label(
            color_frame,
            text=f"Current status: {'ENABLED' if self.flip_colors else 'DISABLED'}",
            font=("Arial", 9, "bold"),
            fg="green" if self.flip_colors else "red"
        )
        self.flip_status_label.pack(anchor=tk.W)
        
        # Buttons frame
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Close button
        close_button = tk.Button(
            button_frame,
            text="Close",
            command=settings_window.destroy,
            width=15,
            font=("Arial", 10)
        )
        close_button.pack(side=tk.RIGHT)
        
        # Apply button (for future settings)
        apply_button = tk.Button(
            button_frame,
            text="Apply All",
            command=lambda: self._apply_advanced_settings(settings_window),
            width=15,
            font=("Arial", 10),
            bg="#4CAF50",
            fg="white"
        )
        apply_button.pack(side=tk.RIGHT, padx=(0, 10))
        
    def _toggle_flip_colors(self):
        """Toggle the flip colors setting."""
        self.flip_colors = self.flip_colors_var.get()
        
        # Update status label
        if hasattr(self, 'flip_status_label'):
            self.flip_status_label.config(
                text=f"Current status: {'ENABLED' if self.flip_colors else 'DISABLED'}",
                fg="green" if self.flip_colors else "red"
            )
        
        print(f"Flip colors setting changed to: {self.flip_colors}")
        
    def _apply_advanced_settings(self, window):
        """Apply all advanced settings and close window."""
        # For now, just toggle flip colors is applied automatically
        # Future settings can be applied here
        messagebox.showinfo(
            "Settings Applied", 
            f"Advanced settings applied successfully!\n\nFlip Colors: {'Enabled' if self.flip_colors else 'Disabled'}"
        )
        window.destroy()
        
    def _apply_color_flip(self, image):
        """Apply color inversion to the image.
        
        Args:
            image (PIL.Image): The image to flip colors
            
        Returns:
            PIL.Image: The image with flipped colors
        """
        try:
            import numpy as np
            
            # Convert PIL image to numpy array
            img_array = np.array(image)
            
            # Flip colors: 255 - cell_value for each pixel
            flipped_array = 255 - img_array
            
            # Convert back to PIL Image
            from PIL import Image
            flipped_image = Image.fromarray(flipped_array.astype('uint8'))
            
            return flipped_image
            
        except Exception as e:
            print(f"Error applying color flip: {e}")
            # Return original image if flipping fails
            return image
        
    def _export_temp_high_res_image(self):
        """Export a temporary high-resolution PNG image for processing using PostScript method.
        
        Returns:
            str: Path to temporary image file, or None if failed
        """
        import tempfile
        import os
        
        try:
            # Calculate target resolution based on 0.072mm per pixel
            target_width = int(self.length_mm / 0.072)
            target_height = int(self.height_mm / 0.072)
            
            # Get current work area bounds in canvas coordinates
            work_x1, work_y1, work_width, work_height = self.get_work_area_bounds()
            
            # Create temporary PostScript file
            temp_ps_fd, temp_ps_path = tempfile.mkstemp(suffix='.ps')
            os.close(temp_ps_fd)  # Close file descriptor
            
            # Create temporary PNG file for final output
            temp_png_fd, temp_png_path = tempfile.mkstemp(suffix='.png')
            os.close(temp_png_fd)  # Close file descriptor
            
            try:
                # Temporarily hide reference points and origin points for clean export
                hidden_items = []
                for item in self.canvas.find_withtag("reference_point"):
                    hidden_items.append(item)
                    self.canvas.itemconfig(item, state='hidden')
                
                # Also hide any origin point markers if they exist
                for item in self.canvas.find_all():
                    tags = self.canvas.gettags(item)
                    if 'origin' in tags:
                        hidden_items.append(item)
                        self.canvas.itemconfig(item, state='hidden')
                
                # Hide image resize handles
                for item in self.canvas.find_withtag("image_handles"):
                    hidden_items.append(item)
                    self.canvas.itemconfig(item, state='hidden')
                
                # Hide all temporary UI elements
                for item in self.canvas.find_withtag("temp"):
                    hidden_items.append(item)
                    self.canvas.itemconfig(item, state='hidden')
                
                # Hide snap indicators
                for item in self.canvas.find_withtag("snap_indicator"):
                    hidden_items.append(item)
                    self.canvas.itemconfig(item, state='hidden')
                
                # Hide work area elements (border, grid, rulers) for clean export
                for work_area_item in self.work_area_objects:
                    hidden_items.append(work_area_item)
                    self.canvas.itemconfig(work_area_item, state='hidden')
                
                # Export canvas as PostScript
                self.canvas.postscript(file=temp_ps_path, colormode="color")
                
                # Restore all hidden items
                for item in hidden_items:
                    self.canvas.itemconfig(item, state='normal')
                
                # Process PostScript file with Pillow
                from PIL import Image
                
                # Open PostScript file
                ps_image = Image.open(temp_ps_path)
                
                # Get canvas dimensions
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()
                
                # Calculate the scale factor between PS image and canvas
                ps_width, ps_height = ps_image.size
                scale_x = ps_width / canvas_width
                scale_y = ps_height / canvas_height
                
                # Calculate crop coordinates in PostScript image space
                crop_x1 = int(work_x1 * scale_x)
                crop_y1 = int(work_y1 * scale_y)
                crop_x2 = int((work_x1 + work_width) * scale_x)
                crop_y2 = int((work_y1 + work_height) * scale_y)
                
                # Ensure crop coordinates are within image bounds
                crop_x1 = max(0, crop_x1)
                crop_y1 = max(0, crop_y1)
                crop_x2 = min(ps_width, crop_x2)
                crop_y2 = min(ps_height, crop_y2)
                
                # Crop to work area
                work_area_image = ps_image.crop((crop_x1, crop_y1, crop_x2, crop_y2))
                
                # Resize to target resolution
                high_res_image = work_area_image.resize((target_width, target_height), Image.Resampling.NEAREST)
                
                # Apply color flipping if enabled
                if self.flip_colors:
                    high_res_image = self._apply_color_flip(high_res_image)
                
                # Save as PNG
                high_res_image.save(temp_png_path, "PNG")
                
                print(f"Temporary high-res image created using PostScript method: {target_width}x{target_height} pixels")
                
                return temp_png_path
                
            except ImportError:
                print("PostScript support not available, falling back to manual drawing method")
                # Fallback to original method if PostScript support is missing
                return self._export_temp_high_res_image_fallback()
                
            except Exception as pil_error:
                print(f"Error processing PostScript image: {pil_error}")
                # Fallback to original method if PostScript processing fails
                return self._export_temp_high_res_image_fallback()
                
            finally:
                # Clean up temporary PostScript file
                try:
                    os.unlink(temp_ps_path)
                except:
                    pass
                    
        except Exception as e:
            print(f"Error creating temporary image: {e}")
            return None
            
    def _export_temp_high_res_image_fallback(self):
        """Fallback method for creating temporary high-res image using manual drawing.
        
        Returns:
            str: Path to temporary image file, or None if failed
        """
        import tempfile
        import os
        
        try:
            # Calculate target resolution based on 0.072mm per pixel
            target_width = int(self.length_mm / 0.072)
            target_height = int(self.height_mm / 0.072)
            
            # Create high-resolution image
            from PIL import Image, ImageDraw
            image = Image.new('RGB', (target_width, target_height), 'white')
            draw = ImageDraw.Draw(image)
            
            # Calculate scale factor from mm to pixels
            scale_x = target_width / self.length_mm
            scale_y = target_height / self.height_mm
            
            # Draw all drawing objects (except origin and reference points)
            for drawing_obj in self.drawing_objects:
                if drawing_obj['type'] not in ['origin', 'reference_point']:
                    self._draw_object_on_image(draw, drawing_obj, scale_x, scale_y)
            
            # Apply color flipping if enabled
            if self.flip_colors:
                image = self._apply_color_flip(image)
            
            # Save to temporary file
            temp_fd, temp_path = tempfile.mkstemp(suffix='.png')
            os.close(temp_fd)  # Close file descriptor
            image.save(temp_path, 'PNG')
            
            print(f"Temporary high-res image created using fallback method: {target_width}x{target_height} pixels")
            
            return temp_path
            
        except Exception as e:
            print(f"Error creating temporary image with fallback method: {e}")
            return None
            
    def export_high_res_png(self):
        """Export the work area as a high-resolution PNG image."""
        try:
            # Calculate target resolution based on 0.072mm per pixel
            target_width = int(self.length_mm / 0.072)
            target_height = int(self.height_mm / 0.072)
            
            # Ask user where to save
            file_path = filedialog.asksaveasfilename(
                title="Export High Resolution PNG",
                defaultextension=".png",
                filetypes=[("PNG files", "*.png")],
                initialfile=f"{self.project_name}_highres"
            )
            
            if not file_path:
                return
                
            # Create high-resolution image
            image = Image.new('RGB', (target_width, target_height), 'white')
            draw = ImageDraw.Draw(image)
            
            # Calculate scale factor from mm to pixels
            scale_x = target_width / self.length_mm
            scale_y = target_height / self.height_mm
            
            # Draw all drawing objects
            for drawing_obj in self.drawing_objects:
                self._draw_object_on_image(draw, drawing_obj, scale_x, scale_y)
            
            #Implement HERE
            # Apply color flipping if enabled
            if self.flip_colors:
                image = self._apply_color_flip(image)
            
            # Save the image
            image.save(file_path, 'PNG')
            
            messagebox.showinfo(
                "Export Complete", 
                f"High-resolution PNG saved:\n{file_path}\n\nResolution: {target_width}x{target_height} pixels\nScale: {scale_x:.1f} pixels/mm"
            )
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export PNG:\n{str(e)}")
            
    def export_high_res_png_v2(self):
        """Export the work area as a high-resolution PNG using PostScript method."""
        print("Exporting high-resolution PNG (PostScript Method)...")
        try:
            # Ask user where to save
            file_path = filedialog.asksaveasfilename(
                title="Export High Resolution PNG (PostScript Method)",
                defaultextension=".png",
                filetypes=[("PNG files", "*.png")],
                initialfile=f"{self.project_name}_highres_v2"
            )
            
            if not file_path:
                return
            
            # Calculate target resolution based on 0.072mm per pixel
            target_width = int(self.length_mm / 0.072)
            target_height = int(self.height_mm / 0.072)
            
            # Get current work area bounds in canvas coordinates
            work_x1, work_y1, work_width, work_height = self.get_work_area_bounds()
            
            # Create temporary PostScript file
            import tempfile
            import os
            
            temp_ps_fd, temp_ps_path = tempfile.mkstemp(suffix='.ps')
            os.close(temp_ps_fd)  # Close file descriptor
            
            try:
                # Temporarily hide reference points and origin points for clean export
                hidden_items = []
                for item in self.canvas.find_withtag("reference_point"):
                    hidden_items.append(item)
                    self.canvas.itemconfig(item, state='hidden')
                
                # Also hide any origin point markers if they exist
                for item in self.canvas.find_all():
                    tags = self.canvas.gettags(item)
                    if 'origin' in tags:
                        hidden_items.append(item)
                        self.canvas.itemconfig(item, state='hidden')
                
                # Hide image resize handles (the 4 corner rectangles for resizing images)
                for item in self.canvas.find_withtag("image_handles"):
                    hidden_items.append(item)
                    self.canvas.itemconfig(item, state='hidden')
                
                # Hide all temporary UI elements (preview lines, info text, snap indicators, etc.)
                for item in self.canvas.find_withtag("temp"):
                    hidden_items.append(item)
                    self.canvas.itemconfig(item, state='hidden')
                
                # Hide snap indicators specifically
                for item in self.canvas.find_withtag("snap_indicator"):
                    hidden_items.append(item)
                    self.canvas.itemconfig(item, state='hidden')
                
                # Hide work area elements (border, grid, rulers) for clean export
                for work_area_item in self.work_area_objects:
                    hidden_items.append(work_area_item)
                    self.canvas.itemconfig(work_area_item, state='hidden')
                
                # Export canvas as PostScript (now only shows drawing objects on transparent/white background)
                self.canvas.postscript(file=temp_ps_path, colormode="color")
                
                # Restore all hidden items
                for item in hidden_items:
                    self.canvas.itemconfig(item, state='normal')
                
                # Try to open with Pillow (requires pillow with PostScript support)
                try:
                    # Import PIL with PostScript support
                    from PIL import Image
                    
                    # Open PostScript file
                    ps_image = Image.open(temp_ps_path)
                    
                    # Get canvas dimensions
                    canvas_width = self.canvas.winfo_width()
                    canvas_height = self.canvas.winfo_height()
                    
                    # Calculate the scale factor between PS image and canvas
                    ps_width, ps_height = ps_image.size
                    scale_x = ps_width / canvas_width
                    scale_y = ps_height / canvas_height
                    
                    # Calculate crop coordinates in PostScript image space
                    crop_x1 = int(work_x1 * scale_x)
                    crop_y1 = int(work_y1 * scale_y)
                    crop_x2 = int((work_x1 + work_width) * scale_x)
                    crop_y2 = int((work_y1 + work_height) * scale_y)
                    
                    # Ensure crop coordinates are within image bounds
                    crop_x1 = max(0, crop_x1)
                    crop_y1 = max(0, crop_y1)
                    crop_x2 = min(ps_width, crop_x2)
                    crop_y2 = min(ps_height, crop_y2)
                    
                    # Crop to work area
                    work_area_image = ps_image.crop((crop_x1, crop_y1, crop_x2, crop_y2))
                    
                    # Resize to target resolution
                    high_res_image = work_area_image.resize((target_width, target_height), Image.Resampling.NEAREST)
                    
                    # Apply color flipping if enabled
                    if self.flip_colors:
                        high_res_image = self._apply_color_flip(high_res_image)
                    
                    # Save as PNG
                    high_res_image.save(file_path, "PNG")
                    
                    # Show success message
                    messagebox.showinfo(
                        "Export Complete (v2)", 
                        f"High-resolution PNG saved using PostScript method:\n{file_path}\n\nResolution: {target_width}x{target_height} pixels\nCropped from: {crop_x2-crop_x1}x{crop_y2-crop_y1} PS pixels"
                    )
                    
                except ImportError:
                    messagebox.showerror(
                        "PostScript Support Missing", 
                        "Pillow PostScript support is not available.\n\nPlease install with:\npip install pillow[postscript]\n\nOr use the standard export method."
                    )
                except Exception as pil_error:
                    messagebox.showerror(
                        "PostScript Processing Error", 
                        f"Failed to process PostScript file:\n{str(pil_error)}\n\nThis might be due to missing PostScript support in Pillow.\nTry using the standard export method instead."
                    )
                    
            finally:
                # Clean up temporary PostScript file
                try:
                    os.unlink(temp_ps_path)
                except:
                    pass  # Ignore cleanup errors
                    
        except Exception as e:
            messagebox.showerror("Export Error (v2)", f"Failed to export PNG using PostScript method:\n{str(e)}")
            
    def _draw_object_on_image(self, draw, drawing_obj, scale_x, scale_y):
        """Draw a single object on PIL image."""
        obj_type = drawing_obj['type']
        real_coords = drawing_obj['real_coords']
        properties = drawing_obj['properties']
        
        # Skip reference points in export (they're just for editing)
        if obj_type == 'reference_point':
            return
            
        # Skip origin points in export (they're just for reference)
        if obj_type == 'origin':
            return
        
        # Calculate line width based on real mm width and scale
        width_mm = properties.get('width_mm', 0.1)  # Default 0.1mm
        line_width = max(1, int(width_mm * scale_x))  # Use actual mm width
        
        # Draw based on object type - handle coordinates differently for each type
        if obj_type == 'line':
            if len(real_coords) >= 4:
                # Convert line coordinates: [x1, y1, x2, y2]
                x1 = int(real_coords[0] * scale_x)
                y1 = int(real_coords[1] * scale_y)
                x2 = int(real_coords[2] * scale_x)
                y2 = int(real_coords[3] * scale_y)
                draw.line([x1, y1, x2, y2], fill='black', width=line_width)
                
        elif obj_type == 'rectangle':
            if len(real_coords) >= 4:
                # Convert rectangle coordinates: [x1, y1, x2, y2]
                x1 = int(real_coords[0] * scale_x)
                y1 = int(real_coords[1] * scale_y)
                x2 = int(real_coords[2] * scale_x)
                y2 = int(real_coords[3] * scale_y)
                
                # Ensure proper rectangle coordinates
                left = min(x1, x2)
                top = min(y1, y2)
                right = max(x1, x2)
                bottom = max(y1, y2)
                
                # Draw rectangle outline
                points = [(left, top), (right, top), (right, bottom), (left, bottom), (left, top)]
                for i in range(len(points) - 1):
                    draw.line([points[i], points[i+1]], fill='black', width=line_width)
                    
        elif obj_type == 'circle':
            # Handle circle objects in export
            if len(real_coords) >= 3:  # center_x, center_y, radius
                center_x_mm, center_y_mm, radius_mm = real_coords[0], real_coords[1], real_coords[2]
                
                # Convert to pixel coordinates
                center_pixel_x = int(center_x_mm * scale_x)
                center_pixel_y = int(center_y_mm * scale_y)
                radius_pixels = int(radius_mm * scale_x)  # Use scale_x for circular shape
                
                # Calculate circle bounds
                left = center_pixel_x - radius_pixels
                top = center_pixel_y - radius_pixels
                right = center_pixel_x + radius_pixels
                bottom = center_pixel_y + radius_pixels
                
                # Draw circle outline using PIL's ellipse method
                draw.ellipse([left, top, right, bottom], outline='black', width=line_width)
                    
        elif obj_type == 'image':
            # Handle image objects in export
            try:
                file_path = properties.get('file_path')
                width_mm = properties.get('width_mm', 20.0)
                height_mm = properties.get('height_mm', 20.0)
                
                if file_path and len(real_coords) >= 2:
                    # Convert center position: [center_x, center_y]
                    center_x = int(real_coords[0] * scale_x)
                    center_y = int(real_coords[1] * scale_y)
                    
                    # Load the original image
                    image_to_paste = Image.open(file_path)
                    
                    # Calculate target size in pixels
                    target_width = int(width_mm * scale_x)
                    target_height = int(height_mm * scale_y)
                    
                    # Resize image
                    resized_image = image_to_paste.resize((target_width, target_height), Image.Resampling.LANCZOS)
                    
                    # Convert to RGBA if needed for transparency support
                    if resized_image.mode != 'RGBA':
                        resized_image = resized_image.convert('RGBA')
                    
                    # Calculate paste position (center the image)
                    paste_x = center_x - target_width // 2
                    paste_y = center_y - target_height // 2
                    
                    # Create a temporary image for this object
                    temp_img = Image.new('RGBA', (target_width, target_height), (255, 255, 255, 0))
                    temp_img.paste(resized_image, (0, 0))
                    
                    # Get the main image (assuming it's RGB)
                    if hasattr(draw, '_image'):
                        main_image = draw._image
                        if main_image.mode == 'RGB':
                            # Convert temp image to RGB for pasting
                            white_bg = Image.new('RGB', temp_img.size, (255, 255, 255))
                            white_bg.paste(temp_img, mask=temp_img.split()[-1] if temp_img.mode == 'RGBA' else None)
                            main_image.paste(white_bg, (paste_x, paste_y))
                        else:
                            main_image.paste(temp_img, (paste_x, paste_y), temp_img if temp_img.mode == 'RGBA' else None)
                    
            except Exception as e:
                print(f"Error drawing image in export: {e}")
                # Draw a placeholder rectangle if image fails
                if len(real_coords) >= 2:
                    # Convert center position: [center_x, center_y]
                    center_x = int(real_coords[0] * scale_x)
                    center_y = int(real_coords[1] * scale_y)
                    
                    placeholder_width = int(properties.get('width_mm', 20.0) * scale_x)
                    placeholder_height = int(properties.get('height_mm', 20.0) * scale_y)
                    
                    left = center_x - placeholder_width // 2
                    top = center_y - placeholder_height // 2
                    right = center_x + placeholder_width // 2
                    bottom = center_y + placeholder_height // 2
                    
                    # Draw placeholder rectangle
                    points = [(left, top), (right, top), (right, bottom), (left, bottom), (left, top)]
                    for i in range(len(points) - 1):
                        draw.line([points[i], points[i+1]], fill='red', width=2)
            
    def close(self):
        """Close the sketching stage."""
        if self.window:
            self.window.destroy()
