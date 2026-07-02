"""
Application entry point. Initializes global crash logging, configures the UI, and starts the event loop.
"""
import sys
import signal
import faulthandler
import os
import logging
from logging.handlers import RotatingFileHandler
from src.utils.paths import get_app_data_dir

try:
    log_dir = get_app_data_dir()
    log_path = os.path.join(log_dir, "safemarc.log")
    
    # Enable VT100 ANSI escape sequences on Windows 10+
    if sys.platform == "win32":
        os.system('')
        
    # C-level faulthandler
    log_file_obj = open(log_path, "a", encoding="utf-8", buffering=1)
    faulthandler.enable(file=log_file_obj)
    
    # Define custom SUCCESS level
    logging.SUCCESS = 25
    logging.addLevelName(logging.SUCCESS, 'SUCCESS')
    setattr(logging.Logger, 'success', lambda self, message, *args, **kws: self._log(logging.SUCCESS, message, args, **kws))

    class ColorFormatter(logging.Formatter):
        grey = "\x1b[38;20m"
        green = "\x1b[32;20m"
        yellow = "\x1b[33;20m"
        red = "\x1b[31;20m"
        bold_red = "\x1b[31;1m"
        cyan = "\x1b[36;20m"
        reset = "\x1b[0m"
        
        FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"

        FORMATS = {
            logging.DEBUG: cyan + FORMAT + reset,
            logging.INFO: grey + FORMAT + reset,
            logging.SUCCESS: green + FORMAT + reset,
            logging.WARNING: yellow + FORMAT + reset,
            logging.ERROR: red + FORMAT + reset,
            logging.CRITICAL: bold_red + FORMAT + reset
        }

        def format(self, record):
            log_fmt = self.FORMATS.get(record.levelno)
            formatter = logging.Formatter(log_fmt)
            return formatter.format(record)

    file_handler = RotatingFileHandler(log_path, maxBytes=10*1024*1024, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"))
    
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(ColorFormatter())
    
    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, stream_handler]
    )
    logger = logging.getLogger(__name__)

    def uncaught_exception_handler(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        
    sys.excepthook = uncaught_exception_handler

    import threading
    def thread_exception_handler(args):
        logger.critical(f"Uncaught exception in thread {args.thread.name}", exc_info=(args.exc_type, args.exc_value, args.exc_traceback))
        
    threading.excepthook = thread_exception_handler
    
    logger.info(f"Logging initialized. Logs are saved persistently to: {log_path}")
except Exception as e:
    try:
        faulthandler.enable()
    except Exception:
        pass
    print(f"[SafeMARC] Failed to initialize file logging ({e}), falling back to console.")

def run_gui():
    import shutil
    import os
    import tempfile
    import atexit

    safemarc_temp = os.path.join(tempfile.gettempdir(), "safemarc_temp")
    if os.path.exists(safemarc_temp):
        try:
            shutil.rmtree(safemarc_temp)
            print("[SafeMARC] Successfully cleared leftover temporary resources on startup.")
        except Exception:
            pass


    import qdarktheme
    from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton, QCheckBox, QComboBox, QTabBar, QMenu
    from PySide6.QtCore import Qt, QObject, QEvent
    from src.gui.main_window import SafeMARCMainWindow

    class KeyboardFocusFilter(QObject):
        def eventFilter(self, obj, event):
            from PySide6.QtWidgets import QWidget
            if isinstance(obj, QWidget):
                if event.type() == QEvent.FocusIn:
                    reason = event.reason()
                    if reason in (Qt.TabFocusReason, Qt.BacktabFocusReason, Qt.ShortcutFocusReason):
                        obj.setProperty("focused_via_keyboard", "true")
                    else:
                        obj.setProperty("focused_via_keyboard", "false")
                    obj.style().unpolish(obj)
                    obj.style().polish(obj)
                elif event.type() == QEvent.FocusOut:
                    obj.setProperty("focused_via_keyboard", "false")
                    obj.style().unpolish(obj)
                    obj.style().polish(obj)
            return super().eventFilter(obj, event)

    for widget_class in [QPushButton, QCheckBox, QComboBox, QTabBar, QMenu]:
        original_init = widget_class.__init__
        def make_new_init(orig_init):
            def new_init(self, *args, **kwargs):
                orig_init(self, *args, **kwargs)
                self.setCursor(Qt.PointingHandCursor)
            return new_init
        widget_class.__init__ = make_new_init(original_init)

    def handle_sigint(signum, frame):
        print("\n[SafeMARC] Caught Ctrl+C. Quitting event loop to trigger cleanup...")
        QApplication.quit()
        sys.exit(0)
    signal.signal(signal.SIGINT, handle_sigint)

    app = QApplication(sys.argv)
    focus_filter = KeyboardFocusFilter(app)
    app.installEventFilter(focus_filter)
    custom_style = """
    QMainWindow, QWidget#centralWidget, QSplitter, QSplitter > QWidget {
        background-color: #0B0F19;
    }
    QLabel {
        background: transparent;
        background-color: transparent;
    }
    QDialog {
        background-color: #0B0F19;
    }
    QMessageBox {
        background-color: #0B0F19;
    }
    QMessageBox QLabel {
        color: #F3F4F6;
        font-size: 13px;
        background: transparent;
    }
    QMessageBox QPushButton {
        background-color: #1F2937;
        color: #E5E7EB;
        border: 1px solid #374151;
        border-radius: 8px;
        padding: 6px 14px;
        font-weight: 600;
        font-size: 13px;
        min-width: 80px;
    }
    QMessageBox QPushButton:hover {
        background-color: #374151;
        border-color: #4B5563;
        color: #FFFFFF;
    }
    QMessageBox QPushButton:focus {
        background-color: #374151;
        border-color: #10B981;
        color: #FFFFFF;
    }
    """
    app.setStyleSheet(qdarktheme.load_stylesheet() + custom_style)
    window = SafeMARCMainWindow()
    window.show()
    window.setFocus()

    import shutil
    import os
    tess_path = shutil.which("tesseract")
    if not tess_path:
        if os.name == "nt":
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
                tess_path = path
                break
            
    if not tess_path:
        QMessageBox.warning(
            window,
            "Missing Dependency",
            "Tesseract OCR is missing.\n\nLinux: sudo dnf install tesseract\nWindows: Download Installer",
        )

    # Periodically wake event loop to process system signals.
    from PySide6.QtCore import QTimer
    timer = QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Caught KeyboardInterrupt. Exiting cleanly...")
    finally:
        if os.path.exists(safemarc_temp):
            try:
                shutil.rmtree(safemarc_temp)
                logging.getLogger(__name__).debug("RAII Guard: Successfully cleared temporary resources on termination.")
            except Exception:
                pass

if __name__ == "__main__":
    import argparse
    from src.version import __version__
    import logging

    parser = argparse.ArgumentParser(description="SafeMARC")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--debug", action="store_true", help="Enable enhanced debug logging")
    
    args, unknown = parser.parse_known_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger(__name__).debug("Enhanced debug logging enabled.")
        
    run_gui()
