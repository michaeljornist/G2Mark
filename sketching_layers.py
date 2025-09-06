"""
Sketching Layers manager for the G2burn Laser Engraving Application.
This module manages layers for organizing drawing objects.
"""

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox


class SketchingLayer:
    """Represents a single drawing layer."""
    
    def __init__(self, layer_id, name, visible=True):
        """Initialize a layer.
        
        Args:
            layer_id (int): Unique identifier for the layer
            name (str): Name of the layer
            visible (bool): Whether the layer is visible
        """
        self.id = layer_id
        self.name = name
        self.visible = visible
        self.locked = False  # Future feature for locking layers
        self.color = "#000000"  # Default color for layer objects
        
    def __repr__(self):
        """String representation of the layer."""
        return f"Layer(id={self.id}, name='{self.name}', visible={self.visible})"


class SketchingLayers:
    """Manages all drawing layers and the layers panel UI."""
    
    def __init__(self, parent_frame, sketching_stage):
        """Initialize the layers manager.
        
        Args:
            parent_frame (tk.Frame): Parent frame for the layers panel
            sketching_stage (SketchingStage): Reference to the main sketching stage
        """
        self.sketching_stage = sketching_stage
        self.layers = []
        self.current_layer_id = 1
        self.active_layer_id = 1
        self.layer_counter = 0
        
        # UI components
        self.layers_frame = None
        self.layers_listbox = None
        self.layer_checkboxes = {}
        self.layer_vars = {}
        
        # Create the first default layer
        self._create_default_layer()
        
        # Create the layers panel UI
        self.create_layers_panel(parent_frame)
        
    def _create_default_layer(self):
        """Create the initial default layer."""
        self.layer_counter += 1
        default_layer = SketchingLayer(
            layer_id=self.layer_counter,
            name="Layer1",
            visible=True
        )
        self.layers.append(default_layer)
        self.current_layer_id = default_layer.id
        self.active_layer_id = default_layer.id
        
    def create_layers_panel(self, parent_frame):
        """Create the layers panel UI.
        
        Args:
            parent_frame (tk.Frame): Parent frame to contain the layers panel
        """
        # Store reference to parent frame for resizing
        self.parent_frame = parent_frame
        
        # Panel state (compact or expanded)
        self.is_expanded = False
        self.compact_width = 150
        self.expanded_width = 250
        
        # Header frame with title and toggle button
        header_frame = tk.Frame(parent_frame, bg="#e0e0e0")
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Title label
        title_label = tk.Label(
            header_frame,
            text="Layers",
            font=("Arial", 10, "bold"),
            bg="#e0e0e0"
        )
        title_label.pack(side=tk.LEFT)
        
        # Toggle button (compact/expand)
        self.toggle_button = tk.Button(
            header_frame,
            text=">>",
            font=("Arial", 8),
            width=3,
            command=self._toggle_panel_size,
            bg="#d0d0d0"
        )
        self.toggle_button.pack(side=tk.RIGHT)
        
        # Main layers frame
        self.layers_frame = tk.LabelFrame(
            parent_frame,
            text="Layers",
            font=("Arial", 10, "bold"),
            padx=5,
            pady=5
        )
        self.layers_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Layers list frame
        list_frame = tk.Frame(self.layers_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollable frame for layers
        canvas = tk.Canvas(list_frame, height=200)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Buttons frame
        self.buttons_frame = tk.Frame(self.layers_frame)
        self.buttons_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Create buttons and store references
        self.add_button = tk.Button(
            self.buttons_frame,
            text="+ Add" if not self.is_expanded else "+ Add Layer",
            command=self.add_new_layer,
            font=("Arial", 9)
        )
        
        self.delete_button = tk.Button(
            self.buttons_frame,
            text="Del" if not self.is_expanded else "Delete",
            command=self.delete_current_layer,
            font=("Arial", 9)
        )
        
        self.rename_button = tk.Button(
            self.buttons_frame,
            text="Ren" if not self.is_expanded else "Rename",
            command=self.rename_current_layer,
            font=("Arial", 9)
        )
        
        # Layout buttons based on current mode
        self._layout_buttons()
        
        # Update the display
        self._update_layers_display()
    
    def _layout_buttons(self):
        """Layout buttons based on current panel mode (compact or expanded)."""
        # Clear current layout
        for widget in self.buttons_frame.winfo_children():
            widget.pack_forget()
        
        if self.is_expanded:
            # Horizontal layout for expanded mode
            self.add_button.config(text="+ Add Layer")
            self.delete_button.config(text="Delete")
            self.rename_button.config(text="Rename")
            
            self.add_button.pack(side=tk.LEFT, padx=(0, 5))
            self.delete_button.pack(side=tk.LEFT, padx=(0, 5))
            self.rename_button.pack(side=tk.LEFT)
        else:
            # Vertical layout for compact mode
            self.add_button.config(text="+ Add")
            self.delete_button.config(text="Del")
            self.rename_button.config(text="Ren")
            
            self.add_button.pack(fill=tk.X, pady=(0, 2))
            self.delete_button.pack(fill=tk.X, pady=(0, 2))
            self.rename_button.pack(fill=tk.X)
    
    def _toggle_panel_size(self):
        """Toggle between compact and expanded panel modes."""
        self.is_expanded = not self.is_expanded
        
        # Update panel width
        new_width = self.expanded_width if self.is_expanded else self.compact_width
        self.parent_frame.config(width=new_width)
        
        # Update toggle button text
        self.toggle_button.config(text="<<" if self.is_expanded else ">>")
        
        # Update button layout
        self._layout_buttons()
        
        # Update layers display to fit new width
        self._update_layers_display()
        
    def _update_layers_display(self):
        """Update the layers display in the UI."""
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.layer_checkboxes = {}
        self.layer_vars = {}
        
        # Create widgets for each layer
        for i, layer in enumerate(reversed(self.layers)):  # Show newest layers at top
            layer_frame = tk.Frame(self.scrollable_frame)
            layer_frame.pack(fill=tk.X, pady=1)
            
            # Visibility checkbox
            var = tk.BooleanVar(value=layer.visible)
            self.layer_vars[layer.id] = var
            
            checkbox = tk.Checkbutton(
                layer_frame,
                variable=var,
                command=lambda lid=layer.id: self._toggle_layer_visibility(lid)
            )
            checkbox.pack(side=tk.LEFT)
            self.layer_checkboxes[layer.id] = checkbox
            
            # Layer name label (clickable for editing)
            # Truncate name in compact mode
            display_name = layer.name
            if not self.is_expanded and len(layer.name) > 8:
                display_name = layer.name[:8] + "..."
            
            name_label = tk.Label(
                layer_frame,
                text=display_name,
                anchor="w",
                relief="flat" if layer.id != self.active_layer_id else "sunken",
                bg="white" if layer.id != self.active_layer_id else "#d0d0d0",
                font=("Arial", 9),
                cursor="hand2"
            )
            name_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
            
            # Store label reference for this layer
            if not hasattr(self, 'layer_labels'):
                self.layer_labels = {}
            self.layer_labels[layer.id] = name_label
            
            # Simple click bindings
            name_label.bind("<Button-1>", lambda e, lid=layer.id: self._set_active_layer(lid))
            
            # Right-click context menu
            def show_context_menu(event):
                context_menu = tk.Menu(self.layers_frame, tearoff=0)
                context_menu.add_command(
                    label="Rename Layer", 
                    command=lambda: self._start_rename_layer(layer.id, name_label)
                )
                if len(self.layers) > 1:  # Only show delete if not the last layer
                    context_menu.add_command(
                        label="Delete Layer", 
                        command=lambda: self._delete_layer(layer.id)
                    )
                try:
                    context_menu.tk_popup(event.x_root, event.y_root)
                finally:
                    context_menu.grab_release()
            
            name_label.bind("<Button-3>", show_context_menu)  # Right click
            
            # Object count label (only show in expanded mode)
            if self.is_expanded:
                object_count = self._count_objects_in_layer(layer.id)
                count_label = tk.Label(
                    layer_frame,
                    text=f"({object_count})",
                    font=("Arial", 8),
                    fg="gray"
                )
                count_label.pack(side=tk.RIGHT, padx=(5, 0))
            
    def _toggle_layer_visibility(self, layer_id):
        """Toggle the visibility of a layer.
        
        Args:
            layer_id (int): ID of the layer to toggle
        """
        layer = self.get_layer_by_id(layer_id)
        if layer:
            layer.visible = self.layer_vars[layer_id].get()
            # Trigger redraw to show/hide objects
            self.sketching_stage._redraw_all()
            
    def _set_active_layer(self, layer_id):
        """Set the active layer for new drawings.
        
        Args:
            layer_id (int): ID of the layer to make active
        """
        self.active_layer_id = layer_id
        self.current_layer_id = layer_id
        self._update_layers_display()
        
        # Update status
        layer = self.get_layer_by_id(layer_id)
        if layer:
            status_text = f"Active Layer: {layer.name}"
            if hasattr(self.sketching_stage, 'status_var'):
                current_status = self.sketching_stage.status_var.get()
                if " | " in current_status:
                    tool_status = current_status.split(" | ")[0]
                    self.sketching_stage.status_var.set(f"{tool_status} | {status_text}")
                else:
                    self.sketching_stage.status_var.set(f"{current_status} | {status_text}")
                    
    def add_new_layer(self):
        """Add a new layer."""
        self.layer_counter += 1
        new_layer_name = f"Layer{self.layer_counter}"
        
        new_layer = SketchingLayer(
            layer_id=self.layer_counter,
            name=new_layer_name,
            visible=True
        )
        
        self.layers.append(new_layer)
        self._set_active_layer(new_layer.id)
        self._update_layers_display()
        
    def delete_current_layer(self):
        """Delete the currently active layer."""
        if len(self.layers) <= 1:
            messagebox.showwarning("Cannot Delete", "Cannot delete the last layer.")
            return
            
        # Confirm deletion
        layer = self.get_layer_by_id(self.active_layer_id)
        object_count = self._count_objects_in_layer(self.active_layer_id)
        
        if object_count > 0:
            response = messagebox.askyesno(
                "Delete Layer",
                f"Layer '{layer.name}' contains {object_count} objects.\nAre you sure you want to delete it?"
            )
            if not response:
                return
                
        # Remove layer and its objects
        self.layers = [l for l in self.layers if l.id != self.active_layer_id]
        self._remove_objects_from_layer(self.active_layer_id)
        
        # Set new active layer (first available layer)
        if self.layers:
            self._set_active_layer(self.layers[0].id)
            
        self._update_layers_display()
        self.sketching_stage._redraw_all()
        
    def rename_current_layer(self):
        """Rename the currently active layer using inline editing if possible."""
        layer = self.get_layer_by_id(self.active_layer_id)
        if not layer:
            return
        
        # Try to use inline editing if we have the label widget
        if hasattr(self, 'layer_labels') and self.active_layer_id in self.layer_labels:
            label_widget = self.layer_labels[self.active_layer_id]
            self._start_rename_layer(self.active_layer_id, label_widget)
        else:
            # Fallback to dialog
            new_name = simpledialog.askstring(
                "Rename Layer",
                f"Enter new name for '{layer.name}':",
                initialvalue=layer.name
            )
            
            if new_name and new_name.strip():
                layer.name = new_name.strip()
                self._update_layers_display()
    
    def _start_rename_layer(self, layer_id, label_widget):
        """Start inline renaming of a layer.
        
        Args:
            layer_id (int): ID of the layer to rename
            label_widget (tk.Label): The label widget to replace with entry
        """
        layer = self.get_layer_by_id(layer_id)
        if not layer:
            return
        
        # Get the parent frame and position info
        parent = label_widget.master
        pack_info = label_widget.pack_info()
        
        # Create entry widget for editing
        entry = tk.Entry(
            parent,
            font=("Arial", 9),
            relief="solid",
            borderwidth=2,
            highlightthickness=0,
            bg="white"
        )
        
        # Set current name and select all text
        entry.insert(0, layer.name)
        entry.select_range(0, tk.END)
        
        # Replace label with entry
        label_widget.pack_forget()
        entry.pack(**pack_info)
        entry.focus_set()
        
        def finish_rename(event=None):
            """Finish the rename operation."""
            new_name = entry.get().strip()
            if new_name and new_name != layer.name:
                layer.name = new_name
            
            # Restore the display
            entry.destroy()
            self._update_layers_display()
        
        def cancel_rename(event=None):
            """Cancel the rename operation."""
            entry.destroy()
            self._update_layers_display()
        
        # Bind events
        entry.bind("<Return>", finish_rename)
        entry.bind("<KP_Enter>", finish_rename)  # Keypad Enter
        entry.bind("<Escape>", cancel_rename)
        entry.bind("<FocusOut>", finish_rename)
    
    def _delete_layer(self, layer_id):
        """Delete a specific layer by ID."""
        if len(self.layers) <= 1:
            messagebox.showwarning("Cannot Delete", "Cannot delete the last layer.")
            return
        
        # Set this layer as active first, then use existing delete method
        self._set_active_layer(layer_id)
        self.delete_current_layer()
            
    def get_layer_by_id(self, layer_id):
        """Get a layer by its ID.
        
        Args:
            layer_id (int): ID of the layer to find
            
        Returns:
            SketchingLayer: The layer object, or None if not found
        """
        for layer in self.layers:
            if layer.id == layer_id:
                return layer
        return None
        
    def get_active_layer(self):
        """Get the currently active layer.
        
        Returns:
            SketchingLayer: The active layer object
        """
        return self.get_layer_by_id(self.active_layer_id)
        
    def is_layer_visible(self, layer_id):
        """Check if a layer is visible.
        
        Args:
            layer_id (int): ID of the layer to check
            
        Returns:
            bool: True if layer is visible, False otherwise
        """
        layer = self.get_layer_by_id(layer_id)
        return layer.visible if layer else False
        
    def _count_objects_in_layer(self, layer_id):
        """Count objects in a specific layer.
        
        Args:
            layer_id (int): ID of the layer to count objects for
            
        Returns:
            int: Number of objects in the layer
        """
        count = 0
        for obj in self.sketching_stage.drawing_objects:
            if obj.get('layer_id') == layer_id:
                count += 1
        return count
        
    def _remove_objects_from_layer(self, layer_id):
        """Remove all objects from a specific layer.
        
        Args:
            layer_id (int): ID of the layer to clear
        """
        self.sketching_stage.drawing_objects = [
            obj for obj in self.sketching_stage.drawing_objects 
            if obj.get('layer_id') != layer_id
        ]
        
    def get_current_layer_id(self):
        """Get the ID of the current active layer.
        
        Returns:
            int: ID of the active layer
        """
        return self.active_layer_id
    
    def get_active_layer_id(self):
        """Get the ID of the current active layer.
        
        Returns:
            int: ID of the active layer
        """
        return self.active_layer_id
    
    def refresh_layer_objects(self):
        """Refresh the layer display to show current object counts."""
        if self.layers_frame:
            self._update_layers_display()
