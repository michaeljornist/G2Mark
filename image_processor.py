"""
Image processor for the G2burn Laser Engraving Application.
This module handles image processing for laser engraving operations.
"""

import numpy as np
from PIL import Image
from math import floor
from typing import Tuple, Dict, Optional
import os


class ImageProcessor:
    """Processes images for laser engraving operations."""
    
    def __init__(self):
        """Initialize the image processor."""
        self.default_laser_beam_diameter = 0.072  # mm
        self.default_threshold = 128
        
    def prepare_engraving_matrix(
        self,
        image_path: str,
        engrave_size: Tuple[float, float] = (300, 300),
        laser_beam_diameter: float = None,
        threshold: int = None
    ) -> Dict:
        """Convert an image into a scaled matrix for laser engraving.
        
        Args:
            image_path (str): Path to the image file
            engrave_size (Tuple[float, float]): (width_mm, height_mm) of engraving area
            laser_beam_diameter (float, optional): Beam diameter in mm
            threshold (int, optional): Threshold for binary conversion (0-255)
            
        Returns:
            Dict: Dictionary containing matrix data and metadata
        """
        if laser_beam_diameter is None:
            laser_beam_diameter = self.default_laser_beam_diameter
            
        if threshold is None:
            threshold = self.default_threshold
            
        # Validate inputs
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
            
        # Calculate resolution in laser steps
        slots_x = floor(engrave_size[0] / laser_beam_diameter)
        slots_y = floor(engrave_size[1] / laser_beam_diameter)
        slots = (slots_x, slots_y)
        
        # Open and process the image
        img = Image.open(image_path).convert("L")  # Convert to grayscale
        original_size = img.size
        
        # Resize image to match laser resolution
        img_resized = img.resize(slots, resample=Image.LANCZOS)
        
        # Save resized preview
        preview_path = self._save_preview(img_resized, image_path)
        
        # Convert to numpy array
        matrix = np.array(img_resized)
        
        # Create binary matrix (1 = laser on, 0 = laser off)
        binary_matrix = (matrix < threshold).astype(int)
        
        # Calculate actual engraving dimensions
        actual_width = slots_x * laser_beam_diameter
        actual_height = slots_y * laser_beam_diameter
        
        return {
            "original_image_path": image_path,
            "preview_path": preview_path,
            "original_size": original_size,
            "engrave_size_mm": engrave_size,
            "actual_size_mm": (actual_width, actual_height),
            "laser_beam_diameter_mm": laser_beam_diameter,
            "resolution_slots": slots,
            "threshold": threshold,
            "grayscale_matrix": matrix,
            "binary_matrix": binary_matrix,
            "total_laser_points": int(np.sum(binary_matrix))
        }
        
    def _save_preview(self, resized_image: Image.Image, original_path: str) -> str:
        """Save a preview of the resized image.
        
        Args:
            resized_image (Image.Image): The resized image
            original_path (str): Path to the original image
            
        Returns:
            str: Path to the saved preview image
        """
        # Generate preview filename
        base_name = os.path.splitext(os.path.basename(original_path))[0]
        preview_filename = f"{base_name}_engraving_preview.png"
        
        # Save in the same directory as the original or in a temp directory
        original_dir = os.path.dirname(original_path)
        preview_path = os.path.join(original_dir, preview_filename)
        
        try:
            resized_image.save(preview_path)
            return preview_path
        except Exception:
            # Fallback to current directory
            preview_path = preview_filename
            resized_image.save(preview_path)
            return preview_path
            
    def generate_engraving_gcode(
        self,
        matrix_data: Dict,
        feed_rate: int = 1000,
        laser_power: int = 255,
        travel_speed: int = 3000
    ) -> list:
        """Generate G-Code from an engraving matrix.
        
        Args:
            matrix_data (Dict): Matrix data from prepare_engraving_matrix
            feed_rate (int): Feed rate for engraving moves (mm/min)
            laser_power (int): Laser power for engraving (0-255 or 0-1000)
            travel_speed (int): Travel speed for rapid moves (mm/min)
            
        Returns:
            list: List of G-Code command strings
        """
        binary_matrix = matrix_data["binary_matrix"]
        beam_diameter = matrix_data["laser_beam_diameter_mm"]
        
        gcode_lines = []
        
        # Header
        gcode_lines.extend([
            "; G-code for image engraving",
            f"; Original image: {matrix_data['original_image_path']}",
            f"; Engraving size: {matrix_data['actual_size_mm'][0]:.3f}mm x {matrix_data['actual_size_mm'][1]:.3f}mm",
            f"; Resolution: {matrix_data['resolution_slots'][0]} x {matrix_data['resolution_slots'][1]} points",
            f"; Laser beam diameter: {beam_diameter:.3f}mm",
            f"; Total laser points: {matrix_data['total_laser_points']}",
            "G21 ; Set units to millimeters",
            "G90 ; Absolute positioning",
            "G0 X0 Y0 ; Move to origin",
            "M5 ; Laser off initially",
            ""
        ])
        
        rows, cols = binary_matrix.shape
        
        # Process each row
        for row in range(rows):
            y_pos = row * beam_diameter
            laser_on = False
            
            # Alternate scanning direction for efficiency (raster pattern)
            if row % 2 == 0:
                # Left to right
                col_range = range(cols)
            else:
                # Right to left
                col_range = range(cols - 1, -1, -1)
                
            for col in col_range:
                x_pos = col * beam_diameter
                should_engrave = binary_matrix[row, col] == 1
                
                if should_engrave and not laser_on:
                    # Turn laser on and move to position
                    gcode_lines.extend([
                        f"G0 X{x_pos:.3f} Y{y_pos:.3f} F{travel_speed}",
                        f"M3 S{laser_power}"
                    ])
                    laser_on = True
                    
                elif should_engrave and laser_on:
                    # Continue engraving to position
                    gcode_lines.append(f"G1 X{x_pos:.3f} Y{y_pos:.3f} F{feed_rate}")
                    
                elif not should_engrave and laser_on:
                    # Turn laser off
                    gcode_lines.append("M5")
                    laser_on = False
                    
            # Turn off laser at end of row if still on
            if laser_on:
                gcode_lines.append("M5")
                laser_on = False
                
            # Add blank line between rows for readability
            gcode_lines.append("")
            
        # Footer
        gcode_lines.extend([
            "M5 ; Ensure laser is off",
            "G0 X0 Y0 ; Return to origin",
            "M30 ; Program end"
        ])
        
        return gcode_lines
        
    def create_test_pattern(
        self,
        size: Tuple[int, int] = (400, 400),
        pattern_type: str = "grid"
    ) -> Image.Image:
        """Create a test pattern for engraving tests.
        
        Args:
            size (Tuple[int, int]): Size of the test pattern in pixels
            pattern_type (str): Type of pattern ("grid", "circles", "gradient")
            
        Returns:
            Image.Image: Generated test pattern image
        """
        width, height = size
        
        if pattern_type == "grid":
            return self._create_grid_pattern(width, height)
        elif pattern_type == "circles":
            return self._create_circles_pattern(width, height)
        elif pattern_type == "gradient":
            return self._create_gradient_pattern(width, height)
        else:
            raise ValueError(f"Unknown pattern type: {pattern_type}")
            
    def _create_grid_pattern(self, width: int, height: int) -> Image.Image:
        """Create a grid test pattern.
        
        Args:
            width (int): Pattern width in pixels
            height (int): Pattern height in pixels
            
        Returns:
            Image.Image: Grid pattern image
        """
        img = Image.new('L', (width, height), 255)  # White background
        
        # Create grid lines
        grid_spacing = 40
        line_width = 2
        
        # Draw vertical lines
        for x in range(0, width, grid_spacing):
            for y in range(height):
                for w in range(line_width):
                    if x + w < width:
                        img.putpixel((x + w, y), 0)  # Black lines
                        
        # Draw horizontal lines
        for y in range(0, height, grid_spacing):
            for x in range(width):
                for w in range(line_width):
                    if y + w < height:
                        img.putpixel((x, y + w), 0)  # Black lines
                        
        return img
        
    def _create_circles_pattern(self, width: int, height: int) -> Image.Image:
        """Create a circles test pattern.
        
        Args:
            width (int): Pattern width in pixels
            height (int): Pattern height in pixels
            
        Returns:
            Image.Image: Circles pattern image
        """
        from PIL import ImageDraw
        
        img = Image.new('L', (width, height), 255)  # White background
        draw = ImageDraw.Draw(img)
        
        # Draw concentric circles
        center_x, center_y = width // 2, height // 2
        max_radius = min(width, height) // 2 - 10
        
        for radius in range(20, max_radius, 20):
            # Draw circle outline
            left = center_x - radius
            top = center_y - radius
            right = center_x + radius
            bottom = center_y + radius
            
            draw.ellipse([left, top, right, bottom], outline=0, width=2)
            
        return img
        
    def _create_gradient_pattern(self, width: int, height: int) -> Image.Image:
        """Create a gradient test pattern.
        
        Args:
            width (int): Pattern width in pixels
            height (int): Pattern height in pixels
            
        Returns:
            Image.Image: Gradient pattern image
        """
        img = Image.new('L', (width, height))
        
        # Create horizontal gradient
        for x in range(width):
            gray_value = int((x / width) * 255)
            for y in range(height):
                img.putpixel((x, y), gray_value)
                
        return img
        
    def analyze_image(self, image_path: str) -> Dict:
        """Analyze an image and provide statistics.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            Dict: Image analysis results
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
            
        img = Image.open(image_path)
        
        # Convert to grayscale for analysis
        gray_img = img.convert('L')
        img_array = np.array(gray_img)
        
        # Calculate statistics
        analysis = {
            "file_path": image_path,
            "file_size_bytes": os.path.getsize(image_path),
            "image_size": img.size,
            "color_mode": img.mode,
            "has_transparency": img.mode in ('RGBA', 'LA') or 'transparency' in img.info,
            "grayscale_stats": {
                "min_value": int(np.min(img_array)),
                "max_value": int(np.max(img_array)),
                "mean_value": float(np.mean(img_array)),
                "std_dev": float(np.std(img_array))
            },
            "histogram": self._calculate_histogram(img_array),
            "estimated_engraving_coverage": self._estimate_coverage(img_array)
        }
        
        return analysis
        
    def _calculate_histogram(self, img_array: np.ndarray, bins: int = 10) -> Dict:
        """Calculate a simplified histogram of image values.
        
        Args:
            img_array (np.ndarray): Image array
            bins (int): Number of histogram bins
            
        Returns:
            Dict: Histogram data
        """
        hist, bin_edges = np.histogram(img_array, bins=bins, range=(0, 255))
        
        histogram = {}
        for i in range(len(hist)):
            range_start = int(bin_edges[i])
            range_end = int(bin_edges[i + 1])
            histogram[f"{range_start}-{range_end}"] = int(hist[i])
            
        return histogram
        
    def _estimate_coverage(self, img_array: np.ndarray, threshold: int = 128) -> Dict:
        """Estimate laser engraving coverage.
        
        Args:
            img_array (np.ndarray): Image array
            threshold (int): Threshold for binary conversion
            
        Returns:
            Dict: Coverage estimation
        """
        binary_array = img_array < threshold
        total_pixels = img_array.size
        laser_pixels = int(np.sum(binary_array))
        
        coverage_percentage = (laser_pixels / total_pixels) * 100
        
        return {
            "total_pixels": total_pixels,
            "laser_pixels": laser_pixels,
            "coverage_percentage": round(coverage_percentage, 2),
            "threshold_used": threshold
        }
