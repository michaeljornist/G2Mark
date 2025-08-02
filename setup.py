#!/usr/bin/env python3
"""
Setup script for G2burn Laser Engraving Application.
This script helps set up the environment and run the application.
"""

import sys
import subprocess
import importlib.util
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version}")
    return True


def check_package(package_name, import_name=None):
    """Check if a package is installed."""
    if import_name is None:
        import_name = package_name
        
    spec = importlib.util.find_spec(import_name)
    if spec is None:
        print(f"❌ {package_name} is not installed")
        return False
    else:
        print(f"✅ {package_name} is available")
        return True


def install_requirements():
    """Install required packages."""
    print("\n🔧 Installing required packages...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "Pillow>=8.0.0", "numpy>=1.19.0", "pyserial>=3.4"
        ])
        print("✅ All packages installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install packages")
        print("   Please install manually: pip install Pillow numpy pyserial")
        return False


def check_tkinter():
    """Check if tkinter is available."""
    try:
        import tkinter
        print("✅ tkinter is available")
        return True
    except ImportError:
        print("❌ tkinter is not available")
        print("   Please install tkinter for your Python distribution")
        return False


def run_application():
    """Run the G2burn application."""
    print("\n🚀 Starting G2burn Laser Engraver...")
    try:
        from project import Project
        app = Project()
        app.run()
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        return False
    return True


def main():
    """Main setup function."""
    print("🔥 G2burn Laser Engraver Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check tkinter
    if not check_tkinter():
        sys.exit(1)
    
    # Check required packages
    packages_ok = True
    packages_ok &= check_package("Pillow", "PIL")
    packages_ok &= check_package("numpy")
    packages_ok &= check_package("pyserial", "serial")
    
    # Install packages if needed
    if not packages_ok:
        print("\n📦 Some packages are missing")
        choice = input("Install missing packages? (y/n): ").lower().strip()
        if choice in ['y', 'yes']:
            if not install_requirements():
                sys.exit(1)
        else:
            print("❌ Cannot run without required packages")
            sys.exit(1)
    
    # Final check
    print("\n🔍 Final compatibility check...")
    try:
        from project import Project
        from sketching_stage import SketchingStage
        from drawing_tools import DrawingToolManager
        from gcode_generator import GCodeGenerator
        from grbl_controller import GRBLController
        from image_processor import ImageProcessor
        print("✅ All modules imported successfully!")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        sys.exit(1)
    
    print("\n🎉 Setup complete!")
    print("\nTo run the application:")
    print("  python3 project.py")
    print("  or")
    print("  python3 setup.py --run")
    
    # Run if requested
    if len(sys.argv) > 1 and sys.argv[1] == "--run":
        run_application()


if __name__ == "__main__":
    main()
