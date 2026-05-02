import sys
import signal

def run_gui():
    import qdarktheme
    from PySide6.QtWidgets import QApplication, QMessageBox
    from src.gui.main_window import SafeMARCMainWindow

    # Allow Ctrl+C to terminate application
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    app.setStyleSheet(qdarktheme.load_stylesheet())
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

    sys.exit(app.exec())

def run_cli():
    from src.cli.cli import main
    main()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_cli()
    else:
        run_gui()
