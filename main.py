"""
G2burn Laser Engraving Application - Legacy Main File

This file is now deprecated. Please use project.py for the new OOP implementation.
Run: python project.py

Legacy code is preserved below for reference.
"""

# Import the new Project class
from project import Project

def main():
    """Main entry point - uses the new OOP implementation."""
    app = Project()
    app.run()

if __name__ == "__main__":
    main()

# ==========================================
# LEGACY CODE BELOW - PRESERVED FOR REFERENCE
# ==========================================

import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog

# Callback for opening the engraving workspace
def open_engraving_workspace_legacy(project_name, height, length):
    # Convert height and length to float
    real_height = float(height)
    real_length = float(length)
    
    # Create fullscreen workspace window
    workspace_window = tk.Toplevel(root)
    workspace_window.title(f"Laser Engraver - {project_name}")
    
    # Set window to fullscreen
    workspace_window.attributes('-fullscreen', True)
    
    # Add ability to exit fullscreen with Escape key
    workspace_window.bind('<Escape>', lambda e: workspace_window.attributes('-fullscreen', False))
    
    # Screen dimensions are in PIXELS!!!
    screen_width = workspace_window.winfo_screenwidth() 
    screen_height = workspace_window.winfo_screenheight()
    
    # Store project dimensions and zoom level in global variables
    workspace_data = {
        'project_name': project_name,
        'real_height': real_height,
        'real_length': real_length,
        'zoom_level': 1.0,
        'work_area_objects': [],  # Store IDs of work area objects for scaling
        'drawing_objects': [],    # Store drawing objects with their real coordinates
        'pan_start_x': 0,
        'pan_start_y': 0,
        'center_x': 0,  # Will store canvas center offset
        'center_y': 0   # Will store canvas center offset
    }
    
    # Create main layout structure
    # Menu bar at the top
    menu_frame = tk.Frame(workspace_window, height=40, bg="#f0f0f0")
    menu_frame.pack(side=tk.TOP, fill=tk.X)
    
    # Main content area
    content_frame = tk.Frame(workspace_window)
    content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    
    # Status bar at the bottom
    status_frame = tk.Frame(workspace_window, height=25, bg="#f0f0f0")
    status_frame.pack(side=tk.BOTTOM, fill=tk.X)
    
    # Create status indicators
    status_var = tk.StringVar()
    status_var.set("Mode: Select")
    status_label = tk.Label(status_frame, textvariable=status_var, font=("Arial", 9), bd=1, relief=tk.SUNKEN, anchor=tk.W)
    status_label.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=2, expand=True)
    
    # Zoom indicator
    zoom_var = tk.StringVar()
    zoom_var.set("Zoom: 100%")
    zoom_label = tk.Label(status_frame, textvariable=zoom_var, font=("Arial", 9), bd=1, relief=tk.SUNKEN, width=12)
    zoom_label.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=2)
    
    # Coordinates indicator
    coord_var = tk.StringVar()
    coord_var.set("X: 0mm Y: 0mm")
    coord_label = tk.Label(status_frame, textvariable=coord_var, font=("Arial", 9), bd=1, relief=tk.SUNKEN, width=16)
    coord_label.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=2)
    
    # Add menu buttons
    btn_width = 10
    
    # File operations
    file_frame = tk.Frame(menu_frame, bg="#f0f0f0")
    file_frame.pack(side=tk.LEFT, padx=5)
    
    tk.Button(file_frame, text="Save", width=btn_width, command=lambda: save_workspace(canvas, project_name)).pack(side=tk.LEFT, padx=2, pady=5)
    tk.Button(file_frame, text="Export", width=btn_width, command=lambda: export_workspace(canvas, project_name)).pack(side=tk.LEFT, padx=2, pady=5)
    
    # Tool buttons
    tools_frame = tk.Frame(menu_frame, bg="#f0f0f0")
    tools_frame.pack(side=tk.LEFT, padx=5)
    
    # "Select" button
    select_btn = tk.Button(tools_frame, text="Select", width=btn_width, 
                          command=lambda: update_mode(canvas, "select", status_var))
    select_btn.pack(side=tk.LEFT, padx=2, pady=5)
    

    # "Create new Line" button
    line_btn = tk.Button(tools_frame, text="Line", width=btn_width,
                        command=lambda: update_mode(canvas, "line", status_var))
    line_btn.pack(side=tk.LEFT, padx=2, pady=5)
    

    # "Create new Rectangle" button
    rect_btn = tk.Button(tools_frame, text="Rectangle", width=btn_width,
                        command=lambda: update_mode(canvas, "rect", status_var))
    rect_btn.pack(side=tk.LEFT, padx=2, pady=5)
    

    # "Clear Canvas" button
    tk.Button(tools_frame, text="Clear", width=btn_width,
             command=lambda: clear_canvas(canvas)).pack(side=tk.LEFT, padx=2, pady=5)
    
    # View controls
    view_frame = tk.Frame(menu_frame, bg="#f0f0f0")
    view_frame.pack(side=tk.RIGHT, padx=5)
    
    tk.Button(view_frame, text="Zoom In", width=btn_width,
             command=lambda: zoom_canvas(1.25, canvas, workspace_data, zoom_var)).pack(side=tk.LEFT, padx=2, pady=5)
    
    tk.Button(view_frame, text="Zoom Out", width=btn_width,
             command=lambda: zoom_canvas(0.8, canvas, workspace_data, zoom_var)).pack(side=tk.LEFT, padx=2, pady=5)
    
    tk.Button(view_frame, text="Reset View", width=btn_width,
             command=lambda: reset_view(canvas, workspace_data, zoom_var)).pack(side=tk.LEFT, padx=2, pady=5)
    
    tk.Button(view_frame, text="G-Code", width=btn_width,
             command=lambda: generate_gcode(canvas, real_length, real_height)).pack(side=tk.LEFT, padx=2, pady=5)
    
    # Create canvas with scrollbars in content frame
    canvas_frame = tk.Frame(content_frame)
    canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Create canvas with dark background to show working area
    canvas = tk.Canvas(canvas_frame, bg="#303030", relief=tk.SUNKEN, bd=0,
                      highlightthickness=0, width=screen_width-40, height=screen_height-100)
    canvas.pack(fill=tk.BOTH, expand=True)
    
    # Calculate initial work area size 
    # Make working area take up about 70% of available screen space initially
    max_width = int(screen_width * 0.7)
    max_height = int(screen_height * 0.7)
    
    # Calculate scaling to fit work area while maintaining aspect ratio
    width_scale = max_width / real_length
    height_scale = max_height / real_height
    initial_scale = min(width_scale, height_scale)
    
    # Calculate initial work area dimensions
    work_width = int(real_length * initial_scale)
    work_height = int(real_height * initial_scale)
    
    # Calculate center position to place the work area
    workspace_data['center_x'] = (screen_width - work_width) // 2
    workspace_data['center_y'] = (screen_height - work_height) // 2
    
    # Draw the work area in the center of the canvas
    draw_work_area(canvas, workspace_data, work_width, work_height)
    
    # Bind mouse wheel for zooming
    canvas.bind("<MouseWheel>", lambda e: mouse_zoom(e, canvas, workspace_data, zoom_var))  # Windows/MacOS
    canvas.bind("<Button-4>", lambda e: mouse_zoom(e, canvas, workspace_data, zoom_var))  # Linux scroll up
    canvas.bind("<Button-5>", lambda e: mouse_zoom(e, canvas, workspace_data, zoom_var))  # Linux scroll down
    
    # Bind middle mouse button for panning
    canvas.bind("<ButtonPress-2>", lambda e: start_pan(e, canvas, workspace_data))
    canvas.bind("<B2-Motion>", lambda e: pan_canvas(e, canvas, workspace_data))
    
    # Bind mouse movement to update coordinates display
    canvas.bind("<Motion>", lambda e: update_coordinates(e, canvas, workspace_data, coord_var))
    
    # Helper function to update mode and status
    def update_mode(canvas, mode, status_var):
        set_draw_mode(canvas, mode)
        mode_display = {
            "select": "Select - Click to select objects",
            "line": "Drawing Line - Click to place points",
            "rect": "Drawing Rectangle - Click and drag"
        }
        status_var.set(f"Mode: {mode_display.get(mode, mode)}")
        
    # Register workspace with the main window
    workspace_window.workspace_data = workspace_data
    workspace_window.canvas = canvas

