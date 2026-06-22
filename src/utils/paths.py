import sys
import os

def resource_path(relative_path):
    """Get absolute path to resource, handling PyInstaller packaging."""
    try:
        # PyInstaller path lookup.
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def get_app_data_dir(app_name="SafeMARC"):
    """
    Get the appropriate application data directory across different OSes.
    Respects XDG Base Directory Specification on Linux.
    """
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        # Linux/Unix XDG standard.
        base = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    
    app_dir = os.path.join(base, app_name)
    os.makedirs(app_dir, exist_ok=True)
    return app_dir
