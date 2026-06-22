import sys
import signal
import faulthandler
import os
import logging
from src.utils.paths import get_app_data_dir

class TeeStream:
    def __init__(self, original_stream, log_file):
        self.original_stream = original_stream
        self.log_file = log_file

    def write(self, data):
        self.original_stream.write(data)
        try:
            self.log_file.write(data)
            self.log_file.flush()
        except Exception:
            pass

    def flush(self):
        self.original_stream.flush()
        try:
            self.log_file.flush()
        except Exception:
            pass

# Initialize logging and faulthandler
try:
    log_dir = get_app_data_dir()
    log_path = os.path.join(log_dir, "safemarc.log")
    log_file_obj = open(log_path, "w", encoding="utf-8", buffering=1)
    
    # Enable faulthandler to write directly to the log file on segfault
    faulthandler.enable(file=log_file_obj)
    
    # Redirect stdout and stderr to both console and the log file
    sys.stdout = TeeStream(sys.stdout, log_file_obj)
    sys.stderr = TeeStream(sys.stderr, log_file_obj)
    
    # Capture uncaught exceptions in main thread
    def uncaught_exception_handler(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        import traceback
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        sys.stderr.write("".join(tb_lines) + "\n")
    sys.excepthook = uncaught_exception_handler

    # Capture uncaught exceptions in background threads
    import threading
    def thread_exception_handler(args):
        import traceback
        tb_lines = traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback)
        sys.stderr.write(f"Uncaught exception in thread {args.thread.name}:\n" + "".join(tb_lines) + "\n")
    threading.excepthook = thread_exception_handler
    
    print(f"[SafeMARC] Logging initialized. Logs are saved persistently to: {log_path}")
except Exception as e:
    faulthandler.enable()
    print(f"[SafeMARC] Failed to initialize file logging ({e}), falling back to console.")

def run_gui():
    import shutil
    import os
    import tempfile
    import atexit

    # Clean up leftover temporary directories.
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

    # Monkey patch clickable widgets to default to PointingHandCursor.
    for widget_class in [QPushButton, QCheckBox, QComboBox, QTabBar, QMenu]:
        original_init = widget_class.__init__
        def make_new_init(orig_init):
            def new_init(self, *args, **kwargs):
                orig_init(self, *args, **kwargs)
                self.setCursor(Qt.PointingHandCursor)
            return new_init
        widget_class.__init__ = make_new_init(original_init)

    # Handle SIGINT cleanly.
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
    if not tess_path and os.name == "nt":
        default_win_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if os.path.exists(default_win_path):
            tess_path = default_win_path
            
    if not tess_path:
        QMessageBox.warning(
            window,
            "Missing Dependency",
            "Tesseract OCR is missing.\n\nLinux: sudo dnf install tesseract\nWindows: Download Installer",
        )

    # Let Python interpreter check for signals periodically.
    from PySide6.QtCore import QTimer
    timer = QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\n[SafeMARC] Caught KeyboardInterrupt. Exiting cleanly...")
    finally:
        if os.path.exists(safemarc_temp):
            try:
                shutil.rmtree(safemarc_temp)
                print("[SafeMARC] RAII Guard: Successfully cleared temporary resources on termination.")
            except Exception:
                pass

def run_cli():
    from src.cli.cli import main
    main()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_cli()
    else:
        run_gui()
