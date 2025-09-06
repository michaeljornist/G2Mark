# G2burn - Laser Engraving Application

A modern, object-oriented laser engraving application built with Python and Tkinter. This application provides an intuitive interface for creating designs and generating G-Code for GRBL-based laser engravers.

## Features

- **Modern OOP Architecture**: Clean, maintainable code structure with proper separation of concerns
- **Intuitive Drawing Tools**: Line and rectangle drawing tools with real-time preview
- **Line Editing**: Edit length and angle of lines numerically while drawing
- **Snap-to-Point**: Precisely align drawings by snapping to existing points
- **Precise Workspace**: Millimeter-accurate workspace with grid and rulers
- **G-Code Generation**: Export your designs as G-Code for laser engraving
- **GRBL Support**: Direct communication with GRBL-based laser controllers
- **Image Processing**: Convert images to engraving matrices
- **Zoom and Pan**: Navigate large designs with smooth zoom and pan controls

## Project Structure

```
G2burn/
├── project.py              # Main Project class (entry point)
├── sketching_stage.py      # SketchingStage class (workspace management)
├── drawing_tools.py        # Drawing tools (Line, Rectangle, Select)
├── gcode_generator.py      # G-Code generation
├── grbl_controller.py      # GRBL communication
├── image_processor.py      # Image processing for engraving
├── utils.py                # Utility functions and constants
├── setup.py                # Setup and installation script
├── requirements.txt        # Python package dependencies
├── README.md               # This file
├── SNAP_FEATURE.md         # Documentation for snap-to-point feature
├── LINE_EDITING_FEATURE.md # Documentation for line editing feature
├── main.py                 # Legacy code (preserved for reference)
└── legacy/                 # Legacy files and utilities
    └── other/              # Original utility scripts
        ├── read.py         # GRBL settings reader
        ├── run.py          # Direct GRBL command execution
        └── tests.py        # Image processing tests
```

## Class Architecture

### Core Classes

1. **Project** - Main application controller
   - Manages application lifecycle
   - Handles project creation and settings
   - Coordinates between components

2. **SketchingStage** - Drawing workspace manager
   - Manages the drawing canvas and work area
   - Handles zoom, pan, and view controls
   - Coordinates drawing operations

3. **DrawingToolManager** - Tool management system
   - Manages different drawing tools (Select, Line, Rectangle)
   - Handles tool switching and state management
   - Provides extensible architecture for new tools

4. **GCodeGenerator** - G-Code creation and export
   - Converts drawing objects to G-Code
   - Provides syntax highlighting and preview
   - Supports multiple export formats

5. **GRBLController** - Hardware communication
   - Manages serial communication with GRBL controllers
   - Provides status monitoring and command execution
   - Handles emergency stops and safety features

6. **ImageProcessor** - Image processing utilities
   - Converts images to engraving matrices
   - Generates test patterns
   - Provides image analysis tools

## Getting Started

### Prerequisites

- Python 3.7 or higher
- Required packages:
  ```bash
  pip install pillow numpy pyserial
  ```

### Running the Application

1. **New OOP Version** (Recommended):
   ```bash
   python project.py
   ```

2. **Legacy Version** (For reference):
   ```bash
   python main.py
   ```

### Basic Usage

1. **Create a New Project**:
   - Click "New Project"
   - Enter project name and dimensions (in mm)
   - Click "Create Project"

2. **Drawing**:
   - Select a drawing tool (Line, Rectangle)
   - Click in the white work area to draw
   - Use the status bar to track coordinates

3. **View Controls**:
   - Zoom: Mouse wheel or Zoom In/Out buttons
   - Pan: Middle mouse button drag
   - Reset: Reset View button

4. **Generate G-Code**:
   - Click "G-Code" button
   - Review generated code
   - Save or copy to clipboard

## Key Improvements in the Refactor

### 1. Object-Oriented Design
- **Before**: Monolithic script with global variables
- **After**: Clean class hierarchy with proper encapsulation

### 2. Consistent Naming Convention
- **Before**: Mixed naming styles (`open_engraving_workspace`, `draw_work_area`)
- **After**: Consistent PascalCase for classes, snake_case for methods

### 3. Separation of Concerns
- **Before**: All functionality in one 900+ line file
- **After**: Logical separation into focused modules

### 4. Improved Maintainability
- **Before**: Difficult to modify or extend
- **After**: Modular design allows easy addition of new features

### 5. Better Error Handling
- **Before**: Basic error handling
- **After**: Comprehensive error handling with user feedback

### 6. Enhanced Documentation
- **Before**: Minimal comments
- **After**: Full docstrings and type hints

## Architecture Benefits

### Extensibility
- Easy to add new drawing tools by inheriting from `DrawingTool`
- Simple to add new export formats in `GCodeGenerator`
- Straightforward to add new image processing features

### Testability
- Each class can be unit tested independently
- Clear interfaces make mocking easy
- Separation of concerns enables focused testing

### Maintainability
- Clear responsibility boundaries
- Consistent coding patterns
- Comprehensive documentation

## Configuration

### GRBL Settings
Modify `grbl_controller.py` to adjust:
- Serial port (default: `/dev/tty.wchusbserial1130`)
- Baud rate (default: `115200`)
- Communication timeouts

### Default Values
Modify `utils.py` Constants class to adjust:
- Default feed rates and laser power
- UI dimensions and colors
- File extensions

## Development

### Adding New Drawing Tools

1. Create a new class inheriting from `DrawingTool`:
   ```python
   class CircleTool(DrawingTool):
       def activate(self):
           # Implementation
       
       def deactivate(self):
           # Implementation
   ```

2. Register the tool in `DrawingToolManager.__init__()`:
   ```python
   self.tools['circle'] = CircleTool(canvas, sketching_stage)
   ```

3. Add a button in `_create_tool_buttons()`:
   ```python
   self.tool_buttons['circle'] = tk.Button(...)
   ```

### Adding New Export Formats

1. Add methods to `GCodeGenerator`:
   ```python
   def export_to_svg(self):
       # SVG export implementation
   ```

2. Update the export menu in `SketchingStage`

## License

This project is open source. See the license file for details.

## Contributing

1. Follow the existing code style and naming conventions
2. Add comprehensive docstrings to new functions and classes
3. Include type hints where appropriate
4. Test your changes thoroughly
5. Update documentation as needed

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all files are in the same directory
2. **Serial Communication**: Check your GRBL device port and permissions
3. **Image Processing**: Verify Pillow installation for image features

### Debug Mode

Enable debug logging by modifying `utils.py`:
```python
logger.set_enabled(True)
```

## Future Enhancements

- [ ] Circle and arc drawing tools
- [ ] Text tool with font support
- [ ] Layer management
- [ ] Undo/redo functionality
- [ ] Advanced image processing options
- [ ] 3D preview capabilities
- [ ] Cloud project storage
- [ ] Plugin system for custom tools
