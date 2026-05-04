import sys
import signal

def run_gui():
    import qdarktheme
    from PySide6.QtWidgets import QApplication, QMessageBox
    from src.gui.main_window import SafeMARCMainWindow

    # Allow Ctrl+C to terminate application
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    custom_style = """
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

    sys.exit(app.exec())

def run_cli():
    from src.cli.cli import main
    main()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_cli()
    else:
        run_gui()
