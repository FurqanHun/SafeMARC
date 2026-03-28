import os
import shutil
import sys

import qdarktheme
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.core.scanner import SafeScanner


class SafeMARC(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SafeMARC - v0.1 (Dev)")
        self.setGeometry(100, 100, 600, 400)

        # 1. Initialize the Engine
        try:
            self.scanner = SafeScanner()
            engine_status = "AI Engine: Online"
        except Exception as e:
            self.scanner = None
            engine_status = f"AI Engine Error: {e}"

        # 2. Main Layout Setup
        layout = QVBoxLayout()

        self.title_label = QLabel("SafeMARC")
        self.title_label.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #4CAF50;"
        )
        layout.addWidget(self.title_label)

        self.status_label = QLabel(engine_status)
        layout.addWidget(self.status_label)

        self.tess_label = QLabel(self.check_tesseract())
        layout.addWidget(self.tess_label)

        # 3. The File Selection Area
        self.file_path_label = QLabel("No file selected.")
        self.file_path_label.setStyleSheet("color: #aaaaaa; font-style: italic;")
        layout.addWidget(self.file_path_label)

        self.btn_select = QPushButton("📁 Select Document")
        self.btn_select.clicked.connect(self.select_file)
        layout.addWidget(self.btn_select)

        # 4. The Action Button (Disabled by default)
        self.btn_redact = QPushButton("🛡️ Redact Document")
        self.btn_redact.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.btn_redact.setEnabled(False)  # Disabled until image is picked
        self.btn_redact.clicked.connect(self.run_redaction)
        layout.addWidget(self.btn_redact)

        # Container
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # State Variable to hold the picked image path
        self.current_image_path = None

    def check_tesseract(self):
        tess_path = shutil.which("tesseract")
        if not tess_path and os.name == "nt":
            default_win_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            if os.path.exists(default_win_path):
                tess_path = default_win_path
        if tess_path:
            return f"Tesseract Found: {tess_path}"
        else:
            return "Tesseract NOT FOUND! (Install it or add to PATH)"

    def select_file(self):
        """Opens the file picker for the user to choose an image."""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Image to Redact", "", "Images (*.png *.jpg *.jpeg)"
        )

        if file_name:
            self.current_image_path = file_name
            # Update UI
            self.file_path_label.setText(f"Selected: {file_name}")
            self.btn_redact.setEnabled(True)
            self.btn_redact.setStyleSheet(
                "font-size: 16px; font-weight: bold; background-color: #b71c1c; color: white;"
            )

    def run_redaction(self):
        """Executes the scan and redact logic."""
        if not self.scanner or not self.current_image_path:
            return

        self.btn_redact.setText("Processing... Please wait.")
        self.btn_redact.setEnabled(False)
        QApplication.processEvents()  # Force UI to update text before freezing

        # Generate output path
        base, ext = os.path.splitext(self.current_image_path)
        output_path = f"{base}_redacted{ext}"

        # THE CORE LOGIC
        try:
            hits = self.scanner.scan(self.current_image_path)

            if not hits:
                QMessageBox.information(
                    self, "Result", "No sensitive data found in this image."
                )
            else:
                success = self.scanner.redact(
                    self.current_image_path, output_path, hits
                )
                if success:
                    QMessageBox.information(
                        self,
                        "Success!",
                        f"Redacted {len(hits)} items.\n\nSaved to:\n{output_path}",
                    )
                else:
                    QMessageBox.warning(self, "Error", "Failed to save redacted image.")
        except Exception as e:
            QMessageBox.critical(
                self, "Crash", f"An error occurred during scanning:\n{e}"
            )

        # Reset button state
        self.btn_redact.setText("🛡️ Redact Document")
        self.btn_redact.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarktheme.load_stylesheet())
    window = SafeMARC()
    window.show()

    if "NOT FOUND" in window.tess_label.text():
        QMessageBox.warning(
            window,
            "Missing Dependency",
            "Tesseract OCR is missing.\n\nLinux: sudo dnf install tesseract\nWindows: Download Installer",
        )

    sys.exit(app.exec())
