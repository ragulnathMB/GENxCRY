#!/usr/bin/env python3
"""
GENxCRY - AI Dataset Generator
By RN Software

Main application entry point for the image annotation and dataset generation tool.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# Add the current directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow

def main():
    """Main application entry point."""
    try:
        # Create the main window
        root = tk.Tk()
        root.title("GENxCRY - Artificial Image Dataset Generator by RN Software")
        root.geometry("1200x800")
        root.minsize(800, 600)
        
        # Set the application icon (if available)
        try:
            root.iconbitmap("assets/icon.ico")
        except:
            pass  # Icon file not found, continue without it
        
        # Create and start the main application
        app = MainWindow(root)
        
        # Start the GUI event loop
        root.mainloop()
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start application: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