def draw_work_area(canvas, workspace_data, width, height):
    """Draw the working area on the canvas with the specified dimensions"""
    # Clear previous work area objects
    for obj_id in workspace_data['work_area_objects']:
        canvas.delete(obj_id)
    workspace_data['work_area_objects'] = []
    
    # Calculate top-left corner from center point
    x1 = workspace_data['center_x'] - (width // 2)
    y1 = workspace_data['center_y'] - (height // 2)
    x2 = x1 + width
    y2 = y1 + height
    
    # Draw white background of working area
    bg_id = canvas.create_rectangle(x1, y1, x2, y2, 
                                  fill="white", outline="gray")
    workspace_data['work_area_objects'].append(bg_id)
    
    # Draw border
    border_id = canvas.create_rectangle(x1, y1, x2, y2, 
                                      outline="black", width=2)
    workspace_data['work_area_objects'].append(border_id)
    
    # Calculate grid spacing based on zoom level
    # Use a fixed number of grid cells regardless of zoom
    cells = 20
    x_spacing = width / cells
    y_spacing = height / cells
    
    # Draw grid lines
    for i in range(1, cells):
        # Vertical lines
        x = x1 + (i * x_spacing)
        line_id = canvas.create_line(x, y1, x, y2, 
                                   fill="lightgray", dash=(1, 1))
        workspace_data['work_area_objects'].append(line_id)
        
        # Horizontal lines
        y = y1 + (i * y_spacing)
        line_id = canvas.create_line(x1, y, x2, y, 
                                   fill="lightgray", dash=(1, 1))
        workspace_data['work_area_objects'].append(line_id)
    
    # Draw rulers
    ruler_width = 20
    
    # Top ruler background
    top_ruler_id = canvas.create_rectangle(
        x1, y1 - ruler_width, x2, y1, 
        fill="#f0f0f0", outline="gray")
    workspace_data['work_area_objects'].append(top_ruler_id)
    
    # Left ruler background
    left_ruler_id = canvas.create_rectangle(
        x1 - ruler_width, y1, x1, y2, 
        fill="#f0f0f0", outline="gray")
    workspace_data['work_area_objects'].append(left_ruler_id)
    
    # Add tick marks and labels to rulers
    tick_spacing = width / 10
    for i in range(11):
        # Position for tick mark
        tick_x = x1 + (i * tick_spacing)
        
        # Draw tick on top ruler
        tick_id = canvas.create_line(
            tick_x, y1 - 5, tick_x, y1,
            fill="black")
        workspace_data['work_area_objects'].append(tick_id)
        
        # Add label for tick (in mm)
        mm_value = int((i / 10) * workspace_data['real_length'])
        label_id = canvas.create_text(
            tick_x, y1 - 10,
            text=f"{mm_value}",
            font=("Arial", 7),
            anchor="s")
        workspace_data['work_area_objects'].append(label_id)
    
    # Add tick marks to left ruler
    tick_spacing = height / 10
    for i in range(11):
        # Position for tick mark
        tick_y = y1 + (i * tick_spacing)
        
        # Draw tick on left ruler
        tick_id = canvas.create_line(
            x1 - 5, tick_y, x1, tick_y,
            fill="black")
        workspace_data['work_area_objects'].append(tick_id)
        
        # Add label for tick (in mm)
        mm_value = int((i / 10) * workspace_data['real_height'])
        label_id = canvas.create_text(
            x1 - 10, tick_y,
            text=f"{mm_value}",
            font=("Arial", 7),
            anchor="e")
        workspace_data['work_area_objects'].append(label_id)

def zoom_canvas(factor, canvas, workspace_data, zoom_var):
    """Zoom the canvas by the specified factor"""
    # Update zoom level
    workspace_data['zoom_level'] *= factor
    
    # Update the zoom display
    zoom_percent = int(workspace_data['zoom_level'] * 100)
    zoom_var.set(f"Zoom: {zoom_percent}%")
    
    # Calculate new work area dimensions
    width = int(workspace_data['real_length'] * workspace_data['zoom_level'])
    height = int(workspace_data['real_height'] * workspace_data['zoom_level'])
    
    # Clear all canvas objects before redrawing
    canvas.delete("all")
    
    # Redraw the work area with new dimensions
    draw_work_area(canvas, workspace_data, width, height)
    
    # Redraw all drawing objects at their scaled positions
    redraw_all_drawing_objects(canvas, workspace_data)

def mouse_zoom(event, canvas, workspace_data, zoom_var):
    """Handle mouse wheel zoom events"""
    # Get zoom direction
    if event.num == 4 or event.delta > 0:  # Zoom in
        factor = 1.1
    else:  # Zoom out
        factor = 0.9
    
    # Apply zoom
    zoom_canvas(factor, canvas, workspace_data, zoom_var)

def start_pan(event, canvas, workspace_data):
    """Start canvas panning operation"""
    workspace_data['pan_start_x'] = event.x
    workspace_data['pan_start_y'] = event.y
    canvas.config(cursor="fleur")  # Change cursor to hand/move icon

def redraw_all_drawing_objects(canvas, workspace_data):
    """Redraw all stored drawing objects on the canvas at their scaled positions"""
    # Calculate work area bounds
    width = int(workspace_data['real_length'] * workspace_data['zoom_level'])
    height = int(workspace_data['real_height'] * workspace_data['zoom_level'])
    x1 = workspace_data['center_x'] - (width // 2)
    y1 = workspace_data['center_y'] - (height // 2)
    
    # For each stored drawing object
    for drawing_obj in workspace_data['drawing_objects']:
        obj_type = drawing_obj['type']
        real_coords = drawing_obj['real_coords']
        properties = drawing_obj['properties']
        
        # Convert real mm coordinates to canvas coordinates
        canvas_coords = []
        for i in range(0, len(real_coords), 2):
            # Calculate position based on real coordinates (in mm) and apply zoom
            canvas_x = x1 + (real_coords[i] * workspace_data['zoom_level'])
            canvas_y = y1 + (real_coords[i+1] * workspace_data['zoom_level'])
            canvas_coords.extend([canvas_x, canvas_y])
        
        # Create the appropriate shape
        if obj_type == 'line':
            canvas.create_line(
                canvas_coords,
                fill=properties.get('fill', 'black'),
                width=properties.get('width', 2),
                tags="drawing"
            )
        elif obj_type == 'rectangle':
            canvas.create_rectangle(
                canvas_coords,
                outline=properties.get('outline', 'black'),
                width=properties.get('width', 2),
                fill=properties.get('fill', ''),
                tags="drawing"
            )
        elif obj_type == 'oval':
            canvas.create_oval(
                canvas_coords,
                outline=properties.get('outline', 'black'),
                fill=properties.get('fill', ''),
                width=properties.get('width', 2),
                tags="drawing"
            )

def pan_canvas(event, canvas, workspace_data):
    """Pan the canvas based on mouse movement"""
    # Calculate the movement
    dx = event.x - workspace_data['pan_start_x']
    dy = event.y - workspace_data['pan_start_y']
    
    # Update center position
    workspace_data['center_x'] += dx
    workspace_data['center_y'] += dy
    
    # Update pan start position
    workspace_data['pan_start_x'] = event.x
    workspace_data['pan_start_y'] = event.y
    
    # Clear the canvas and redraw everything
    canvas.delete("all")
    
    # Calculate current dimensions
    width = int(workspace_data['real_length'] * workspace_data['zoom_level'])
    height = int(workspace_data['real_height'] * workspace_data['zoom_level'])
    
    # Redraw work area at new position
    draw_work_area(canvas, workspace_data, width, height)
    
    # Redraw all drawing objects at their scaled positions
    redraw_all_drawing_objects(canvas, workspace_data)

def reset_view(canvas, workspace_data, zoom_var):
    """Reset the view to initial state"""
    # Reset zoom level
    workspace_data['zoom_level'] = 1.0
    zoom_var.set("Zoom: 100%")
    
    # Get screen dimensions
    screen_width = canvas.winfo_width()
    screen_height = canvas.winfo_height()
    
    # Calculate initial work area size again
    max_width = int(screen_width * 0.7)
    max_height = int(screen_height * 0.7)
    
    width_scale = max_width / workspace_data['real_length']
    height_scale = max_height / workspace_data['real_height']
    initial_scale = min(width_scale, height_scale)
    
    # Reset zoom level to calculated initial scale
    workspace_data['zoom_level'] = initial_scale
    
    # Update zoom display
    zoom_percent = int(workspace_data['zoom_level'] * 100)
    zoom_var.set(f"Zoom: {zoom_percent}%")
    
    # Calculate dimensions
    width = int(workspace_data['real_length'] * workspace_data['zoom_level'])
    height = int(workspace_data['real_height'] * workspace_data['zoom_level'])
    
    # Reset center position
    workspace_data['center_x'] = screen_width // 2
    workspace_data['center_y'] = screen_height // 2
    
    # Clear canvas
    canvas.delete("all")
    
    # Redraw work area
    draw_work_area(canvas, workspace_data, width, height)
    
    # Redraw all drawing objects
    redraw_all_drawing_objects(canvas, workspace_data)

def update_coordinates(event, canvas, workspace_data, coord_var):
    """Update coordinate display based on mouse position"""
    # Calculate current dimensions
    width = int(workspace_data['real_length'] * workspace_data['zoom_level'])
    height = int(workspace_data['real_height'] * workspace_data['zoom_level'])
    
    # Calculate top-left corner from center point
    x1 = workspace_data['center_x'] - (width // 2)
    y1 = workspace_data['center_y'] - (height // 2)
    
    # Check if mouse is within the work area
    if (x1 <= event.x <= x1 + width and y1 <= event.y <= y1 + height):
        # Convert canvas coordinates to mm
        mm_x = (event.x - x1) / workspace_data['zoom_level']
        mm_y = (event.y - y1) / workspace_data['zoom_level']
        coord_var.set(f"X: {mm_x:.1f}mm Y: {mm_y:.1f}mm")
    else:
        coord_var.set("X: -- Y: --")

def save_workspace(canvas, project_name):
    """Save the current workspace"""
    messagebox.showinfo("Save", f"Project '{project_name}' saved.")
    # Add actual save functionality here

def export_workspace(canvas, project_name):
    """Export the workspace to a file"""
    file_types = [
        ("G-code files", "*.gcode *.nc"),
        ("SVG files", "*.svg"),
        ("All files", "*.*")
    ]
    file_path = filedialog.asksaveasfilename(
        title="Export Project",
        defaultextension=".gcode",
        filetypes=file_types,
        initialfile=f"{project_name}"
    )
    if file_path:
        messagebox.showinfo("Export", f"Project exported to {file_path}")
        # Add actual export functionality here

# Drawing mode variables
current_draw_mode = "select"
start_x = start_y = 0
is_first_click = True  # Track whether we're placing first or second point
line_preview_id = None  # ID of the temporary preview line

# Custom cursors
def create_line_cursor():
    """Create a custom line cursor"""
    # This creates a simple line cursor using font characters
    # Another option would be to create a cursor from a .cur file
    return "crosshair"  # Fallback to a crosshair cursor

def set_draw_mode(canvas, mode):
    global current_draw_mode, is_first_click
    
    # Reset variables
    is_first_click = True
    
    # Remove any existing preview elements
    canvas.delete("temp")
    
    # Reset previous bindings
    canvas.unbind("<Button-1>") #Click
    canvas.unbind("<B1-Motion>") # Dragging
    canvas.unbind("<ButtonRelease-1>") # Release click
    
    # Make sure we preserve the coordinate tracking motion handler
    preserve_motion_handlers(canvas)
    
    # Set cursor back to default
    canvas.config(cursor="")
    
    current_draw_mode = mode
    if mode == "line":
        # Change cursor to line drawing cursor
        canvas.config(cursor=create_line_cursor())
        
        # Bind click for placing points
        canvas.bind("<Button-1>", lambda e: handle_line_click(e, canvas))
        
        # Bind mouse motion for preview line
        original_motion = canvas.bind("<Motion>")
        canvas.bind("<Motion>", lambda e: handle_motion_with_line_preview(e, canvas, original_motion))
    elif mode == "rect":
        canvas.bind("<Button-1>", lambda e: start_draw(e, canvas))
        canvas.bind("<B1-Motion>", lambda e: draw_rect(e, canvas))
        canvas.bind("<ButtonRelease-1>", lambda e: finish_rect(e, canvas))
    else:
        # Default select mode
        canvas.config(cursor="")

def preserve_motion_handlers(canvas):
    """Preserve existing motion handlers that track coordinates"""
    # We'll store the original handler and call it after our function
    canvas._original_motion_handler = canvas.bind("<Motion>")

def handle_motion_with_line_preview(event, canvas, original_handler):
    """Handle motion event for line preview while preserving original handler"""
    # First update line preview
    update_line_preview(event, canvas)
    
    # Then call the original handler if it exists
    if original_handler:
        canvas.bind("<Motion>", original_handler)

def is_point_in_work_area(event, canvas):
    """Check if point is within the work area"""
    # Get workspace data from the parent window
    workspace_data = canvas.winfo_toplevel().workspace_data
    
    # Calculate current dimensions
    width = int(workspace_data['real_length'] * workspace_data['zoom_level'])
    height = int(workspace_data['real_height'] * workspace_data['zoom_level'])
    
    # Calculate top-left corner from center point
    x1 = workspace_data['center_x'] - (width // 2)
    y1 = workspace_data['center_y'] - (height // 2)
    x2 = x1 + width
    y2 = y1 + height
    
    # Check if point is within work area
    return (x1 <= event.x <= x2) and (y1 <= event.y <= y2)

def handle_line_click(event, canvas):
    """Handle clicks for line drawing mode"""
    global is_first_click, start_x, start_y, line_preview_id
    
    # Only draw if clicking within work area
    if not is_point_in_work_area(event, canvas):
        return
    
    # Get workspace data
    workspace_data = canvas.winfo_toplevel().workspace_data
    
    # Calculate work area bounds
    width = int(workspace_data['real_length'] * workspace_data['zoom_level'])
    height = int(workspace_data['real_height'] * workspace_data['zoom_level'])
    x1 = workspace_data['center_x'] - (width // 2)
    y1 = workspace_data['center_y'] - (height // 2)
    
    if is_first_click:
        # First click: Store starting point
        start_x, start_y = event.x, event.y
        
        # Create a temporary point marker
        canvas.create_oval(start_x-3, start_y-3, start_x+3, start_y+3, 
                          fill="gray", outline="black", tags="temp")
        
        is_first_click = False
    else:
        # Second click: Create the actual line
        canvas.create_line(start_x, start_y, event.x, event.y, 
                          fill="black", width=2, tags="drawing")
        
        # Convert canvas coordinates to real mm coordinates
        real_x1 = (start_x - x1) / workspace_data['zoom_level']
        real_y1 = (start_y - y1) / workspace_data['zoom_level']
        real_x2 = (event.x - x1) / workspace_data['zoom_level']
        real_y2 = (event.y - y1) / workspace_data['zoom_level']
        
        # Store the drawing object with its real coordinates
        drawing_obj = {
            'type': 'line',
            'real_coords': [real_x1, real_y1, real_x2, real_y2],
            'properties': {
                'fill': 'black',
                'width': 2
            }
        }
        workspace_data['drawing_objects'].append(drawing_obj)
        
        # Clear temporary elements
        canvas.delete("temp")
        
        # Reset for next line
        is_first_click = True
        line_preview_id = None

def update_line_preview(event, canvas):
    """Update the preview line as mouse moves"""
    global is_first_click, start_x, start_y, line_preview_id
    
    # Only show preview if we're waiting for second click and mouse is in work area
    if not is_first_click:
        # Delete previous preview line if exists
        if line_preview_id:
            canvas.delete(line_preview_id)
        
        # Create new preview line
        line_preview_id = canvas.create_line(start_x, start_y, event.x, event.y, 
                                           fill="gray", width=2, dash=(4, 2),
                                           tags="temp")

def start_draw(event, canvas):
    """Start drawing a rectangle"""
    global start_x, start_y
    
    # Only start drawing if within work area
    if is_point_in_work_area(event, canvas):
        start_x, start_y = event.x, event.y

def draw_rect(event, canvas):
    """Draw preview rectangle while dragging"""
    global start_x, start_y
    
    # Only draw if we have a valid start point
    if start_x == 0 and start_y == 0:
        return
        
    canvas.delete("temp_rect")
    canvas.create_rectangle(start_x, start_y, event.x, event.y, 
                           outline="red", width=2, tags="temp_rect temp")

def finish_rect(event, canvas):
    """Finalize rectangle on mouse release"""
    global start_x, start_y
    
    # Convert temporary rectangle to permanent if we have a valid start point
    if start_x == 0 and start_y == 0:
        return
        
    # Only finalize if end point is within work area
    if is_point_in_work_area(event, canvas):
        coords = canvas.coords("temp_rect")
        if coords:
            # Get workspace data
            workspace_data = canvas.winfo_toplevel().workspace_data
            
            # Calculate work area bounds
            width = int(workspace_data['real_length'] * workspace_data['zoom_level'])
            height = int(workspace_data['real_height'] * workspace_data['zoom_level'])
            x1_area = workspace_data['center_x'] - (width // 2)
            y1_area = workspace_data['center_y'] - (height // 2)
            
            # Create the visual rectangle
            canvas.create_rectangle(coords, outline="black", width=2, tags="drawing")
            
            # Convert canvas coordinates to real mm coordinates
            real_x1 = (coords[0] - x1_area) / workspace_data['zoom_level']
            real_y1 = (coords[1] - y1_area) / workspace_data['zoom_level']
            real_x2 = (coords[2] - x1_area) / workspace_data['zoom_level']
            real_y2 = (coords[3] - y1_area) / workspace_data['zoom_level']
            
            # Store the drawing object with its real coordinates
            drawing_obj = {
                'type': 'rectangle',
                'real_coords': [real_x1, real_y1, real_x2, real_y2],
                'properties': {
                    'outline': 'black',
                    'width': 2,
                    'fill': ''
                }
            }
            workspace_data['drawing_objects'].append(drawing_obj)
            
    # Clean up
    canvas.delete("temp_rect")
    start_x = start_y = 0

def clear_canvas(canvas):
    """Clear all drawings while preserving the work area"""
    # Get workspace data from the parent window
    try:
        workspace_data = canvas.winfo_toplevel().workspace_data
        
        # Clear the drawing objects list
        workspace_data['drawing_objects'] = []
        
        # Clear only drawing and temporary elements on the canvas
        canvas.delete("drawing")
        canvas.delete("temp")
        
        # Redraw the work area to ensure it's clean
        width = int(workspace_data['real_length'] * workspace_data['zoom_level'])
        height = int(workspace_data['real_height'] * workspace_data['zoom_level'])
        draw_work_area(canvas, workspace_data, width, height)
    except (AttributeError, TypeError):
        # Fallback for older code or testing
        canvas.delete("drawing")
        canvas.delete("temp")
    
    global is_first_click, line_preview_id, start_x, start_y
    # Reset drawing state
    is_first_click = True
    line_preview_id = None
    start_x = start_y = 0

def load_image(canvas):
    from tkinter import filedialog
    file_path = filedialog.askopenfilename(
        title="Select Image",
        filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
    )
    if file_path:
        try:
            from PIL import Image, ImageTk
            img = Image.open(file_path)
            # Resize image to fit canvas
            img.thumbnail((canvas.winfo_width()-20, canvas.winfo_height()-20))
            photo = ImageTk.PhotoImage(img)
            canvas.create_image(canvas.winfo_width()//2, canvas.winfo_height()//2, 
                              image=photo, tags="drawing")
            # Keep a reference to prevent garbage collection
            canvas.image = photo
        except ImportError:
            messagebox.showwarning("Missing Library", "PIL (Pillow) is required for image loading.\nInstall with: pip install Pillow")
        except Exception as e:
            messagebox.showerror("Error", f"Could not load image: {str(e)}")

def generate_gcode(canvas, length, height):
    """Generate G-code from the current canvas objects"""
    # Try to get workspace data to convert coordinates properly
    try:
        workspace_data = canvas.winfo_toplevel().workspace_data
        
        # Calculate work area bounds
        width = int(workspace_data['real_length'] * workspace_data['zoom_level'])
        height = int(workspace_data['real_height'] * workspace_data['zoom_level'])
        x1 = workspace_data['center_x'] - (width // 2)
        y1 = workspace_data['center_y'] - (height // 2)
        
        # Function to convert canvas coordinates to mm
        def to_mm(canvas_coord, origin, zoom):
            return (canvas_coord - origin) / zoom
        
        # Collect drawing objects on the canvas
        drawing_objects = canvas.find_withtag("drawing")
        gcode_commands = []
        
        # Process each drawing object
        for obj_id in drawing_objects:
            obj_type = canvas.type(obj_id)
            coords = canvas.coords(obj_id)
            
            if obj_type == "line":
                # Convert line coordinates to mm
                x_start = to_mm(coords[0], x1, workspace_data['zoom_level'])
                y_start = to_mm(coords[1], y1, workspace_data['zoom_level'])
                x_end = to_mm(coords[2], x1, workspace_data['zoom_level'])
                y_end = to_mm(coords[3], y1, workspace_data['zoom_level'])
                
                # Add G-code for line
                gcode_commands.extend([
                    f"G0 X{x_start:.3f} Y{y_start:.3f} ; Move to start",
                    "M3 S255 ; Laser on",
                    f"G1 X{x_end:.3f} Y{y_end:.3f} F1000 ; Line to end",
                    "M5 ; Laser off"
                ])
            
            elif obj_type == "rectangle":
                # Convert rectangle coordinates to mm
                x1_rect = to_mm(coords[0], x1, workspace_data['zoom_level'])
                y1_rect = to_mm(coords[1], y1, workspace_data['zoom_level'])
                x2_rect = to_mm(coords[2], x1, workspace_data['zoom_level'])
                y2_rect = to_mm(coords[3], y1, workspace_data['zoom_level'])
                
                # Add G-code for rectangle
                gcode_commands.extend([
                    f"G0 X{x1_rect:.3f} Y{y1_rect:.3f} ; Move to corner 1",
                    "M3 S255 ; Laser on",
                    f"G1 X{x2_rect:.3f} Y{y1_rect:.3f} F1000 ; Line to corner 2",
                    f"G1 X{x2_rect:.3f} Y{y2_rect:.3f} F1000 ; Line to corner 3",
                    f"G1 X{x1_rect:.3f} Y{y2_rect:.3f} F1000 ; Line to corner 4",
                    f"G1 X{x1_rect:.3f} Y{y1_rect:.3f} F1000 ; Line back to corner 1",
                    "M5 ; Laser off"
                ])
    
    except (AttributeError, TypeError):
        # Fallback for basic G-code if workspace data not available
        gcode_commands = []
    
    # Basic G-code header
    gcode_header = [
        "; G-code generated by Laser Engraver App",
        "G21 ; Set units to millimeters",
        "G90 ; Absolute positioning",
        "G28 ; Home all axes",
        f"; Workspace: {length}mm x {height}mm",
        "M3 S0 ; Laser off",
        "G0 X0 Y0 ; Move to origin"
    ]
    
    # Basic G-code footer
    gcode_footer = [
        "M5 ; Laser off",
        "G0 X0 Y0 ; Return to origin",
        "M30 ; Program end"
    ]
    
    # Combine all G-code sections
    if not gcode_commands:
        gcode_commands = ["; No drawing objects found"]
    
    gcode = gcode_header + gcode_commands + gcode_footer
    
    # Show G-code in a new window
    gcode_window = tk.Toplevel()
    gcode_window.title("Generated G-Code")
    gcode_window.geometry("500x400")
    
    # Add save button
    save_frame = tk.Frame(gcode_window)
    save_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
    
    tk.Button(save_frame, text="Save G-code", 
             command=lambda: save_gcode_to_file(gcode)).pack(side=tk.RIGHT)
    
    # Text area for G-code
    text_widget = tk.Text(gcode_window, wrap=tk.WORD)
    text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    scrollbar = tk.Scrollbar(gcode_window, orient=tk.VERTICAL, command=text_widget.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    text_widget.config(yscrollcommand=scrollbar.set)
    
    text_widget.insert(tk.END, "\n".join(gcode))

def save_gcode_to_file(gcode_lines):
    """Save generated G-code to a file"""
    file_path = filedialog.asksaveasfilename(
        defaultextension=".gcode",
        filetypes=[("G-code files", "*.gcode"), ("NC files", "*.nc"), ("All files", "*.*")]
    )
    if file_path:
        with open(file_path, 'w') as f:
            f.write("\n".join(gcode_lines))
        messagebox.showinfo("G-code Saved", f"G-code saved to {file_path}")
    return file_path

# Callback for saving the project - LEGACY
def save_project_legacy():
    # This function is now part of the legacy code
    pass

# Callback for opening new project window - LEGACY  
def new_project_legacy():
    # This function is now part of the legacy code
    pass

# Main window - LEGACY
def create_legacy_main():
    root = tk.Tk()
    root.title("Laser Engraver App")

    new_project_btn = tk.Button(root, text="New Project", command=new_project_legacy)
    new_project_btn.pack(padx=50, pady=30)

    root.mainloop()

# Uncomment below to run legacy version
# create_legacy_main()

# ==========================================
# END OF LEGACY CODE
# ==========================================
