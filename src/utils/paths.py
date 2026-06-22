import sys
import os
import contextlib

@contextlib.contextmanager
def pytesseract_env():
    """Context manager to temporarily restore the original LD_LIBRARY_PATH for Tesseract subprocesses."""
    is_frozen = getattr(sys, 'frozen', False)
    original_env = os.environ.copy()
    try:
        if is_frozen:
            lp_orig = os.environ.get('LD_LIBRARY_PATH_ORIG')
            if lp_orig is not None:
                os.environ['LD_LIBRARY_PATH'] = lp_orig
            else:
                os.environ.pop('LD_LIBRARY_PATH', None)
        yield
    finally:
        if is_frozen:
            os.environ.clear()
            os.environ.update(original_env)

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
