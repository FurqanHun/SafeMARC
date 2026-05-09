import sys
import signal

def run_gui():
    import shutil
    import os
    import tempfile
    import atexit

    # Clean up leftover temporary directories from previous crashed or aborted sessions
    safemarc_temp = os.path.join(tempfile.gettempdir(), "safemarc_temp")
    if os.path.exists(safemarc_temp):
        try:
            shutil.rmtree(safemarc_temp)
            print("[SafeMARC] Successfully cleared leftover temporary resources on startup.")
        except Exception:
            pass


    import qdarktheme
    from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton, QCheckBox, QComboBox, QTabBar, QMenu
    from PySide6.QtCore import Qt
    from src.gui.main_window import SafeMARCMainWindow

    # Monkey patch clickable widgets to default to PointingHandCursor globally
    for widget_class in [QPushButton, QCheckBox, QComboBox, QTabBar, QMenu]:
        original_init = widget_class.__init__
        def make_new_init(orig_init):
            def new_init(self, *args, **kwargs):
                orig_init(self, *args, **kwargs)
                self.setCursor(Qt.PointingHandCursor)
            return new_init
        widget_class.__init__ = make_new_init(original_init)

    # Custom SIGINT handler to explicitly quit the application and trigger RAII cleanup
    def handle_sigint(signum, frame):
        print("\n[SafeMARC] Caught Ctrl+C. Quitting event loop to trigger cleanup...")
        QApplication.quit()
        sys.exit(0)
    signal.signal(signal.SIGINT, handle_sigint)

    app = QApplication(sys.argv)
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

    # Let Python interpreter check for signals periodically
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
