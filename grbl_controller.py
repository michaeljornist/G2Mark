"""
GRBL communication module for the G2burn Laser Engraving Application.
This module handles communication with GRBL-based laser engravers.
"""

import serial
import time
import threading
from tkinter import messagebox
from typing import Optional, List, Callable


class GRBLController:
    """Handles communication with GRBL-based laser engravers."""
    
    def __init__(self):
        """Initialize the GRBL controller."""
        self.serial_connection: Optional[serial.Serial] = None
        self.is_connected = False
        self.port = '/dev/tty.wchusbserial1130'  # Default port, can be changed
        self.baud_rate = 115200
        self.timeout = 1
        
        # Status tracking
        self.grbl_status = "Unknown"
        self.position = {"x": 0.0, "y": 0.0, "z": 0.0}
        self.is_homed = False
        
        # Callbacks
        self.status_callback: Optional[Callable] = None
        self.message_callback: Optional[Callable] = None
        
    def set_port(self, port: str):
        """Set the serial port for communication.
        
        Args:
            port (str): Serial port path (e.g., '/dev/tty.wchusbserial1130')
        """
        self.port = port
        
    def set_baud_rate(self, baud_rate: int):
        """Set the baud rate for communication.
        
        Args:
            baud_rate (int): Baud rate (default: 115200)
        """
        self.baud_rate = baud_rate
        
    def connect(self) -> bool:
        """Connect to the GRBL controller.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.serial_connection = serial.Serial(
                self.port, 
                self.baud_rate, 
                timeout=self.timeout
            )
            time.sleep(2)  # Wait for connection to stabilize
            
            # Wake up GRBL
            self._send_wake_up()
            
            self.is_connected = True
            self._log_message(f"Connected to GRBL on {self.port}")
            
            # Start status monitoring
            self._start_status_monitoring()
            
            return True
            
        except serial.SerialException as e:
            self._log_message(f"Failed to connect: {str(e)}")
            self.is_connected = False
            return False
            
    def disconnect(self):
        """Disconnect from the GRBL controller."""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            
        self.is_connected = False
        self.grbl_status = "Disconnected"
        self._log_message("Disconnected from GRBL")
        
    def _send_wake_up(self):
        """Send wake up sequence to GRBL."""
        if not self.is_connected or not self.serial_connection:
            return
            
        self.serial_connection.write(b"\r\n\r\n")
        time.sleep(2)
        self.serial_connection.flushInput()
        
    def send_command(self, command: str) -> bool:
        """Send a G-Code command to GRBL.
        
        Args:
            command (str): G-Code command to send
            
        Returns:
            bool: True if command sent successfully, False otherwise
        """
        if not self.is_connected or not self.serial_connection:
            self._log_message("Not connected to GRBL")
            return False
            
        try:
            # Ensure command ends with newline
            if not command.endswith('\n'):
                command += '\n'
                
            self.serial_connection.write(command.encode())
            self._log_message(f"Sent: {command.strip()}")
            return True
            
        except Exception as e:
            self._log_message(f"Error sending command: {str(e)}")
            return False
            
    def send_gcode_file(self, gcode_lines: List[str], progress_callback: Optional[Callable] = None):
        """Send multiple G-Code lines to GRBL.
        
        Args:
            gcode_lines (List[str]): List of G-Code commands
            progress_callback (Optional[Callable]): Callback for progress updates
        """
        if not self.is_connected:
            self._log_message("Not connected to GRBL")
            return
            
        def send_file():
            total_lines = len(gcode_lines)
            
            for i, line in enumerate(gcode_lines):
                # Skip empty lines and comments
                line = line.strip()
                if not line or line.startswith(';'):
                    continue
                    
                # Send command and wait for response
                if self.send_command(line):
                    self._wait_for_ok()
                    
                    # Update progress
                    if progress_callback:
                        progress = int((i + 1) / total_lines * 100)
                        progress_callback(progress, line)
                        
                time.sleep(0.1)  # Small delay between commands
                
        # Run in separate thread to avoid blocking UI
        thread = threading.Thread(target=send_file, daemon=True)
        thread.start()
        
    def _wait_for_ok(self, timeout: float = 5.0):
        """Wait for 'ok' response from GRBL.
        
        Args:
            timeout (float): Maximum time to wait in seconds
        """
        if not self.is_connected or not self.serial_connection:
            return
            
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.serial_connection.in_waiting:
                response = self.serial_connection.readline().decode().strip()
                self._log_message(f"Received: {response}")
                
                if response.lower() == 'ok':
                    return
                elif response.lower().startswith('error'):
                    self._log_message(f"GRBL Error: {response}")
                    return
                    
            time.sleep(0.1)
            
    def home_machine(self):
        """Home the machine (G28 command)."""
        if self.send_command("G28"):
            self.is_homed = True
            self._log_message("Homing machine...")
            
    def set_absolute_positioning(self):
        """Set absolute positioning mode (G90)."""
        self.send_command("G90")
        
    def set_relative_positioning(self):
        """Set relative positioning mode (G91)."""
        self.send_command("G91")
        
    def laser_on(self, power: int = 1000):
        """Turn laser on with specified power.
        
        Args:
            power (int): Laser power (0-1000 or 0-255 depending on setup)
        """
        self.send_command(f"M3 S{power}")
        
    def laser_off(self):
        """Turn laser off."""
        self.send_command("M5")
        
    def move_to(self, x: float, y: float, feed_rate: int = 1000):
        """Move to specified coordinates.
        
        Args:
            x (float): X coordinate in mm
            y (float): Y coordinate in mm
            feed_rate (int): Feed rate in mm/min
        """
        self.send_command(f"G1 X{x:.3f} Y{y:.3f} F{feed_rate}")
        
    def rapid_move_to(self, x: float, y: float):
        """Rapid move to specified coordinates.
        
        Args:
            x (float): X coordinate in mm
            y (float): Y coordinate in mm
        """
        self.send_command(f"G0 X{x:.3f} Y{y:.3f}")
        
    def jog(self, x: float = 0, y: float = 0, feed_rate: int = 1000):
        """Jog the machine by specified amounts.
        
        Args:
            x (float): X distance to jog in mm
            y (float): Y distance to jog in mm
            feed_rate (int): Feed rate in mm/min
        """
        if x != 0 or y != 0:
            self.send_command("G91")  # Relative mode
            self.send_command(f"G1 X{x:.3f} Y{y:.3f} F{feed_rate}")
            self.send_command("G90")  # Back to absolute mode
            
    def get_settings(self) -> List[str]:
        """Get GRBL settings.
        
        Returns:
            List[str]: List of GRBL settings
        """
        if not self.is_connected or not self.serial_connection:
            return []
            
        self.send_command("$$")
        time.sleep(1)
        
        settings = []
        while self.serial_connection.in_waiting:
            line = self.serial_connection.readline().decode().strip()
            if line:
                settings.append(line)
                
        return settings
        
    def get_status(self) -> str:
        """Get current GRBL status.
        
        Returns:
            str: Current status
        """
        if not self.is_connected:
            return "Disconnected"
            
        self.send_command("?")
        time.sleep(0.1)
        
        if self.serial_connection and self.serial_connection.in_waiting:
            response = self.serial_connection.readline().decode().strip()
            self._parse_status_response(response)
            
        return self.grbl_status
        
    def _parse_status_response(self, response: str):
        """Parse GRBL status response.
        
        Args:
            response (str): Status response from GRBL
        """
        # Example: <Idle|MPos:0.000,0.000,0.000|FS:0,0>
        if response.startswith('<') and response.endswith('>'):
            parts = response[1:-1].split('|')
            
            if parts:
                self.grbl_status = parts[0]
                
            # Parse position if available
            for part in parts:
                if part.startswith('MPos:'):
                    coords = part.split(':')[1].split(',')
                    if len(coords) >= 2:
                        self.position['x'] = float(coords[0])
                        self.position['y'] = float(coords[1])
                        if len(coords) >= 3:
                            self.position['z'] = float(coords[2])
                            
    def _start_status_monitoring(self):
        """Start monitoring GRBL status in background."""
        def monitor():
            while self.is_connected:
                self.get_status()
                time.sleep(1)  # Check status every second
                
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
        
    def _log_message(self, message: str):
        """Log a message.
        
        Args:
            message (str): Message to log
        """
        if self.message_callback:
            self.message_callback(message)
        else:
            print(f"GRBL: {message}")
            
    def set_status_callback(self, callback: Callable):
        """Set callback for status updates.
        
        Args:
            callback (Callable): Function to call with status updates
        """
        self.status_callback = callback
        
    def set_message_callback(self, callback: Callable):
        """Set callback for message logging.
        
        Args:
            callback (Callable): Function to call with log messages
        """
        self.message_callback = callback
        
    def emergency_stop(self):
        """Send emergency stop command."""
        if self.is_connected and self.serial_connection:
            self.serial_connection.write(b"\x18")  # Ctrl-X
            self.laser_off()
            self._log_message("EMERGENCY STOP!")
            
    def soft_reset(self):
        """Send soft reset command."""
        if self.is_connected and self.serial_connection:
            self.serial_connection.write(b"\x18")  # Ctrl-X
            time.sleep(1)
            self._send_wake_up()
            self._log_message("Soft reset performed")
            
    def is_idle(self) -> bool:
        """Check if GRBL is in idle state.
        
        Returns:
            bool: True if idle, False otherwise
        """
        return self.grbl_status.lower() == "idle"
        
    def get_position(self) -> dict:
        """Get current machine position.
        
        Returns:
            dict: Current position {x, y, z}
        """
        return self.position.copy()
