"""
Main Project class for the G2burn Laser Engraving Application.
This class manages the overall application state and coordinates between components.
"""

import tkinter as tk
from tkinter import messagebox
from sketching_stage import SketchingStage


class Project:
    """Main application controller for the laser engraving project."""
    
    def __init__(self):
        """Initialize the project with default settings."""
        self.root = None
        self.settings_window = None
        self.current_sketching_stage = None
        
        # Project properties
        self.name = ""
        self.height_mm = 0.0
        self.length_mm = 0.0
        
        # UI components for new project dialog
        self.name_entry = None
        self.height_entry = None
        self.length_entry = None
        
    def run(self):
        """Start the main application."""
        self.root = tk.Tk()
        self.root.title("G2burn - Laser Engraving Application")
        self.root.geometry("400x200")
        
        # Center the main window
        self._center_window(self.root, 400, 200)
        
        # Create main interface
        self._create_main_interface()
        
        # Start the main loop
        self.root.mainloop()
        
    def _center_window(self, window, width, height):
        """Center a window on the screen."""
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")
        
    def _create_main_interface(self):
        """Create the main application interface."""
        # Main frame
        main_frame = tk.Frame(self.root, padx=50, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(
            main_frame, 
            text="G2burn Laser Engraver", 
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # New project button
        new_project_btn = tk.Button(
            main_frame,
            text="New Project",
            command=self.open_new_project_dialog,
            font=("Arial", 12),
            padx=20,
            pady=10
        )
        new_project_btn.pack(pady=10)
        
        # Load project button (for future implementation)
        load_project_btn = tk.Button(
            main_frame,
            text="Load Project",
            command=self._show_not_implemented,
            font=("Arial", 12),
            padx=20,
            pady=10,
            state=tk.DISABLED
        )
        load_project_btn.pack(pady=10)
        
    def _show_not_implemented(self):
        """Show a message for features not yet implemented."""
        messagebox.showinfo("Feature Not Available", "This feature will be implemented in a future version.")
        
    def open_new_project_dialog(self):
        """Open the new project settings dialog."""
        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("New Project Settings")
        self.settings_window.geometry("350x200")
        self._center_window(self.settings_window, 350, 200)
        
        # Make dialog modal
        self.settings_window.transient(self.root)
        self.settings_window.grab_set()
        
        # Create form
        self._create_project_form()
        
    def _create_project_form(self):
        """Create the project settings form."""
        form_frame = tk.Frame(self.settings_window, padx=20, pady=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Project name
        tk.Label(form_frame, text="Project Name:", font=("Arial", 10)).grid(
            row=0, column=0, sticky="w", pady=5
        )
        self.name_entry = tk.Entry(form_frame, width=25, font=("Arial", 10))
        self.name_entry.grid(row=0, column=1, padx=(10, 0), pady=5)
        self.name_entry.focus()
        
        # Height
        tk.Label(form_frame, text="Height (mm):", font=("Arial", 10)).grid(
            row=1, column=0, sticky="w", pady=5
        )
        self.height_entry = tk.Entry(form_frame, width=25, font=("Arial", 10))
        self.height_entry.grid(row=1, column=1, padx=(10, 0), pady=5)
        
        # Length
        tk.Label(form_frame, text="Length (mm):", font=("Arial", 10)).grid(
            row=2, column=0, sticky="w", pady=5
        )
        self.length_entry = tk.Entry(form_frame, width=25, font=("Arial", 10))
        self.length_entry.grid(row=2, column=1, padx=(10, 0), pady=5)
        
        # Buttons frame
        button_frame = tk.Frame(form_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        # Create button
        create_btn = tk.Button(
            button_frame,
            text="Create Project",
            command=self.create_project,
            font=("Arial", 10),
            padx=15,
            pady=5
        )
        create_btn.pack(side=tk.LEFT, padx=5)
        
        # Cancel button
        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            command=self.settings_window.destroy,
            font=("Arial", 10),
            padx=15,
            pady=5
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key to create project
        self.settings_window.bind('<Return>', lambda e: self.create_project())
        
    def create_project(self):
        """Create a new project with the specified settings."""
        # Get form values
        name = self.name_entry.get().strip()
        height_str = self.height_entry.get().strip()
        length_str = self.length_entry.get().strip()
        
        # Validate input
        if not name:
            messagebox.showwarning("Invalid Input", "Please enter a project name.")
            self.name_entry.focus()
            return
            
        if not height_str or not length_str:
            messagebox.showwarning("Invalid Input", "Please fill in all dimensions.")
            return
        
        try:
            height = float(height_str)
            length = float(length_str)
            
            if height <= 0 or length <= 0:
                raise ValueError("Dimensions must be positive")
                
        except ValueError:
            messagebox.showerror(
                "Invalid Input", 
                "Height and Length must be positive numeric values."
            )
            return
        
        # Store project settings
        self.name = name
        self.height_mm = height
        self.length_mm = length
        
        # Close settings dialog
        self.settings_window.destroy()
        
        # Open the sketching stage
        self._open_sketching_stage()
        
    def _open_sketching_stage(self):
        """Open the sketching stage workspace."""
        try:
            self.current_sketching_stage = SketchingStage(
                project_name=self.name,
                height_mm=self.height_mm,
                length_mm=self.length_mm,
                parent_window=self.root
            )
            self.current_sketching_stage.show()
            
        except Exception as e:
            messagebox.showerror(
                "Error", 
                f"Failed to open sketching stage: {str(e)}"
            )
            
    def get_project_info(self):
        """Get current project information."""
        return {
            'name': self.name,
            'height_mm': self.height_mm,
            'length_mm': self.length_mm
        }
        
    def close_sketching_stage(self):
        """Close the current sketching stage."""
        if self.current_sketching_stage:
            self.current_sketching_stage.close()
            self.current_sketching_stage = None


if __name__ == "__main__":
    app = Project()
    app.run()
