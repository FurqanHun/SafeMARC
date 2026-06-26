import sys
import os
import contextlib
from typing import Generator

@contextlib.contextmanager
def pytesseract_env() -> Generator[None, None, None]:
    """Context manager to temporarily restore the original LD_LIBRARY_PATH for Tesseract subprocesses."""
    import shutil
    import pytesseract
    
    if not shutil.which("tesseract"):
        if sys.platform == "win32":
            default_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            ]
        elif sys.platform == "darwin":
            default_paths = [
                "/opt/homebrew/bin/tesseract",
                "/usr/local/bin/tesseract",
                "/opt/local/bin/tesseract",
            ]
        else:
            default_paths = [
                "/usr/bin/tesseract",
                "/usr/local/bin/tesseract",
            ]
        for path in default_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                break

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

def resource_path(relative_path: str) -> str:
    """Get absolute path to resource, handling PyInstaller packaging."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def get_app_data_dir(app_name: str = "SafeMARC") -> str:
    """
    Get the appropriate application data directory across different OSes.
    Respects XDG Base Directory Specification on Linux.
    """
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    
    app_dir = os.path.join(base, app_name)
    os.makedirs(app_dir, exist_ok=True)
    return app_dir
