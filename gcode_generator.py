"""
G-Code generator for the G2burn Laser Engraving Application.
This module handles the generation of G-Code from drawing objects.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
import numpy as np
from PIL import Image, ImageTk


class GCodeGenerator:
    """Generates G-Code from drawing objects for laser engraving."""
    
    def __init__(self, canvas, sketching_stage):
        """Initialize the G-Code generator.
        
        Args:
            canvas (tk.Canvas): The canvas containing drawing objects
            sketching_stage (SketchingStage): Reference to the sketching stage
        """
        self.canvas = canvas
        self.sketching_stage = sketching_stage
        
        # G-Code settings
        self.feed_rate = 1000  # mm/min
        self.laser_power = 255  # 0-255 or 0-1000 depending on controller
        self.travel_speed = 1000  # mm/min for rapid moves
        
    def generate_instructions_from_image(self, image_path, origin):
        """Generate instructions from a high-resolution image.
        
        Args:
            image_path (str): Path to the high-resolution image
            origin (tuple): Origin coordinates as (x, y) in pixels
            
        Returns:
            list: List of lists containing tuples (from, to, power, speed) for each row
        """
        try:
            # Load the image
            image = Image.open(image_path)
            
            # Convert to grayscale if not already
            if image.mode != 'L':
                image = image.convert('L')
            
            # Convert to numpy array
            img_array = np.array(image)
            
            # Convert to binary matrix (1 for black/dark pixels, 0 for white/light pixels)
            # Using threshold of 128 (middle value)
            binary_matrix = (img_array < 128).astype(int)
            
            # Print the origin coordinates
            print(f"Origin coordinates: {origin}")
            print(f"Image size: {binary_matrix.shape} pixels")
            print(f"Matrix shape: {binary_matrix.shape[1]} x {binary_matrix.shape[0]} (width x height)")
            
            # Generate line segments for each row
            all_instructions = []
            
            # Scan each row
            for row_idx in range(binary_matrix.shape[0]):
                row = binary_matrix[row_idx]
                row_instructions = []
                
                # Track line creation state
                in_line = False
                line_start = None
                
                # Scan each pixel in the row
                for col_idx in range(len(row)):
                    pixel_value = row[col_idx]
                    
                    if pixel_value == 1:  # Found a black pixel
                        if not in_line:
                            # Start of a new line
                            in_line = True
                            line_start = col_idx
                            print(f"Saw first 1 at index (col={col_idx}, row={row_idx}) -> coordinate ({col_idx}, {row_idx})")
                    
                    else:  # pixel_value == 0, found a white pixel
                        if in_line:
                            # End of current line
                            line_end = col_idx - 1  # Last black pixel was at col_idx - 1
                            in_line = False
                            
                            # Create instruction tuple: (from, to, power, speed)
                            # Coordinates are (x, y) = (col, row)
                            instruction = (
                                (line_start, row_idx),  # from coordinate (x, y)
                                (line_end + 1, row_idx),  # to coordinate (x, y) - end position after last black pixel
                                self.laser_power,        # power
                                self.travel_speed        # speed
                            )
                            row_instructions.append(instruction)
                            
                            # print(f"Saw last 1 (after that 0) at (col={line_end}, row={row_idx}) -> coordinate ({line_end}, {row_idx})")
                            # print(f"Generated instruction: {instruction}")
                
                # Handle case where row ends while still in a line
                if in_line:
                    line_end = len(row) - 1  # Last pixel in row
                    instruction = (
                        (line_start, row_idx),   # from coordinate (x, y)
                        (line_end + 1, row_idx), # to coordinate (x, y) - end position after last pixel
                        self.laser_power,        # power
                        self.travel_speed        # speed
                    )
                    row_instructions.append(instruction)
                    
                    
                    # print(f"Saw last 1 (end of row) at (col={line_end}, row={row_idx}) -> coordinate ({line_end}, {row_idx})")
                    # print(f"Generated instruction: {instruction}")
                
                # Add row instructions to all instructions
                if row_instructions:  # Only add if row has any instructions
                    all_instructions.append(row_instructions)
                    print(f"Row {row_idx} instructions: {row_instructions}")
            
            print(f"\nTotal rows with instructions: {len(all_instructions)}")
            print(f"Total line segments generated: {sum(len(row) for row in all_instructions)}")
            # print(f"All instructions: {all_instructions}")
            return all_instructions
            
        except Exception as e:
            print(f"Error processing image: {e}")
            messagebox.showerror("Image Processing Error", f"Failed to process image:\n{str(e)}")
            return None





    def generate_instructions_from_image_optimized_v1(self, image_path, origin):
        """Generate instructions from a high-resolution image.
        
        Args:
            image_path (str): Path to the high-resolution image
            origin (tuple): Origin coordinates as (x, y) in pixels
            
        Returns:
            list: List of lists containing tuples (from, to, power, speed) for each row
        """
        try:
            # Load the image
            image = Image.open(image_path)
            
            # Convert to grayscale if not already
            if image.mode != 'L':
                image = image.convert('L')
            
            # Convert to numpy array
            img_array = np.array(image)
            
            # Convert to binary matrix (1 for black/dark pixels, 0 for white/light pixels)
            # Using threshold of 128 (middle value)
            binary_matrix = (img_array < 128).astype(int)
            
            # Print the origin coordinates
            print(f"Origin coordinates: {origin}")
            print(f"Image size: {binary_matrix.shape} pixels")
            print(f"Matrix shape: {binary_matrix.shape[1]} x {binary_matrix.shape[0]} (width x height)")
            
            # Generate line segments for each row
            all_instructions = []
            
            optimization_dict = {}
            instruction_id = 0
            
            #Find closest blackdot to start with from the origin with some recursive spreading function / or some numpy prebuild function
            


            # Scan each row
            for row_idx in range(binary_matrix.shape[0]):
                row = binary_matrix[row_idx]
                row_instructions = []
                
                # Track line creation state
                in_line = False
                line_start = None
                
                # Scan each pixel in the row
                for col_idx in range(len(row)):
                    pixel_value = row[col_idx]
                    
                    if pixel_value == 1:  # Found a black pixel
                        if not in_line:
                            # Start of a new line
                            in_line = True
                            line_start = col_idx
                            print(f"Saw first 1 at index (col={col_idx}, row={row_idx}) -> coordinate ({col_idx}, {row_idx})")
                    
                    else:  # pixel_value == 0, found a white pixel
                        if in_line:
                            # End of current line
                            line_end = col_idx - 1  # Last black pixel was at col_idx - 1
                            in_line = False
                            
                            # Create instruction tuple: (from, to, power, speed)
                            # Coordinates are (x, y) = (col, row)
                            instruction = (
                                (line_start, row_idx),  # from coordinate (x, y)
                                (line_end + 1, row_idx),  # to coordinate (x, y) - end position after last black pixel
                                self.laser_power,        # power
                                self.travel_speed        # speed
                            )
                            row_instructions.append(instruction)
                            
                            # print(f"Saw last 1 (after that 0) at (col={line_end}, row={row_idx}) -> coordinate ({line_end}, {row_idx})")
                            # print(f"Generated instruction: {instruction}")
                
                # Handle case where row ends while still in a line
                if in_line:
                    line_end = len(row) - 1  # Last pixel in row
                    instruction = (
                        (line_start, row_idx),   # from coordinate (x, y)
                        (line_end + 1, row_idx), # to coordinate (x, y) - end position after last pixel
                        self.laser_power,        # power
                        self.travel_speed        # speed
                    )
                    row_instructions.append(instruction)
                    
                    
                    # print(f"Saw last 1 (end of row) at (col={line_end}, row={row_idx}) -> coordinate ({line_end}, {row_idx})")
                    # print(f"Generated instruction: {instruction}")
                
                # Add row instructions to all instructions
                if row_instructions:  # Only add if row has any instructions
                    all_instructions.append(row_instructions)
                    print(f"Row {row_idx} instructions: {row_instructions}")
            
            print(f"\nTotal rows with instructions: {len(all_instructions)}")
            print(f"Total line segments generated: {sum(len(row) for row in all_instructions)}")
            # print(f"All instructions: {all_instructions}")
            return all_instructions
            
        except Exception as e:
            print(f"Error processing image: {e}")
            messagebox.showerror("Image Processing Error", f"Failed to process image:\n{str(e)}")
            return None
        

    def convert_instructions_to_gcode(self, all_instructions, origin, image_height_pixels):
        """Convert instruction tuples to G-Code strings relative to origin.
        
        Args:
            all_instructions (list): List of lists containing instruction tuples
            origin (tuple): Origin coordinates as (x, y) in pixels
            image_height_pixels (int): Height of the image in pixels (for Y-axis flipping)
            
        Returns:
            list: List of G-Code command strings
        """
        gcode_commands = []
        pixel_size_mm = 0.072  # mm per pixel (as used in high-res export)
        
        # Start with absolute positioning
        gcode_commands.append("G90")
        
        origin_x, origin_y = origin
        print(f"Converting instructions to G-Code with origin at ({origin_x}, {origin_y})")
        print(f"Image height: {image_height_pixels} pixels")
        
        # Process each row of instructions
        for row_instructions in all_instructions:
            for instruction in row_instructions:
                from_coord, to_coord, power, speed = instruction
                from_x, from_y = from_coord
                to_x, to_y = to_coord
                
                # Flip Y-coordinates to match G-Code coordinate system
                # In image: Y=0 is top, Y increases downward
                # In G-Code: Y=0 is bottom, Y increases upward
                flipped_from_y = image_height_pixels - 1 - from_y
                flipped_to_y = image_height_pixels - 1 - to_y
                
                # Calculate relative positions from origin in pixels
                rel_from_x = from_x - origin_x
                rel_from_y = flipped_from_y - (image_height_pixels - 1 - origin_y)  # Flip origin Y too
                rel_to_x = to_x - origin_x
                rel_to_y = flipped_to_y - (image_height_pixels - 1 - origin_y)  # Flip origin Y too
                
                # Convert to mm (multiply by pixel size)
                from_x_mm = rel_from_x * pixel_size_mm
                from_y_mm = rel_from_y * pixel_size_mm
                to_x_mm = rel_to_x * pixel_size_mm
                to_y_mm = rel_to_y * pixel_size_mm
                
                print(f"Instruction: {instruction}")
                print(f"  Original Y: {from_y} -> Flipped Y: {flipped_from_y}")
                print(f"  Relative pixels: from({rel_from_x}, {rel_from_y}) to({rel_to_x}, {rel_to_y})")
                print(f"  Relative mm: from({from_x_mm:.3f}, {from_y_mm:.3f}) to({to_x_mm:.3f}, {to_y_mm:.3f})")
                
                # Move to start position (rapid move, laser off)
                gcode_commands.append(f"G1 X{from_x_mm:.3f} Y{from_y_mm:.3f} S{power}")
                
                # Turn on laser
                gcode_commands.append("M3")
                
                # Engrave line (linear move with laser on)
                gcode_commands.append(f"G1 X{to_x_mm:.3f} Y{to_y_mm:.3f} F{speed} S{power}")
                
                # Turn off laser
                gcode_commands.append("M5")
        
        print(f"\nGenerated {len(gcode_commands)} G-Code commands")
        print("Sample G-Code commands:")
        for i, cmd in enumerate(gcode_commands[:10]):  # Show first 10 commands
            print(f"  {i+1}: {cmd}")
        if len(gcode_commands) > 10:
            print(f"  ... and {len(gcode_commands) - 10} more commands")
            
        return gcode_commands
        
    def show_preview_window(self, image_path, gcode_commands, origin):
        """Show preview window with image and G-Code before printing.
        
        Args:
            image_path (str): Path to the high-resolution image
            gcode_commands (list): List of G-Code command strings
            origin (tuple): Origin coordinates as (x, y) in pixels
        """
        # Store G-Code commands for later use
        self._current_gcode_commands = gcode_commands
        
        # Create new window
        preview_window = tk.Toplevel()
        preview_window.title("Preview Before Print - G2burn")
        preview_window.geometry("1000x700")
        preview_window.resizable(True, True)
        
        # Create main frame with padding
        main_frame = ttk.Frame(preview_window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for resizing
        preview_window.columnconfigure(0, weight=1)
        preview_window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title label
        title_label = ttk.Label(main_frame, text="Preview Before Print", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Left side - Image preview
        image_frame = ttk.LabelFrame(main_frame, text="High Resolution Image Preview", padding="5")
        image_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        try:
            # Load and display the image
            image = Image.open(image_path)
            
            # Scale image to fit in preview (max 400x400)
            max_size = 400
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage for display
            photo = ImageTk.PhotoImage(image)
            
            # Create image label
            image_label = ttk.Label(image_frame, image=photo)
            image_label.image = photo  # Keep a reference
            image_label.grid(row=0, column=0, padx=5, pady=5)
            
            # Image info
            original_image = Image.open(image_path)
            info_text = f"Original Size: {original_image.size[0]} x {original_image.size[1]} pixels\n"
            info_text += f"Origin: ({origin[0]}, {origin[1]}) pixels\n"
            info_text += f"Estimated Print Size: {original_image.size[0] * 0.072:.1f} x {original_image.size[1] * 0.072:.1f} mm"
            
            info_label = ttk.Label(image_frame, text=info_text, font=("Arial", 9))
            info_label.grid(row=1, column=0, pady=(10, 0))
            
        except Exception as e:
            error_label = ttk.Label(image_frame, text=f"Error loading image:\n{str(e)}")
            error_label.grid(row=0, column=0, padx=5, pady=5)
        
        # Right side - G-Code preview
        gcode_frame = ttk.LabelFrame(main_frame, text="G-Code Commands", padding="5")
        gcode_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        gcode_frame.columnconfigure(0, weight=1)
        gcode_frame.rowconfigure(0, weight=1)
        
        # G-Code text area with scrollbar
        gcode_text = scrolledtext.ScrolledText(
            gcode_frame, 
            width=50, 
            height=20,
            wrap=tk.NONE,
            font=("Courier", 9)
        )
        gcode_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Insert G-Code commands
        gcode_content = "\n".join(gcode_commands)
        gcode_text.insert(tk.END, gcode_content)
        gcode_text.config(state=tk.DISABLED)  # Make read-only
        
        # G-Code stats
        stats_text = f"Total Commands: {len(gcode_commands)}\n"
        stats_text += f"Estimated Lines: {len([cmd for cmd in gcode_commands if cmd.startswith('G1')])}\n"
        stats_text += f"Rapid Moves: {len([cmd for cmd in gcode_commands if cmd.startswith('G0')])}"
        
        stats_label = ttk.Label(gcode_frame, text=stats_text, font=("Arial", 9))
        stats_label.grid(row=1, column=0, pady=(10, 0), sticky=tk.W)
        
        # Bottom buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(20, 0))
        
        # Test connection button
        test_button = ttk.Button(
            button_frame, 
            text="Test Laser Engraver Connection",
            command=self._test_connection
        )
        test_button.grid(row=0, column=0, padx=(0, 10))
        
        # G2Mark button (sends G-Code to laser)
        g2mark_button = ttk.Button(
            button_frame, 
            text="G2Mark - Send to Laser",
            command=self._g2mark_send_gcode,
            style="Accent.TButton"
        )
        g2mark_button.grid(row=0, column=1, padx=(10, 0))
        
        # Close button
        close_button = ttk.Button(
            button_frame, 
            text="Close",
            command=preview_window.destroy
        )
        close_button.grid(row=0, column=2, padx=(20, 0))
        
        # Center the window
        preview_window.update_idletasks()
        width = preview_window.winfo_width()
        height = preview_window.winfo_height()
        x = (preview_window.winfo_screenwidth() // 2) - (width // 2)
        y = (preview_window.winfo_screenheight() // 2) - (height // 2)
        preview_window.geometry(f"{width}x{height}+{x}+{y}")
        
    def _test_connection(self):
        """Test laser engraver connection by moving head in 1cm rectangle."""
        try:
            import serial
            import time
            
            # Connection parameters
            port = '/dev/tty.wchusbserial1130'
            baud_rate = 115200
            
            # Show connection attempt dialog
            result = messagebox.askyesno(
                "Test Connection", 
                f"Test laser engraver connection?\n\nPort: {port}\nBaud Rate: {baud_rate}\n\nThis will move the laser head in a 1cm rectangle.\nMake sure the laser is safe to move!"
            )
            
            if not result:
                return
            
            # Attempt connection
            try:
                ser = serial.Serial(port, baud_rate, timeout=1)
                time.sleep(2)
                
                # Wake up GRBL
                ser.write(b"\r\n\r\n")
                time.sleep(2)
                ser.flushInput()
                
                # Send test movement commands (1cm rectangle)
                commands = [
                    b"G90\n",           # Absolute positioning
                    b"G0 X10 F3000\n",  # Right 1cm (10mm)
                    b"G0 X10 Y10 F3000\n",  # Up 1cm
                    b"G0 X0 Y10 F3000\n",   # Left 1cm
                    b"G0 X0 Y0 F3000\n"     # Back to origin
                ]
                
                for cmd in commands:
                    ser.write(cmd)
                    time.sleep(0.1)  # Small delay between commands
                
                # Close connection
                time.sleep(1)
                ser.close()
                
                messagebox.showinfo(
                    "Test Connection - Success", 
                    "Connection test completed successfully!\n\nThe laser head should have moved in a 1cm rectangle."
                )
                
            except serial.SerialException as e:
                messagebox.showerror(
                    "Connection Error", 
                    f"Failed to connect to laser engraver:\n\n{str(e)}\n\nPlease check:\n• Cable connection\n• Port name ({port})\n• Device is powered on"
                )
                
            except Exception as e:
                messagebox.showerror(
                    "Test Error", 
                    f"Error during connection test:\n\n{str(e)}"
                )
                
        except ImportError:
            messagebox.showerror(
                "Missing Module", 
                "The 'pyserial' module is required for laser communication.\n\nInstall it with:\npip install pyserial"
            )
        
    def _g2mark_send_gcode(self):
        """Send G-Code commands to the laser engraver."""
        # Get the G-Code commands from the preview window
        if not hasattr(self, '_current_gcode_commands') or not self._current_gcode_commands:
            messagebox.showerror(
                "No G-Code", 
                "No G-Code commands available to send.\nPlease generate G-Code first."
            )
            return
            
        try:
            import serial
            import time
            
            # Connection parameters
            port = '/dev/tty.wchusbserial1130'
            baud_rate = 115200
            
            # Show confirmation dialog with command count
            command_count = len(self._current_gcode_commands)
            result = messagebox.askyesno(
                "Send G-Code to Laser", 
                f"Send {command_count} G-Code commands to the laser engraver?\n\nPort: {port}\nBaud Rate: {baud_rate}\n\nThis will start the engraving process.\nMake sure the laser is positioned correctly and safety measures are in place!"
            )
            
            if not result:
                return
            
            # Show progress window
            progress_window = tk.Toplevel()
            progress_window.title("Sending G-Code - G2burn")
            progress_window.geometry("400x200")
            progress_window.resizable(False, False)
            
            # Center the progress window
            progress_window.update_idletasks()
            x = (progress_window.winfo_screenwidth() // 2) - (200)
            y = (progress_window.winfo_screenheight() // 2) - (100)
            progress_window.geometry(f"400x200+{x}+{y}")
            
            # Progress frame
            progress_frame = ttk.Frame(progress_window, padding="20")
            progress_frame.pack(fill=tk.BOTH, expand=True)
            
            # Status label
            status_label = ttk.Label(progress_frame, text="Connecting to laser engraver...", font=("Arial", 12))
            status_label.pack(pady=10)
            
            # Progress bar
            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, maximum=100)
            progress_bar.pack(fill=tk.X, pady=10)
            
            # Command counter
            counter_label = ttk.Label(progress_frame, text="0 / 0 commands sent", font=("Arial", 10))
            counter_label.pack(pady=5)
            
            # Cancel button
            cancel_requested = tk.BooleanVar(value=False)
            cancel_button = ttk.Button(progress_frame, text="Cancel", command=lambda: cancel_requested.set(True))
            cancel_button.pack(pady=10)
            
            # Update the window
            progress_window.update()
            
            try:
                # Attempt connection
                ser = serial.Serial(port, baud_rate, timeout=1)
                time.sleep(2)
                
                status_label.config(text="Connected! Initializing laser...")
                progress_window.update()
                
                # Wake up GRBL
                ser.write(b"\r\n\r\n")
                time.sleep(2)
                ser.flushInput()
                
                status_label.config(text="Sending G-Code commands...")
                progress_window.update()
                
                # Send G-Code commands
                total_commands = len(self._current_gcode_commands)
                
                for i, command in enumerate(self._current_gcode_commands):
                    # Check if cancel was requested
                    if cancel_requested.get():
                        status_label.config(text="Cancelling...")
                        progress_window.update()
                        # Send emergency stop
                        ser.write(b"M5\n")  # Turn off laser
                        ser.write(b"!\n")   # Feed hold
                        break
                    
                    # Send command
                    command_bytes = (command + "\n").encode('utf-8')
                    ser.write(command_bytes)
                    
                    # Update progress
                    progress_percent = ((i + 1) / total_commands) * 100
                    progress_var.set(progress_percent)
                    counter_label.config(text=f"{i + 1} / {total_commands} commands sent")
                    
                    # Update window
                    progress_window.update()
                    
                    # Small delay between commands
                    time.sleep(0.1)
                
                if not cancel_requested.get():
                    status_label.config(text="G-Code sent successfully!")
                    cancel_button.config(text="Close")
                    
                    # Close connection
                    time.sleep(1)
                    ser.close()
                    
                    messagebox.showinfo(
                        "G2Mark - Success", 
                        f"G-Code sent successfully!\n\n{total_commands} commands were sent to the laser engraver.\nThe engraving process should now be running."
                    )
                else:
                    status_label.config(text="Operation cancelled!")
                    cancel_button.config(text="Close")
                    ser.close()
                    
                    messagebox.showwarning(
                        "G2Mark - Cancelled", 
                        "G-Code transmission was cancelled.\nThe laser has been stopped."
                    )
                
            except serial.SerialException as e:
                progress_window.destroy()
                messagebox.showerror(
                    "Connection Error", 
                    f"Failed to connect to laser engraver:\n\n{str(e)}\n\nPlease check:\n• Cable connection\n• Port name ({port})\n• Device is powered on"
                )
                
            except Exception as e:
                progress_window.destroy()
                messagebox.showerror(
                    "G2Mark Error", 
                    f"Error during G-Code transmission:\n\n{str(e)}"
                )
                
        except ImportError:
            messagebox.showerror(
                "Missing Module", 
                "The 'pyserial' module is required for laser communication.\n\nInstall it with:\npip install pyserial"
            )
