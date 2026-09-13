import os
import sys
import tkinter as tk

def get_icon_path():
    """
    Resolve the absolute path to the assets/devo.ico file.
    Accounts for PyInstaller's _MEIPASS environment.
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        # Check both root _MEIPASS and _internal/assets for PyInstaller 6+
        path_internal = os.path.join(sys._MEIPASS, '_internal', 'assets', 'devo.ico')
        if os.path.exists(path_internal):
            return path_internal
        return os.path.join(sys._MEIPASS, 'assets', 'devo.ico')
        
    # Running in normal Python environment
    # Go up from src/utils/app_utils.py -> src/utils -> src -> devo root -> assets/devo.ico
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_dir, 'assets', 'devo.ico')

def set_app_icon(window):
    """
    Apply the custom devo.ico icon to a tkinter window and its children.
    """
    icon_path = get_icon_path()
    if os.path.exists(icon_path):
        try:
            window.iconbitmap(default=icon_path)
        except Exception:
            pass
