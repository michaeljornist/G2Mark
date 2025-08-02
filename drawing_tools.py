"""
Drawing tools manager for the G2burn Laser Engraving Application.
This module manages different drawing tools and their interactions.
"""

import tkinter as tk
from abc import ABC, abstractmethod


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
        
    def activate(self):
        """Activate the line tool."""
        self.is_active = True
        self.is_first_click = True
        self.canvas.config(cursor="crosshair")
        
        # Clear any existing bindings
        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")
        
        # Bind events for line drawing
        self.canvas.bind("<Button-1>", self._handle_click)
        
        # Preserve the original motion handler for coordinate tracking
        original_motion = self.canvas.bind("<Motion>")
        self.canvas.bind("<Motion>", lambda e: self._handle_motion(e, original_motion))
        
    def deactivate(self):
        """Deactivate the line tool."""
        self.is_active = False
        self.canvas.delete("temp")
        self.is_first_click = True
        self.preview_line_id = None
        
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
            
        if self.is_first_click:
            # First click: Store starting point
            self.start_x, self.start_y = event.x, event.y
            
            # Create a temporary point marker
            self.canvas.create_oval(
                self.start_x-3, self.start_y-3, 
                self.start_x+3, self.start_y+3, 
                fill="gray", outline="black", tags="temp"
            )
            
            self.is_first_click = False
            
        else:
            # Second click: Create the actual line
            self.canvas.create_line(
                self.start_x, self.start_y, event.x, event.y, 
                fill="black", width=2, tags="drawing"
            )
            
            # Convert canvas coordinates to real mm coordinates
            real_x1, real_y1 = self.sketching_stage.canvas_to_mm(self.start_x, self.start_y)
            real_x2, real_y2 = self.sketching_stage.canvas_to_mm(event.x, event.y)
            
            # Store the drawing object
            self.sketching_stage.add_drawing_object(
                'line',
                [real_x1, real_y1, real_x2, real_y2],
                {'fill': 'black', 'width': 2}
            )
            
            # Clear temporary elements and reset
            self.canvas.delete("temp")
            self.is_first_click = True
            self.preview_line_id = None
            
    def _handle_motion(self, event, original_handler):
        """Handle mouse motion for line preview."""
        # Update line preview
        self._update_preview(event)
        
        # Call original motion handler for coordinate tracking
        if original_handler and hasattr(self.sketching_stage, '_update_coordinates'):
            self.sketching_stage._update_coordinates(event)
            
    def _update_preview(self, event):
        """Update the preview line as mouse moves."""
        # Only show preview if waiting for second click
        if not self.is_first_click:
            # Delete previous preview line
            if self.preview_line_id:
                self.canvas.delete(self.preview_line_id)
                
            # Create new preview line
            self.preview_line_id = self.canvas.create_line(
                self.start_x, self.start_y, event.x, event.y, 
                fill="gray", width=2, dash=(4, 2), tags="temp"
            )


class RectangleTool(DrawingTool):
    """Tool for drawing rectangles."""
    
    def __init__(self, canvas, sketching_stage):
        """Initialize the rectangle tool."""
        super().__init__(canvas, sketching_stage)
        self.start_x = 0
        self.start_y = 0
        
    def activate(self):
        """Activate the rectangle tool."""
        self.is_active = True
        self.canvas.config(cursor="crosshair")
        
        # Clear any existing bindings
        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")
        
        # Bind events for rectangle drawing
        self.canvas.bind("<Button-1>", self._start_draw)
        self.canvas.bind("<B1-Motion>", self._draw_preview)
        self.canvas.bind("<ButtonRelease-1>", self._finish_draw)
        
    def deactivate(self):
        """Deactivate the rectangle tool."""
        self.is_active = False
        self.canvas.delete("temp_rect")
        self.start_x = 0
        self.start_y = 0
        
    def get_cursor(self):
        """Get the cursor for this tool."""
        return "crosshair"
        
    def get_status_text(self):
        """Get the status text for this tool."""
        return "Drawing Rectangle - Click and drag"
        
    def _start_draw(self, event):
        """Start drawing a rectangle."""
        # Only start drawing if within work area
        if self.sketching_stage.is_point_in_work_area(event.x, event.y):
            self.start_x, self.start_y = event.x, event.y
            
    def _draw_preview(self, event):
        """Draw preview rectangle while dragging."""
        # Only draw if we have a valid start point
        if self.start_x == 0 and self.start_y == 0:
            return
            
        self.canvas.delete("temp_rect")
        self.canvas.create_rectangle(
            self.start_x, self.start_y, event.x, event.y, 
            outline="red", width=2, tags="temp_rect temp"
        )
        
    def _finish_draw(self, event):
        """Finalize rectangle on mouse release."""
        # Only finalize if we have a valid start point and end is in work area
        if (self.start_x == 0 and self.start_y == 0 or 
            not self.sketching_stage.is_point_in_work_area(event.x, event.y)):
            self.canvas.delete("temp_rect")
            self.start_x = self.start_y = 0
            return
            
        coords = self.canvas.coords("temp_rect")
        if coords:
            # Create the visual rectangle
            self.canvas.create_rectangle(
                coords, outline="black", width=2, tags="drawing"
            )
            
            # Convert canvas coordinates to real mm coordinates
            real_x1, real_y1 = self.sketching_stage.canvas_to_mm(coords[0], coords[1])
            real_x2, real_y2 = self.sketching_stage.canvas_to_mm(coords[2], coords[3])
            
            # Store the drawing object
            self.sketching_stage.add_drawing_object(
                'rectangle',
                [real_x1, real_y1, real_x2, real_y2],
                {'outline': 'black', 'width': 2, 'fill': ''}
            )
            
        # Clean up
        self.canvas.delete("temp_rect")
        self.start_x = self.start_y = 0


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
            'rectangle': RectangleTool(canvas, sketching_stage)
        }
        
        self.current_tool = None
        self.tool_buttons = {}
        
        # Create tool buttons
        self._create_tool_buttons()
        
        # Start with select tool
        self.set_active_tool('select')
        
    def _create_tool_buttons(self):
        """Create buttons for each tool."""
        btn_width = 10
        
        # Select tool button
        self.tool_buttons['select'] = tk.Button(
            self.tools_frame,
            text="Select",
            width=btn_width,
            command=lambda: self.set_active_tool('select')
        )
        self.tool_buttons['select'].pack(side=tk.LEFT, padx=2, pady=5)
        
        # Line tool button
        self.tool_buttons['line'] = tk.Button(
            self.tools_frame,
            text="Line",
            width=btn_width,
            command=lambda: self.set_active_tool('line')
        )
        self.tool_buttons['line'].pack(side=tk.LEFT, padx=2, pady=5)
        
        # Rectangle tool button
        self.tool_buttons['rectangle'] = tk.Button(
            self.tools_frame,
            text="Rectangle",
            width=btn_width,
            command=lambda: self.set_active_tool('rectangle')
        )
        self.tool_buttons['rectangle'].pack(side=tk.LEFT, padx=2, pady=5)
        
        # Clear button
        clear_btn = tk.Button(
            self.tools_frame,
            text="Clear",
            width=btn_width,
            command=self.sketching_stage.clear_canvas
        )
        clear_btn.pack(side=tk.LEFT, padx=2, pady=5)
        
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
                button.config(relief=tk.SUNKEN, bg="#d0d0d0")
            else:
                button.config(relief=tk.RAISED, bg=button.master.cget('bg'))
                
    def get_current_tool(self):
        """Get the currently active tool.
        
        Returns:
            DrawingTool: The currently active tool, or None
        """
        return self.current_tool
