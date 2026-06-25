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
        if self.original_stream is not None:
            try:
                self.original_stream.write(data)
            except Exception:
                pass
        try:
            self.log_file.write(data)
            self.log_file.flush()
        except Exception:
            pass

    def flush(self):
        if self.original_stream is not None:
            try:
                self.original_stream.flush()
            except Exception:
                pass
        try:
            self.log_file.flush()
        except Exception:
            pass

    def fileno(self):
        if self.original_stream is not None and hasattr(self.original_stream, 'fileno'):
            try:
                return self.original_stream.fileno()
            except Exception:
                pass
        if self.log_file is not None and hasattr(self.log_file, 'fileno'):
            try:
                return self.log_file.fileno()
            except Exception:
                pass
        raise AttributeError("TeeStream object has no attribute 'fileno'")

original_stdout = sys.stdout
original_stderr = sys.stderr

try:
    log_dir = get_app_data_dir()
    log_path = os.path.join(log_dir, "safemarc.log")
    log_file_obj = open(log_path, "w", encoding="utf-8", buffering=1)
    
    # Write C-level segfaults directly to the log file.
    faulthandler.enable(file=log_file_obj)
    
    sys.stdout = TeeStream(sys.stdout, log_file_obj)
    sys.stderr = TeeStream(sys.stderr, log_file_obj)
    
    def uncaught_exception_handler(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        import traceback
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        sys.stderr.write("".join(tb_lines) + "\n")
    sys.excepthook = uncaught_exception_handler

    import threading
    def thread_exception_handler(args):
        import traceback
        tb_lines = traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback)
        sys.stderr.write(f"Uncaught exception in thread {args.thread.name}:\n" + "".join(tb_lines) + "\n")
    threading.excepthook = thread_exception_handler
    
    print(f"[SafeMARC] Logging initialized. Logs are saved persistently to: {log_path}")
except Exception as e:
    sys.stdout = original_stdout
    sys.stderr = original_stderr
    try:
        faulthandler.enable()
    except Exception:
        pass
    if sys.stdout is not None and hasattr(sys.stdout, "write"):
        try:
            print(f"[SafeMARC] Failed to initialize file logging ({e}), falling back to console.")
        except Exception:
            pass

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
