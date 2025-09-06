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
        
        # Tool buttons frame (will be populated by DrawingToolManager)
        self.tools_frame = tk.Frame(self.menu_frame, bg="#f0f0f0")
        self.tools_frame.pack(side=tk.LEFT, padx=5)
        
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
        
        # Advanced settings button
        tk.Button(
            view_frame, 
            text="Advanced", 
            width=btn_width,
            font=("Arial", 9),
            command=self.show_advanced_settings
        ).pack(side=tk.LEFT, padx=1, pady=3)
        
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
        
    def add_drawing_object(self, obj_type, real_coords, properties):
        """Add a drawing object to the workspace."""
        drawing_obj = {
            'type': obj_type,
            'real_coords': real_coords,
            'properties': properties,
            'layer_id': self.layers.get_active_layer_id() if hasattr(self, 'layers') else 'default'
        }
        self.drawing_objects.append(drawing_obj)
        
        # Update layers panel if it exists
        if hasattr(self, 'layers'):
            self.layers.refresh_layer_objects()
        
    def clear_canvas(self):
        """Clear all drawings while preserving the work area."""
        self.drawing_objects = []
        self.canvas.delete("drawing")
        self.canvas.delete("temp")
        self.canvas.delete("snap_indicator")
        
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
            
    def generate_gcode(self):
        """Generate G-code from the current drawing objects."""
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
                
                # Show preview window
                self.gcode_generator.show_preview_window(temp_image_path, gcode_commands, origin_pixels)
            
            # Note: Don't clean up temp file immediately as preview window needs it
            # The file will be cleaned up when the system clears temp files
                
    def _find_origin_point(self):
        """Find the origin point from drawing objects.
        
        Returns:
            tuple: Origin coordinates as (x, y) in mm, or None if not found
        """
        for drawing_obj in self.drawing_objects:
            if drawing_obj['type'] == 'origin':
                real_coords = drawing_obj['real_coords']
                if len(real_coords) >= 2:
                    return (real_coords[0], real_coords[1])
        return None
        
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
        """Export a temporary high-resolution PNG image for processing.
        
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
            
            return temp_path
            
        except Exception as e:
            print(f"Error creating temporary image: {e}")
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
