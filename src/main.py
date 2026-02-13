import os
import shutil
import sys

from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

# Check imports from structure
try:
    import core
    import utils

    STRUCTURE_CHECK = "Project Structure: OK"
except ImportError as e:
    STRUCTURE_CHECK = f"Structure Error: {e}"


class SafeMARC(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SafeMARC - v0.1 (Dev)")
        self.setGeometry(100, 100, 600, 400)

        # Main Layout
        layout = QVBoxLayout()

        self.label = QLabel("SafeMARC is Online")
        self.label.setStyleSheet("font-size: 24px; font-weight: bold; color: #4CAF50;")
        layout.addWidget(self.label)

        # Structure Check
        self.struct_label = QLabel(STRUCTURE_CHECK)
        layout.addWidget(self.struct_label)

        # Tesseract Check (The Windows Trap)
        self.tess_label = QLabel(self.check_tesseract())
        layout.addWidget(self.tess_label)

        # Container
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def check_tesseract(self):
        """Checks if Tesseract is installed and reachable."""
        # Check PATH (Linux/Fedora mostly)
        tess_path = shutil.which("tesseract")

        if not tess_path and os.name == "nt":
            default_win_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            if os.path.exists(default_win_path):
                tess_path = default_win_path

        if tess_path:
            return f"Tesseract Found: {tess_path}"
        else:
            return "Tesseract NOT FOUND! (Install it or add to PATH)"


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SafeMARC()
    window.show()

    # Check Tesseract explicitly on launch and warn if missing
    if "NOT FOUND" in window.tess_label.text():
        QMessageBox.warning(
            window,
            "Missing Dependency",
            "Tesseract OCR is missing.\n\nLinux: sudo dnf install tesseract\nWindows: Download Installer",
        )

    sys.exit(app.exec())
