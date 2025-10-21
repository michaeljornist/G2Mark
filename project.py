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
        self.root.geometry("800x600")  # Much bigger window
        
        # Center the main window
        self._center_window(self.root, 800, 600)
        
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
        """Create the modern main application interface with icons."""
        # Set background color
        self.root.configure(bg="#1a1a1a")
        
        # Main container
        main_frame = tk.Frame(self.root, bg="#1a1a1a", padx=40, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header section
        header_frame = tk.Frame(main_frame, bg="#1a1a1a")
        header_frame.pack(fill=tk.X, pady=(0, 40))
        
        # Title
        title_label = tk.Label(
            header_frame, 
            text="G2burn Laser Engraver", 
            font=("Helvetica Neue", 28, "bold"),
            bg="#1a1a1a",
            fg="#ffffff"
        )
        title_label.pack()
        
        # Subtitle
        subtitle_label = tk.Label(
            header_frame, 
            text="Professional Laser Engraving Design & Control", 
            font=("Helvetica Neue", 14),
            bg="#1a1a1a",
            fg="#8e8e93"
        )
        subtitle_label.pack(pady=(8, 0))
        
        # Main content area with cards
        content_frame = tk.Frame(main_frame, bg="#1a1a1a")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights for responsive layout
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_rowconfigure(1, weight=1)
        
        # New Project Card
        self._create_action_card(
            content_frame, 
            "🆕 New Project", 
            "Create a new laser engraving design",
            self.open_new_project_dialog,
            row=0, column=0
        )
        
        # Load Project Card
        self._create_action_card(
            content_frame, 
            "📂 Load Project", 
            "Open an existing project file",
            self._show_load_project,
            row=0, column=1
        )
        
        # My Machines Card
        self._create_action_card(
            content_frame, 
            "⚙️ My Machines", 
            "Manage your laser engraving machines",
            self._show_machines_manager,
            row=1, column=0
        )
        
        # Settings Card
        self._create_action_card(
            content_frame, 
            "🔧 Settings", 
            "Configure application preferences",
            self._show_app_settings,
            row=1, column=1
        )
        
    def _create_action_card(self, parent, title, description, command, row, column):
        """Create a modern action card with icon and description."""
        # Card frame with modern dark styling
        card_frame = tk.Frame(
            parent, 
            bg="#2a2a2a", 
            relief=tk.FLAT, 
            bd=0
        )
        card_frame.grid(
            row=row, column=column, 
            padx=15, pady=15, 
            sticky="nsew",
            ipadx=25, ipady=25
        )
        
        # Add subtle border effect
        border_frame = tk.Frame(card_frame, bg="#404040", height=1)
        border_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Make card clickable with hover effects
        def on_enter(e):
            card_frame.configure(bg="#3a3a3a")
            border_frame.configure(bg="#007AFF")
            title_label.configure(bg="#3a3a3a")
            desc_label.configure(bg="#3a3a3a")
        
        def on_leave(e):
            card_frame.configure(bg="#2a2a2a")
            border_frame.configure(bg="#404040")
            title_label.configure(bg="#2a2a2a")
            desc_label.configure(bg="#2a2a2a")
        
        def on_click(e):
            command()
        
        card_frame.bind("<Button-1>", on_click)
        card_frame.bind("<Enter>", on_enter)
        card_frame.bind("<Leave>", on_leave)
        
        # Title with icon
        title_label = tk.Label(
            card_frame,
            text=title,
            font=("Helvetica Neue", 18, "bold"),
            bg="#2a2a2a",
            fg="#ffffff",
            cursor="hand2"
        )
        title_label.pack(pady=(15, 8))
        title_label.bind("<Button-1>", on_click)
        title_label.bind("<Enter>", on_enter)
        title_label.bind("<Leave>", on_leave)
        
        # Description
        desc_label = tk.Label(
            card_frame,
            text=description,
            font=("Helvetica Neue", 12),
            bg="#2a2a2a",
            fg="#8e8e93",
            wraplength=200,
            cursor="hand2"
        )
        desc_label.pack(pady=(0, 15))
        desc_label.bind("<Button-1>", on_click)
        desc_label.bind("<Enter>", on_enter)
        desc_label.bind("<Leave>", on_leave)
        
    def _show_load_project(self):
        """Show load project dialog."""
        from tkinter import filedialog
        
        file_path = filedialog.askopenfilename(
            title="Load G2burn Project",
            defaultextension=".g2burn",
            filetypes=[
                ("G2burn Projects", "*.g2burn"),
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            # TODO: Implement project loading
            messagebox.showinfo("Load Project", f"Loading project: {file_path}\n(Feature coming soon!)")
    
    def _show_machines_manager(self):
        """Show the machines manager window."""
        machines_window = tk.Toplevel(self.root)
        machines_window.title("My Machines - G2burn")
        machines_window.geometry("700x500")
        self._center_window(machines_window, 700, 500)
        machines_window.configure(bg="#1a1a1a")
        
        # Load machines data
        machines_data = self._load_machines_data()
        
        # Create machines interface
        self._create_machines_interface(machines_window, machines_data)
        
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
    
    def _create_machines_interface(self, window, machines_data):
        """Create the machines management interface."""
        # Main frame
        main_frame = tk.Frame(window, bg="#1a1a1a", padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = tk.Frame(main_frame, bg="#1a1a1a")
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = tk.Label(
            header_frame,
            text="My Machines",
            font=("Helvetica Neue", 22, "bold"),
            bg="#1a1a1a",
            fg="#ffffff"
        )
        title_label.pack(side=tk.LEFT)
        
        # Add new machine button using Label for better styling control
        add_btn = tk.Label(
            header_frame,
            text="+ Add New Machine",
            font=("Arial", 11, "bold"),
            bg="#007AFF",
            fg="#FFFFFF",
            padx=20,
            pady=8,
            cursor="hand2"
        )
        add_btn.pack(side=tk.RIGHT)
        add_btn.bind("<Button-1>", lambda e: self._show_add_machine_dialog())
        add_btn.bind("<Enter>", lambda e: add_btn.configure(bg="#0056CC"))
        add_btn.bind("<Leave>", lambda e: add_btn.configure(bg="#007AFF"))
        
        # Machines list frame with scrollbar
        list_frame = tk.Frame(main_frame, bg="#1a1a1a")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollable frame
        canvas = tk.Canvas(list_frame, bg="#1a1a1a", highlightthickness=0)
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=canvas.yview, 
                                bg="#1a1a1a", troughcolor="#1a1a1a", activebackground="#404040",
                                highlightthickness=0, borderwidth=0)
        scrollable_frame = tk.Frame(canvas, bg="#1a1a1a")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Display machines
        for i, machine in enumerate(machines_data.get("machines", [])):
            self._create_machine_card(scrollable_frame, machine, i)
        
        # Pack scrollable components - only show scrollbar when needed
        canvas.pack(side="left", fill="both", expand=True)
        # Only pack scrollbar if content exceeds window height
        def on_canvas_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Check if scrolling is needed
            canvas_height = canvas.winfo_height()
            content_height = canvas.bbox("all")[3] if canvas.bbox("all") else 0
            if content_height > canvas_height:
                scrollbar.pack(side="right", fill="y")
            else:
                scrollbar.pack_forget()
        
        scrollable_frame.bind("<Configure>", on_canvas_configure)
        
    def _create_machine_card(self, parent, machine, index):
        """Create a card for each machine."""
        # Card frame with modern dark styling
        card_frame = tk.Frame(
            parent,
            bg="#2a2a2a",
            relief=tk.FLAT,
            bd=0
        )
        card_frame.pack(fill=tk.X, pady=8, padx=5, ipady=20, ipadx=20)
        
        # Add subtle border effect
        border_frame = tk.Frame(card_frame, bg="#404040", height=1)
        border_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Machine info frame
        info_frame = tk.Frame(card_frame, bg="#2a2a2a")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Left side - Machine details
        left_frame = tk.Frame(info_frame, bg="#2a2a2a")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Machine name
        name_label = tk.Label(
            left_frame,
            text=machine.get("name", "Unknown Machine"),
            font=("Helvetica Neue", 16, "bold"),
            bg="#2a2a2a",
            fg="#ffffff"
        )
        name_label.pack(anchor=tk.W)
        
        # Machine type
        type_label = tk.Label(
            left_frame,
            text=f"Type: {machine.get('type', 'Unknown')}",
            font=("Helvetica Neue", 11),
            bg="#2a2a2a",
            fg="#8e8e93"
        )
        type_label.pack(anchor=tk.W, pady=(4, 0))
        
        # Work area
        work_area = machine.get("work_area", {})
        area_text = f"Work Area: {work_area.get('width_mm', 0)}×{work_area.get('height_mm', 0)}mm"
        area_label = tk.Label(
            left_frame,
            text=area_text,
            font=("Helvetica Neue", 11),
            bg="#2a2a2a",
            fg="#8e8e93"
        )
        area_label.pack(anchor=tk.W, pady=(2, 0))
        
        # Connection info
        connection = machine.get("connection", {})
        conn_text = f"Port: {connection.get('port', 'Not set')} @ {connection.get('baud_rate', 0)} baud"
        conn_label = tk.Label(
            left_frame,
            text=conn_text,
            font=("Helvetica Neue", 10),
            bg="#2a2a2a",
            fg="#636366"
        )
        conn_label.pack(anchor=tk.W, pady=(2, 0))
        
        # Right side - Status and actions
        right_frame = tk.Frame(info_frame, bg="#2a2a2a")
        right_frame.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Status indicator
        status = machine.get("status", "unknown")
        status_color = "#30D158" if status == "connected" else "#FF453A"
        status_label = tk.Label(
            right_frame,
            text=f"● {status.title()}",
            font=("Helvetica Neue", 11, "bold"),
            bg="#2a2a2a",
            fg=status_color
        )
        status_label.pack(anchor=tk.E, pady=(0, 8))
        
        # Action buttons using Labels for better styling control
        btn_frame = tk.Frame(right_frame, bg="#2a2a2a")
        btn_frame.pack()
        
        # Profiles button as styled label
        profiles_btn = tk.Label(
            btn_frame,
            text="Profiles",
            font=("Arial", 10, "bold"),
            bg="#34C759",
            fg="#FFFFFF",
            padx=12,
            pady=6,
            cursor="hand2"
        )
        profiles_btn.pack(side=tk.RIGHT, padx=(8, 0))
        profiles_btn.bind("<Button-1>", lambda e: self._show_machine_profiles(machine))
        profiles_btn.bind("<Enter>", lambda e: profiles_btn.configure(bg="#28A745"))
        profiles_btn.bind("<Leave>", lambda e: profiles_btn.configure(bg="#34C759"))
        
        # Edit button as styled label
        edit_btn = tk.Label(
            btn_frame,
            text="Edit",
            font=("Arial", 10, "bold"),
            bg="#007AFF",
            fg="#FFFFFF",
            padx=15,
            pady=6,
            cursor="hand2"
        )
        edit_btn.pack(side=tk.RIGHT, padx=(8, 0))
        edit_btn.bind("<Button-1>", lambda e: self._edit_machine(machine))
        edit_btn.bind("<Enter>", lambda e: edit_btn.configure(bg="#0056CC"))
        edit_btn.bind("<Leave>", lambda e: edit_btn.configure(bg="#007AFF"))
        
        # Test button as styled label
        test_btn = tk.Label(
            btn_frame,
            text="Test",
            font=("Arial", 10, "bold"),
            bg="#FF9500",
            fg="#FFFFFF",
            padx=15,
            pady=6,
            cursor="hand2"
        )
        test_btn.pack(side=tk.RIGHT)
        test_btn.bind("<Button-1>", lambda e: self._test_machine(machine))
        test_btn.bind("<Enter>", lambda e: test_btn.configure(bg="#CC7700"))
        test_btn.bind("<Leave>", lambda e: test_btn.configure(bg="#FF9500"))
        
    def _show_machine_profiles(self, machine):
        """Show profiles management window for a specific machine."""
        profiles_window = tk.Toplevel(self.root)
        profiles_window.title(f"Profiles - {machine.get('name', 'Unknown Machine')}")
        profiles_window.geometry("800x600")
        self._center_window(profiles_window, 800, 600)
        profiles_window.configure(bg="#1a1a1a")
        
        # Create profiles interface
        self._create_profiles_interface(profiles_window, machine)
        
    def _create_profiles_interface(self, window, machine):
        """Create the profiles management interface."""
        # Main frame
        main_frame = tk.Frame(window, bg="#1a1a1a", padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = tk.Frame(main_frame, bg="#1a1a1a")
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = tk.Label(
            header_frame,
            text=f"Profiles for {machine.get('name', 'Unknown Machine')}",
            font=("Helvetica Neue", 22, "bold"),
            bg="#1a1a1a",
            fg="#ffffff"
        )
        title_label.pack(side=tk.LEFT)
        
        # Add new profile button
        add_profile_btn = tk.Label(
            header_frame,
            text="+ Add New Profile",
            font=("Arial", 11, "bold"),
            bg="#34C759",
            fg="#FFFFFF",
            padx=20,
            pady=8,
            cursor="hand2"
        )
        add_profile_btn.pack(side=tk.RIGHT)
        add_profile_btn.bind("<Button-1>", lambda e: self._show_add_profile_dialog(machine, window))
        add_profile_btn.bind("<Enter>", lambda e: add_profile_btn.configure(bg="#28A745"))
        add_profile_btn.bind("<Leave>", lambda e: add_profile_btn.configure(bg="#34C759"))
        
        # Profiles list frame with scrollbar
        list_frame = tk.Frame(main_frame, bg="#1a1a1a")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollable frame
        canvas = tk.Canvas(list_frame, bg="#1a1a1a", highlightthickness=0)
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=canvas.yview, 
                                bg="#2a2a2a", troughcolor="#1a1a1a", activebackground="#404040")
        scrollable_frame = tk.Frame(canvas, bg="#1a1a1a")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Display profiles
        profiles = machine.get("profiles", [])
        for i, profile in enumerate(profiles):
            self._create_profile_card(scrollable_frame, profile, machine, window, i)
        
        # Pack scrollable components
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def _create_profile_card(self, parent, profile, machine, profiles_window, index):
        """Create a card for each profile."""
        # Card frame with modern dark styling
        card_frame = tk.Frame(
            parent,
            bg="#2a2a2a",
            relief=tk.FLAT,
            bd=0
        )
        card_frame.pack(fill=tk.X, pady=8, padx=5, ipady=20, ipadx=20)
        
        # Add subtle border effect
        border_frame = tk.Frame(card_frame, bg="#404040", height=1)
        border_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Profile info frame
        info_frame = tk.Frame(card_frame, bg="#2a2a2a")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Left side - Profile details
        left_frame = tk.Frame(info_frame, bg="#2a2a2a")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Profile name
        name_label = tk.Label(
            left_frame,
            text=profile.get("name", "Unknown Profile"),
            font=("Helvetica Neue", 16, "bold"),
            bg="#2a2a2a",
            fg="#ffffff"
        )
        name_label.pack(anchor=tk.W)
        
        # Profile type
        type_label = tk.Label(
            left_frame,
            text=f"Type: {profile.get('type', 'Unknown')}",
            font=("Helvetica Neue", 11),
            bg="#2a2a2a",
            fg="#8e8e93"
        )
        type_label.pack(anchor=tk.W, pady=(4, 0))
        
        # Surface
        surface_label = tk.Label(
            left_frame,
            text=f"Surface: {profile.get('surface', 'Not specified')}",
            font=("Helvetica Neue", 11),
            bg="#2a2a2a",
            fg="#8e8e93"
        )
        surface_label.pack(anchor=tk.W, pady=(2, 0))
        
        # Power and Speed
        settings_text = f"Power: {profile.get('power', 0)}% | Speed: {profile.get('speed', 0)} mm/min"
        settings_label = tk.Label(
            left_frame,
            text=settings_text,
            font=("Helvetica Neue", 10),
            bg="#2a2a2a",
            fg="#636366"
        )
        settings_label.pack(anchor=tk.W, pady=(2, 0))
        
        # Right side - Actions
        right_frame = tk.Frame(info_frame, bg="#2a2a2a")
        right_frame.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Action buttons
        btn_frame = tk.Frame(right_frame, bg="#2a2a2a")
        btn_frame.pack()
        
        # Delete button
        delete_btn = tk.Label(
            btn_frame,
            text="Delete",
            font=("Arial", 10, "bold"),
            bg="#FF453A",
            fg="#FFFFFF",
            padx=12,
            pady=6,
            cursor="hand2"
        )
        delete_btn.pack(side=tk.RIGHT, padx=(8, 0))
        delete_btn.bind("<Button-1>", lambda e: self._delete_profile(profile, machine, profiles_window))
        delete_btn.bind("<Enter>", lambda e: delete_btn.configure(bg="#CC3D33"))
        delete_btn.bind("<Leave>", lambda e: delete_btn.configure(bg="#FF453A"))
        
        # Edit button
        edit_profile_btn = tk.Label(
            btn_frame,
            text="Edit",
            font=("Arial", 10, "bold"),
            bg="#007AFF",
            fg="#FFFFFF",
            padx=15,
            pady=6,
            cursor="hand2"
        )
        edit_profile_btn.pack(side=tk.RIGHT, padx=(8, 0))
        edit_profile_btn.bind("<Button-1>", lambda e: self._edit_profile(profile, machine, profiles_window))
        edit_profile_btn.bind("<Enter>", lambda e: edit_profile_btn.configure(bg="#0056CC"))
        edit_profile_btn.bind("<Leave>", lambda e: edit_profile_btn.configure(bg="#007AFF"))
        
    def _show_add_profile_dialog(self, machine, parent_window):
        """Show dialog to add a new profile."""
        self._show_profile_dialog(machine, parent_window, None, "Add New Profile")
        
    def _edit_profile(self, profile, machine, parent_window):
        """Edit an existing profile."""
        self._show_profile_dialog(machine, parent_window, profile, "Edit Profile")
        
    def _show_profile_dialog(self, machine, parent_window, profile=None, title="Profile"):
        """Show profile creation/editing dialog."""
        dialog = tk.Toplevel(parent_window)
        dialog.title(title)
        dialog.geometry("450x400")
        self._center_window(dialog, 450, 400)
        dialog.configure(bg="#1a1a1a")
        dialog.transient(parent_window)
        dialog.grab_set()
        
        # Main frame
        main_frame = tk.Frame(dialog, bg="#1a1a1a", padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text=title,
            font=("Helvetica Neue", 18, "bold"),
            bg="#1a1a1a",
            fg="#ffffff"
        )
        title_label.pack(pady=(0, 20))
        
        # Form frame
        form_frame = tk.Frame(main_frame, bg="#1a1a1a")
        form_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Profile Name
        name_label = tk.Label(form_frame, text="Profile Name:", font=("Helvetica Neue", 12), 
                             bg="#1a1a1a", fg="#ffffff")
        name_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        name_entry = tk.Entry(form_frame, width=30, font=("Helvetica Neue", 11), bg="#2a2a2a", fg="#ffffff",
                             insertbackground="#ffffff", relief=tk.FLAT, bd=5)
        name_entry.grid(row=0, column=1, padx=(10, 0), pady=(0, 10), sticky="ew")
        
        # Profile Type
        type_label = tk.Label(form_frame, text="Profile Type:", font=("Helvetica Neue", 12),
                             bg="#1a1a1a", fg="#ffffff")
        type_label.grid(row=1, column=0, sticky="w", pady=(0, 5))
        
        type_var = tk.StringVar()
        type_combo = tk.OptionMenu(form_frame, type_var, "cutting1mm", "cutting2mm", "cutting4mm", "engrave")
        type_combo.config(bg="#2a2a2a", fg="#ffffff", font=("Helvetica Neue", 11), relief=tk.FLAT, bd=0,
                         highlightthickness=0, activebackground="#404040", activeforeground="#ffffff")
        type_combo.grid(row=1, column=1, padx=(10, 0), pady=(0, 10), sticky="ew")
        
        # Surface
        surface_label = tk.Label(form_frame, text="Surface:", font=("Helvetica Neue", 12),
                                bg="#1a1a1a", fg="#ffffff")
        surface_label.grid(row=2, column=0, sticky="w", pady=(0, 5))
        
        surface_entry = tk.Entry(form_frame, width=30, font=("Helvetica Neue", 11), bg="#2a2a2a", fg="#ffffff",
                                insertbackground="#ffffff", relief=tk.FLAT, bd=5)
        surface_entry.grid(row=2, column=1, padx=(10, 0), pady=(0, 10), sticky="ew")
        
        # Power
        power_label = tk.Label(form_frame, text="Power (1-100%):", font=("Helvetica Neue", 12),
                              bg="#1a1a1a", fg="#ffffff")
        power_label.grid(row=3, column=0, sticky="w", pady=(0, 5))
        
        power_entry = tk.Entry(form_frame, width=30, font=("Helvetica Neue", 11), bg="#2a2a2a", fg="#ffffff",
                              insertbackground="#ffffff", relief=tk.FLAT, bd=5)
        power_entry.grid(row=3, column=1, padx=(10, 0), pady=(0, 10), sticky="ew")
        
        # Speed
        speed_label = tk.Label(form_frame, text="Speed (0-6000):", font=("Helvetica Neue", 12),
                              bg="#1a1a1a", fg="#ffffff")
        speed_label.grid(row=4, column=0, sticky="w", pady=(0, 5))
        
        speed_entry = tk.Entry(form_frame, width=30, font=("Helvetica Neue", 11), bg="#2a2a2a", fg="#ffffff",
                              insertbackground="#ffffff", relief=tk.FLAT, bd=5)
        speed_entry.grid(row=4, column=1, padx=(10, 0), pady=(0, 10), sticky="ew")
        
        # Configure grid weights
        form_frame.grid_columnconfigure(1, weight=1)
        
        # Fill form if editing
        if profile:
            name_entry.insert(0, profile.get("name", ""))
            type_var.set(profile.get("type", "cutting1mm"))
            surface_entry.insert(0, profile.get("surface", ""))
            power_entry.insert(0, str(profile.get("power", "")))
            speed_entry.insert(0, str(profile.get("speed", "")))
        
        # Buttons frame
        button_frame = tk.Frame(main_frame, bg="#1a1a1a")
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Cancel button
        cancel_btn = tk.Label(
            button_frame,
            text="Cancel",
            font=("Arial", 11, "bold"),
            bg="#636366",
            fg="#FFFFFF",
            padx=20,
            pady=8,
            cursor="hand2"
        )
        cancel_btn.pack(side=tk.RIGHT, padx=(10, 0))
        cancel_btn.bind("<Button-1>", lambda e: dialog.destroy())
        cancel_btn.bind("<Enter>", lambda e: cancel_btn.configure(bg="#555555"))
        cancel_btn.bind("<Leave>", lambda e: cancel_btn.configure(bg="#636366"))
        
        # Save button
        save_btn = tk.Label(
            button_frame,
            text="Save Profile",
            font=("Arial", 11, "bold"),
            bg="#34C759",
            fg="#FFFFFF",
            padx=20,
            pady=8,
            cursor="hand2"
        )
        save_btn.pack(side=tk.RIGHT)
        save_btn.bind("<Button-1>", lambda e: self._save_profile(
            machine, profile, dialog, parent_window,
            name_entry.get(), type_var.get(), surface_entry.get(),
            power_entry.get(), speed_entry.get()
        ))
        save_btn.bind("<Enter>", lambda e: save_btn.configure(bg="#28A745"))
        save_btn.bind("<Leave>", lambda e: save_btn.configure(bg="#34C759"))
        
    def _save_profile(self, machine, existing_profile, dialog, parent_window, name, profile_type, surface, power, speed):
        """Save a profile (create new or update existing)."""
        # Validate inputs
        if not name.strip():
            messagebox.showerror("Validation Error", "Profile name is required.")
            return
            
        try:
            power_val = int(power)
            if not (1 <= power_val <= 100):
                raise ValueError()
        except ValueError:
            messagebox.showerror("Validation Error", "Power must be between 1 and 100.")
            return
            
        try:
            speed_val = int(speed)
            if not (0 <= speed_val <= 6000):
                raise ValueError()
        except ValueError:
            messagebox.showerror("Validation Error", "Speed must be between 0 and 6000.")
            return
        
        # Load current data
        machines_data = self._load_machines_data()
        
        # Find the machine
        machine_found = False
        for machine_data in machines_data["machines"]:
            if machine_data.get("id") == machine.get("id"):
                machine_found = True
                
                # Ensure profiles list exists
                if "profiles" not in machine_data:
                    machine_data["profiles"] = []
                
                if existing_profile:
                    # Update existing profile
                    for i, profile in enumerate(machine_data["profiles"]):
                        if profile.get("id") == existing_profile.get("id"):
                            machine_data["profiles"][i] = {
                                "id": existing_profile.get("id"),
                                "name": name.strip(),
                                "type": profile_type,
                                "surface": surface.strip(),
                                "power": power_val,
                                "speed": speed_val
                            }
                            break
                else:
                    # Create new profile
                    import uuid
                    new_profile = {
                        "id": f"profile_{uuid.uuid4().hex[:8]}",
                        "name": name.strip(),
                        "type": profile_type,
                        "surface": surface.strip(),
                        "power": power_val,
                        "speed": speed_val
                    }
                    machine_data["profiles"].append(new_profile)
                break
        
        if machine_found:
            # Save back to file
            self._save_machines_data(machines_data)
            dialog.destroy()
            # Refresh the profiles window
            self._refresh_profiles_window(parent_window, machine)
            messagebox.showinfo("Success", f"Profile '{name}' saved successfully!")
        else:
            messagebox.showerror("Error", "Machine not found.")
            
    def _delete_profile(self, profile, machine, parent_window):
        """Delete a profile."""
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the profile '{profile.get('name', 'Unknown')}'?"):
            # Load current data
            machines_data = self._load_machines_data()
            
            # Find the machine and remove the profile
            for machine_data in machines_data["machines"]:
                if machine_data.get("id") == machine.get("id"):
                    if "profiles" in machine_data:
                        machine_data["profiles"] = [p for p in machine_data["profiles"] if p.get("id") != profile.get("id")]
                    break
            
            # Save back to file
            self._save_machines_data(machines_data)
            
            # Refresh the profiles window
            self._refresh_profiles_window(parent_window, machine)
            messagebox.showinfo("Success", f"Profile '{profile.get('name', 'Unknown')}' deleted successfully!")
            
    def _save_machines_data(self, data):
        """Save machines data to laser.json file."""
        import json
        import os
        
        try:
            data_file = os.path.join(os.path.dirname(__file__), "DATA", "laser.json")
            with open(data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving machines data: {e}")
            
    def _refresh_profiles_window(self, profiles_window, machine):
        """Refresh the profiles window with updated data."""
        # Destroy current content and recreate
        for widget in profiles_window.winfo_children():
            widget.destroy()
        
        # Reload machine data
        machines_data = self._load_machines_data()
        updated_machine = None
        for machine_data in machines_data["machines"]:
            if machine_data.get("id") == machine.get("id"):
                updated_machine = machine_data
                break
        
        if updated_machine:
            self._create_profiles_interface(profiles_window, updated_machine)
    
    def _show_add_machine_dialog(self):
        """Show dialog to add a new machine."""
        messagebox.showinfo("Add Machine", "Add new machine dialog coming soon!")
        
    def _edit_machine(self, machine):
        """Edit machine settings."""
        messagebox.showinfo("Edit Machine", f"Edit settings for: {machine.get('name', 'Unknown')}")
        
    def _test_machine(self, machine):
        """Test machine connection."""
        messagebox.showinfo("Test Machine", f"Testing connection to: {machine.get('name', 'Unknown')}")
        
    def _show_app_settings(self):
        """Show application settings."""
        messagebox.showinfo("Settings", "Application settings coming soon!")
        
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
