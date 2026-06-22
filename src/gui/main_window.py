import os
import qdarktheme
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QListWidget,
    QSplitter,
    QCheckBox,
    QGroupBox,
    QListWidgetItem,
    QProgressDialog,
    QComboBox,
    QLineEdit,
    QScrollArea,
    QDialog,
    QRadioButton,
    QButtonGroup,
    QGridLayout,
)
from PySide6.QtCore import Qt, QSize, QTimer, QThread, Signal, QEvent, QObject
from PySide6.QtGui import QFont, QIcon, QColor, QKeySequence

from src.core.scanner import SafeScanner
from src.core.batch_processor import BatchProcessor, SUPPORTED_EXTENSIONS
from src.utils.pdf_handler import PDFHandler
from src.gui.preview_widget import PreviewWidget
from src.gui.settings_dialog import SettingsDialog
from src.utils.paths import resource_path
from PySide6.QtWidgets import QFrame
import platform
import sys

class ClickableStatusLabel(QLabel):
    clicked = Signal()

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class EngineStatusDialog(QDialog):
    def __init__(self, scanner, parent=None):
        super().__init__(parent)
        import cv2
        import mediapipe as mp
        import PySide6
        
        self.setWindowTitle("SafeMARC Engine Status")
        self.resize(500, 480)
        self.setStyleSheet("""
            QDialog {
                background-color: #0B0F19;
                color: #F3F4F6;
            }
            QLabel {
                color: #F3F4F6;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title_label = QLabel("System & AI Engine Status")
        title_label.setStyleSheet("font-size: 18px; font-weight: 700; color: #10B981;")
        layout.addWidget(title_label)
        
        def create_card():
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: #111827;
                    border: 1px solid #374151;
                    border-radius: 10px;
                }
                QLabel {
                    border: none;
                    background-color: transparent;
                }
            """)
            return card
            
        # Section 1: Application Version & Environment
        env_card = create_card()
        env_layout = QVBoxLayout(env_card)
        env_layout.setContentsMargins(15, 12, 15, 12)
        env_layout.setSpacing(6)
        
        env_title = QLabel("Environment Information")
        env_title.setStyleSheet("font-weight: 700; color: #9CA3AF; font-size: 12px; text-transform: uppercase;")
        env_layout.addWidget(env_title)
        
        try:
            from src.version import __version__ as app_ver
        except ImportError:
            app_ver = "0.1.0"
            
        is_dev = "dev" in app_ver.lower() or app_ver == "0.1.0"
        ver_suffix = " (DEV)" if is_dev else ""
        
        env_layout.addWidget(QLabel(f"<b>Application Version:</b> {app_ver}{ver_suffix}"))
        env_layout.addWidget(QLabel(f"<b>Python Version:</b> {platform.python_version()}"))
        env_layout.addWidget(QLabel(f"<b>Platform / OS:</b> {platform.system()} {platform.machine()} ({platform.release()})"))
        env_layout.addWidget(QLabel(f"<b>PySide6 Version:</b> {PySide6.__version__ if hasattr(PySide6, '__version__') else '6.x'}"))
        env_layout.addWidget(QLabel(f"<b>OpenCV Version:</b> {cv2.__version__}"))
        env_layout.addWidget(QLabel(f"<b>MediaPipe Version:</b> {mp.__version__}"))
        
        layout.addWidget(env_card)
        
        # Section 2: Model & OCR Status
        status_card = create_card()
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(15, 12, 15, 12)
        status_layout.setSpacing(10)
        
        status_title = QLabel("Model & Dependency Status")
        status_title.setStyleSheet("font-weight: 700; color: #9CA3AF; font-size: 12px; text-transform: uppercase;")
        status_layout.addWidget(status_title)
        
        # SFace Check
        sface_model_path = resource_path("assets/face_recognition_sface_2021dec.onnx")
        sface_exists = os.path.exists(sface_model_path)
        sface_active = scanner.identity_manager.use_sface if (scanner and scanner.identity_manager) else False
        
        sface_lbl = QLabel()
        if sface_active:
            sface_lbl.setText("<span style='color: #10B981;'>✔</span> <b>SFace Recognition Model:</b> Loaded (ONNX)")
        elif sface_exists:
            sface_lbl.setText("<span style='color: #FBBF24;'>⚠</span> <b>SFace Recognition Model:</b> Found, but initialization failed (Fallback to LBPH)")
        else:
            sface_lbl.setText("<span style='color: #FBBF24;'>⚠</span> <b>SFace Recognition Model:</b> Missing (Fallback to LBPH)<br><span style='color: #9CA3AF; font-size: 11px;'>To resolve, download face_recognition_sface_2021dec.onnx into assets/</span>")
        status_layout.addWidget(sface_lbl)
        
        # Body Check
        body_model_path = resource_path("assets/efficientdet_lite2.tflite")
        body_exists = os.path.exists(body_model_path)
        
        body_lbl = QLabel()
        if body_exists:
            body_lbl.setText("<span style='color: #10B981;'>✔</span> <b>Body Silhouette Model:</b> Ready (TFLite)")
        else:
            body_lbl.setText("<span style='color: #FBBF24;'>⚠</span> <b>Body Silhouette Model:</b> Missing (Full Body mode unavailable)<br><span style='color: #9CA3AF; font-size: 11px;'>To resolve, download efficientdet_lite2.tflite into assets/</span>")
        status_layout.addWidget(body_lbl)
        
        # Tesseract Check
        import pytesseract
        from src.utils.paths import pytesseract_env
        try:
            with pytesseract_env():
                tesseract_version = pytesseract.get_tesseract_version()
            has_tesseract = True
        except Exception:
            tesseract_version = "Not found"
            has_tesseract = False
            
        tess_lbl = QLabel()
        if has_tesseract:
            tess_lbl.setText(f"<span style='color: #10B981;'>✔</span> <b>Tesseract OCR:</b> Available (Version: {tesseract_version})")
        else:
            tess_lbl.setText("<span style='color: #EF4444;'>✘</span> <b>Tesseract OCR:</b> Executable not found in PATH<br><span style='color: #9CA3AF; font-size: 11px;'>Ensure Tesseract is installed and the system environment PATH variables are set.</span>")
        status_layout.addWidget(tess_lbl)
        
        layout.addWidget(status_card)
        
        # Close Button
        btn_close = QPushButton("Close")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #1F2937;
                color: #F3F4F6;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #374151;
                border-color: #4B5563;
            }
        """)
        btn_close.clicked.connect(self.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)


def svg_to_icon(svg_str: str, size: int = 16) -> QIcon:
    from PySide6.QtGui import QPainter, QImage, QPixmap
    from PySide6.QtSvg import QSvgRenderer
    renderer = QSvgRenderer(svg_str.encode('utf-8'))
    image = QImage(size, size, QImage.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    return QIcon(QPixmap.fromImage(image))

SVG_SETTINGS = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#F3F4F6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.38a2 2 0 0 0-.73-2.73l-.15-.1a2 2 0 0 1-1-1.72v-.51a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>'''

SVG_FILE_PLUS = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E5E7EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M9 15h6"/><path d="M12 12v6"/></svg>'''

SVG_FOLDER_PLUS = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E5E7EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20V6a2 2 0 0 1 2-2h4l2 3h6a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z"/><path d="M12 11v6"/><path d="M9 14h6"/></svg>'''

SVG_TRASH = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E5E7EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>'''

SVG_X_CIRCLE = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E5E7EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/></svg>'''

SVG_PLAY = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="6 3 20 12 6 21 6 3"/></svg>'''

SVG_ARROW_LEFT = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E5E7EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>'''

SVG_ARROW_RIGHT = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E5E7EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>'''

SVG_SQUARE = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E5E7EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"/></svg>'''

SVG_DRAW = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E5E7EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.375 2.625a2.121 2.121 0 1 1 3 3L12 15l-4 1 1-4Z"/></svg>'''

SVG_ZOOM_IN = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E5E7EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/></svg>'''

SVG_ZOOM_OUT = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E5E7EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="8" y1="11" x2="14" y2="11"/></svg>'''
SVG_ZOOM_RESET = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E5E7EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3H5a2 2 0 0 0-2 2v3"/><path d="M21 8V5a2 2 0 0 0-2-2h-3"/><path d="M3 16v3a2 2 0 0 0 2 2h3"/><path d="M16 21h3a2 2 0 0 0 2-2v-3"/><rect width="10" height="10" x="7" y="7" rx="1"/></svg>'''

SVG_REFRESH = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E5E7EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 21v-5h5"/></svg>'''
SVG_CLIPBOARD = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E5E7EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/></svg>'''
SVG_FACE = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E5E7EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'''
SVG_PIN = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E5E7EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="17" x2="12" y2="22"/><path d="M5 17h14v-1.76a2 2 0 0 0-.44-1.24l-2.12-2.12a2 2 0 0 1-.44-1.24V5a2 2 0 0 0-2-2H9a2 2 0 0 0-2 2v5.64a2 2 0 0 1-.44 1.24l-2.12 2.12a2 2 0 0 0-.44 1.24Z"/></svg>'''


class PatternLineEdit(QLineEdit):
    def __init__(self, is_regex, parent_window, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_regex = is_regex
        self.parent_window = parent_window

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() & Qt.ShiftModifier:
                self.parent_window.add_pattern_row(is_regex=self.is_regex)
                QTimer.singleShot(50, self.parent_window.focus_last_pattern_field)
                return
            else:
                self.clearFocus()
                return
        super().keyPressEvent(event)


class ScanWorker(QThread):
    finished = Signal()
    error = Signal(Exception)

    def __init__(self, scanner, file_path, pdf_words=None, cache_key=None):
        super().__init__()
        self.scanner = scanner
        self.file_path = file_path
        self.pdf_words = pdf_words
        self.cache_key = cache_key
        self.hits = []

    def run(self):
        try:
            self.hits = self.scanner.scan(self.file_path, pdf_words=self.pdf_words, cache_key=self.cache_key)
            self.finished.emit()
        except Exception as e:
            self.error.emit(e)


def apply_focus_indicators(parent):
    from PySide6.QtWidgets import QWidget, QPushButton, QCheckBox, QComboBox, QLineEdit, QListWidget, QSlider, QRadioButton
    for child in parent.findChildren(QWidget):
        style = child.styleSheet() or ""
        focus_style = ""
        if isinstance(child, QPushButton):
            focus_style = "\nQPushButton[focused_via_keyboard=\"true\"] { border: 2px solid #10B981; outline: none; }"
        elif isinstance(child, QCheckBox):
            focus_style = "\nQCheckBox[focused_via_keyboard=\"true\"] { color: #FFFFFF; }\nQCheckBox[focused_via_keyboard=\"true\"]::indicator { border: 2px solid #10B981; outline: none; }"
        elif isinstance(child, QComboBox):
            focus_style = "\nQComboBox[focused_via_keyboard=\"true\"] { border: 2px solid #10B981; outline: none; }"
        elif isinstance(child, QLineEdit):
            focus_style = "\nQLineEdit[focused_via_keyboard=\"true\"] { border: 2px solid #10B981; outline: none; }"
        elif isinstance(child, QListWidget):
            focus_style = "\nQListWidget[focused_via_keyboard=\"true\"] { border: 2px solid #10B981; outline: none; }"
        elif isinstance(child, QSlider):
            focus_style = "\nQSlider[focused_via_keyboard=\"true\"] { outline: none; }\nQSlider[focused_via_keyboard=\"true\"]::handle:horizontal { border: 2px solid #FFFFFF; background: #10B981; }"
        elif isinstance(child, QRadioButton):
            focus_style = "\nQRadioButton[focused_via_keyboard=\"true\"] { color: #FFFFFF; }\nQRadioButton[focused_via_keyboard=\"true\"]::indicator { border: 2px solid #10B981; outline: none; }"
            
        if focus_style:
            child.setStyleSheet(style + focus_style)


class QuickAddIdentityDialog(QDialog):
    def __init__(self, existing_names, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Identity")
        self.setFixedSize(360, 180)
        self.setStyleSheet("""
            QDialog { background-color: #0B0F19; }
            QLabel { color: #E5E7EB; font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; }
            QComboBox {
                background-color: #1F2937;
                color: #F3F4F6;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QComboBox:focus { border-color: #10B981; }
            QComboBox QAbstractItemView {
                background-color: #1F2937;
                color: #F3F4F6;
                selection-background-color: #10B981;
                selection-color: #FFFFFF;
                border: 1px solid #374151;
            }
            QPushButton {
                background-color: #1F2937;
                color: #E5E7EB;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #374151; border-color: #4B5563; color: #FFFFFF; }
            QPushButton#btnSave { background-color: #10B981; color: white; border: none; }
            QPushButton#btnSave:hover { background-color: #059669; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        lbl = QLabel("Select or enter name for this face:")
        
        self.combo_name = QComboBox()
        self.combo_name.setEditable(True)
        self.combo_name.addItems(existing_names)
        self.combo_name.setCurrentText("")
        
        from PySide6.QtWidgets import QCompleter
        completer = QCompleter(existing_names, self)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.combo_name.setCompleter(completer)
        
        # Ensure the line edit styling matches
        if self.combo_name.lineEdit():
            self.combo_name.lineEdit().setStyleSheet("""
                background-color: #1F2937;
                color: #F3F4F6;
                border: none;
            """)
            self.combo_name.lineEdit().setPlaceholderText("e.g. John Doe")
            self.combo_name.lineEdit().returnPressed.connect(self._on_save)
            
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_save = QPushButton("Save")
        self.btn_save.setObjectName("btnSave")
        self.btn_save.setDefault(True)
        self.btn_save.clicked.connect(self._on_save)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        
        layout.addWidget(lbl)
        layout.addWidget(self.combo_name)
        layout.addLayout(btn_layout)
        
        apply_focus_indicators(self)
        
    def _on_save(self):
        name = self.get_name()
        if not name:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Invalid Name", "Please enter or select a valid identity name.")
            return
        self.accept()
        
    def get_name(self):
        return self.combo_name.currentText().strip()


class FocusEventFilter(QObject):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window

    def eventFilter(self, obj, event):
        if event is not None:
            if event.type() == QEvent.FocusIn:
                try:
                    from PySide6.QtWidgets import QLineEdit, QTextEdit, QPlainTextEdit
                    if isinstance(obj, (QLineEdit, QTextEdit, QPlainTextEdit)):
                        self.main_window.set_shortcuts_enabled(False)
                    else:
                        self.main_window.set_shortcuts_enabled(True)
                except Exception:
                    pass
        return super().eventFilter(obj, event)


class SafeMARCMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SafeMARC - v0.1 (DEV)")
        avail = QApplication.primaryScreen().availableGeometry()
        w = min(int(avail.width() * 0.85), 1400)
        h = min(int(avail.height() * 0.85), 800)
        x = avail.x() + (avail.width() - w) // 2
        y = avail.y() + (avail.height() - h) // 2
        self.setGeometry(x, y, w, h)
        self.setAcceptDrops(True)

        # Load Keyboard Shortcuts Configuration
        from PySide6.QtCore import QSettings
        from src.gui.settings_dialog import DEFAULT_SHORTCUTS
        self.settings = QSettings("SafeMARC", "SafeMARC")
        self.shortcuts_config = {}
        for key, default_seq in DEFAULT_SHORTCUTS.items():
            self.shortcuts_config[key] = self.settings.value(f"shortcut_{key}", default_seq)

        # Core Engines
        sface_exists = False
        body_exists = False
        has_tesseract = False
        sface_active = False
        try:
            self.scanner = SafeScanner()
            self.processor = BatchProcessor(self.scanner)
            
            sface_model_path = resource_path("assets/face_recognition_sface_2021dec.onnx")
            sface_exists = os.path.exists(sface_model_path)
            sface_active = self.scanner.identity_manager.use_sface if (self.scanner and self.scanner.identity_manager) else False
            
            body_model_path = resource_path("assets/efficientdet_lite2.tflite")
            body_exists = os.path.exists(body_model_path)
            
            import pytesseract
            from src.utils.paths import pytesseract_env
            try:
                with pytesseract_env():
                    pytesseract.get_tesseract_version()
                has_tesseract = True
            except Exception:
                has_tesseract = False
                
            if not sface_active or not body_exists or not has_tesseract:
                engine_status = "AI Engine: Warning (Click for Info)"
                status_state = "warning"
            else:
                engine_status = "AI Engine: Online"
                status_state = "online"
        except Exception as e:
            self.scanner = None
            self.processor = None
            engine_status = "AI Engine Error"
            status_state = "error"

        # Central Widget & Main Layout
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0B0F19;
            }
            QWidget#centralWidget {
                background-color: #0B0F19;
            }
            QPushButton:focus {
                border: 2px solid #10B981 !important;
                outline: none;
            }
            QCheckBox:focus {
                color: #FFFFFF !important;
            }
            QCheckBox::indicator:focus {
                border: 2px solid #10B981 !important;
                outline: none;
            }
            QComboBox:focus {
                border: 2px solid #10B981 !important;
                outline: none;
            }
            QListWidget:focus {
                border: 2px solid #10B981 !important;
                outline: none;
            }
            QSlider:focus {
                outline: none;
            }
            QLineEdit:focus {
                border: 2px solid #10B981 !important;
                outline: none;
            }
        """)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Header
        header_layout = QHBoxLayout()
        self.title_label = QLabel("SafeMARC")
        self.title_label.setStyleSheet(
            "font-size: 26px; font-weight: 800; color: #10B981; letter-spacing: 0.5px; font-family: 'Segoe UI', Arial, sans-serif;"
        )
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        self.status_label = ClickableStatusLabel(engine_status)
        self.status_label.clicked.connect(self._show_engine_status_popup)
        if status_state == "online":
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #064E3B;
                    color: #34D399;
                    border: 1px solid #047857;
                    border-radius: 12px;
                    padding: 4px 12px;
                    font-size: 11px;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    margin-right: 8px;
                }
            """)
        elif status_state == "warning":
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #451A03;
                    color: #FBBF24;
                    border: 1px solid #78350F;
                    border-radius: 12px;
                    padding: 4px 12px;
                    font-size: 11px;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    margin-right: 8px;
                }
            """)
        else:
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #7F1D1D;
                    color: #FCA5A5;
                    border: 1px solid #B91C1C;
                    border-radius: 12px;
                    padding: 4px 12px;
                    font-size: 11px;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    margin-right: 8px;
                }
            """)
        header_layout.addWidget(self.status_label)
        
        self.btn_settings = QPushButton(" Settings")
        self.btn_settings.setIcon(svg_to_icon(SVG_SETTINGS))
        self.btn_settings.setStyleSheet("""
            QPushButton {
                background-color: #1F2937;
                color: #F3F4F6;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 6px 14px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #374151;
                border-color: #4B5563;
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background-color: #111827;
            }
        """)
        self.btn_settings.clicked.connect(self.open_settings)
        header_layout.addWidget(self.btn_settings)
        
        main_layout.addLayout(header_layout)

        # Splitter for sidebar and preview
        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter, 1)

        # === Sidebar (File Queue & Settings) ===
        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        # File Queue
        self.file_list = QListWidget()
        self.file_list.setStyleSheet("""
            QListWidget {
                background-color: #111827;
                border: 1px solid #374151;
                border-radius: 10px;
                padding: 8px;
                font-size: 13px;
                color: #F3F4F6;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-radius: 6px;
                margin-bottom: 4px;
            }
            QListWidget::item:hover {
                background-color: #1F2937;
                color: #FFFFFF;
            }
            QListWidget::item:selected {
                background-color: #0D9488;
                color: #FFFFFF;
                font-weight: 600;
            }
        """)
        self.file_list.itemClicked.connect(self.on_file_selected)
        
        queue_header = QHBoxLayout()
        lbl_queue = QLabel("Queue")
        lbl_queue.setStyleSheet("font-size: 13px; font-weight: 700; color: #9CA3AF; margin-top: 5px; margin-left: 2px; text-transform: uppercase; letter-spacing: 0.5px;")
        self.lbl_count = QLabel("Files: 0")
        self.lbl_count.setStyleSheet("font-size: 11px; color: #6B7280; margin-top: 8px; margin-right: 5px;")
        queue_header.addWidget(lbl_queue)
        queue_header.addStretch()
        queue_header.addWidget(self.lbl_count)
        
        sidebar_layout.addLayout(queue_header)
        
        self.txt_queue_search = QLineEdit()
        self.txt_queue_search.setPlaceholderText("Search queue...")
        self.txt_queue_search.setStyleSheet("""
            QLineEdit {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 6px 10px;
                color: #E5E7EB;
                font-size: 13px;
                font-family: 'Segoe UI', Arial, sans-serif;
                margin-top: 4px;
                margin-bottom: 4px;
            }
            QLineEdit:focus {
                border-color: #10B981;
            }
        """)
        self.txt_queue_search.textChanged.connect(self._filter_queue_list)
        self.txt_queue_search.setVisible(False)
        sidebar_layout.addWidget(self.txt_queue_search)
        
        sidebar_layout.addWidget(self.file_list, 1)

        # Queue Buttons
        self.btn_add_file = QPushButton(" Add Files")
        self.btn_add_file.setIcon(svg_to_icon(SVG_FILE_PLUS))
        self.btn_add_file.clicked.connect(self.add_files)
        
        self.btn_add_folder = QPushButton(" Add Folder")
        self.btn_add_folder.setIcon(svg_to_icon(SVG_FOLDER_PLUS))
        self.btn_add_folder.clicked.connect(self.add_folder)
        
        self.btn_remove = QPushButton(" Remove")
        self.btn_remove.setIcon(svg_to_icon(SVG_X_CIRCLE))
        self.btn_remove.clicked.connect(self.remove_selected_file)
        
        self.btn_clear = QPushButton(" Clear")
        self.btn_clear.setIcon(svg_to_icon(SVG_TRASH))
        self.btn_clear.clicked.connect(self.clear_queue)
        
        self.btn_paste = QPushButton(" Paste")
        self.btn_paste.setIcon(svg_to_icon(SVG_CLIPBOARD))
        self.btn_paste.clicked.connect(self.on_paste)
        self.btn_paste.setToolTip("Paste image from clipboard (Ctrl+V)")
        
        btn_style = """
            QPushButton {
                background-color: #1F2937;
                color: #E5E7EB;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 6px 8px;
                font-weight: 600;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #374151;
                border-color: #4B5563;
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background-color: #111827;
            }
            QPushButton:disabled {
                background-color: #111827;
                color: #4B5563;
                border-color: #1F2937;
            }
        """
        
        for btn in (self.btn_add_file, self.btn_add_folder, self.btn_paste, self.btn_remove, self.btn_clear):
            btn.setStyleSheet(btn_style)
        
        queue_btns_container = QVBoxLayout()
        queue_btns_container.setSpacing(6)
        
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(6)
        row1_layout.setContentsMargins(0, 0, 0, 0)
        row1_layout.addWidget(self.btn_add_file)
        row1_layout.addWidget(self.btn_add_folder)
        
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(6)
        row2_layout.setContentsMargins(0, 0, 0, 0)
        row2_layout.addWidget(self.btn_paste)
        row2_layout.addWidget(self.btn_remove)
        row2_layout.addWidget(self.btn_clear)
        
        queue_btns_container.addLayout(row1_layout)
        queue_btns_container.addLayout(row2_layout)
        sidebar_layout.addLayout(queue_btns_container)

        # Settings Group (Styled Card instead of native GroupBox)
        settings_card = QWidget()
        settings_card.setObjectName("settingsCard")
        settings_card.setStyleSheet("""
            QWidget#settingsCard {
                background-color: #111827;
                border: 1px solid #374151;
                border-radius: 10px;
                margin-top: 10px;
            }
            QWidget#settingsCard QLabel, QWidget#settingsCard QCheckBox {
                background: transparent;
            }
        """)
        settings_layout = QVBoxLayout(settings_card)
        settings_layout.setContentsMargins(14, 14, 14, 14)
        settings_layout.setSpacing(10)
        
        lbl_settings_title = QLabel("VISION SETTINGS")
        lbl_settings_title.setStyleSheet("font-weight: 700; font-size: 11px; color: #10B981; letter-spacing: 0.5px; text-transform: uppercase;")
        settings_layout.addWidget(lbl_settings_title)

        # Vision Mode Dropdown
        self.cmb_vision_mode = QComboBox()
        self.cmb_vision_mode.addItem("Faces Only", "faces")
        self.cmb_vision_mode.addItem("Full Body", "bodies")
        self.cmb_vision_mode.addItem("Text Only", "text")
        self.cmb_vision_mode.currentIndexChanged.connect(self.on_vision_mode_changed)
        
        combo_style = """
            QComboBox {
                background-color: #1F2937;
                color: #F3F4F6;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 5px 10px;
                font-size: 13px;
                min-width: 130px;
            }
            QComboBox:hover {
                border-color: #4B5563;
            }
            QComboBox::drop-down {
                border: 0;
            }
            QComboBox QAbstractItemView {
                background-color: #1F2937;
                border: 1px solid #374151;
                color: #F3F4F6;
                selection-background-color: #0D9488;
                outline: 0;
            }
        """
        self.cmb_vision_mode.setStyleSheet(combo_style)
        
        mode_layout = QHBoxLayout()
        lbl_vision_target = QLabel("Vision Target:")
        lbl_vision_target.setStyleSheet("font-weight: bold; color: #9CA3AF;")
        mode_layout.addWidget(lbl_vision_target)
        mode_layout.addWidget(self.cmb_vision_mode)
        settings_layout.addLayout(mode_layout)

        self.cmb_face_mode = QComboBox()
        self.cmb_face_mode.addItems(["All", "Blacklist", "Whitelist"])
        self.cmb_face_mode.setStyleSheet(combo_style)
        self.cmb_face_mode.currentTextChanged.connect(self._update_face_mode)
        
        face_mode_layout = QHBoxLayout()
        lbl_face_mode = QLabel("Face Mode:")
        lbl_face_mode.setStyleSheet("font-weight: bold; color: #9CA3AF;")
        face_mode_layout.addWidget(lbl_face_mode)
        face_mode_layout.addWidget(self.cmb_face_mode)
        settings_layout.addLayout(face_mode_layout)
        
        self.btn_select_people = QPushButton(" Select People")
        self.btn_select_people.setIcon(svg_to_icon(SVG_FACE))
        self.btn_select_people.setStyleSheet("""
            QPushButton {
                background-color: #1F2937;
                color: #E5E7EB;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #374151; border-color: #4B5563; }
        """)
        self.btn_select_people.clicked.connect(self._show_people_selector)
        self.btn_select_people.hide()
        settings_layout.addWidget(self.btn_select_people)
        
        checkbox_style = """
            QCheckBox {
                spacing: 8px;
                color: #E5E7EB;
                font-size: 12px;
                padding-top: 4px;
                padding-bottom: 4px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid #374151;
                background-color: #1F2937;
            }
            QCheckBox::indicator:hover {
                border-color: #4B5563;
            }
            QCheckBox::indicator:checked {
                background-color: #10B981;
                border-color: #10B981;
            }
        """
        
        self.chk_suffix = QCheckBox("Append '_safemarc_redacted' suffix")
        self.chk_suffix.setChecked(False)  # Default uses folder
        self.chk_suffix.setToolTip("If unchecked, creates a 'safemarc_redacted_output' folder.")
        self.chk_suffix.setStyleSheet(checkbox_style)
        settings_layout.addWidget(self.chk_suffix)

        self.chk_auto_skip = QCheckBox("Auto-Skip Clean Images")
        self.chk_auto_skip.setChecked(False)
        self.chk_auto_skip.setStyleSheet(checkbox_style)
        settings_layout.addWidget(self.chk_auto_skip)

        self.chk_skip_review = QCheckBox("Skip Review (Auto-Redact)")
        self.chk_skip_review.setChecked(False)
        self.chk_skip_review.setStyleSheet(checkbox_style)
        settings_layout.addWidget(self.chk_skip_review)

        self.chk_always_rasterize = QCheckBox("Always Rasterize PDFs")
        self.chk_always_rasterize.setChecked(False)
        self.chk_always_rasterize.setToolTip("If unchecked, non-redacted PDFs are copied directly without rasterizing.")
        self.chk_always_rasterize.setStyleSheet(checkbox_style)
        settings_layout.addWidget(self.chk_always_rasterize)

        # === Right Panel (Settings & Redaction Rules) ===
        right_panel_widget = QWidget()
        right_panel_layout = QVBoxLayout(right_panel_widget)
        right_panel_layout.setContentsMargins(0, 0, 0, 0)
        right_panel_layout.setSpacing(0)

        # Text Patterns Card (Styled Card instead of native GroupBox)
        text_card = QWidget()
        text_card.setObjectName("textCard")
        text_card.setStyleSheet("""
            QWidget#textCard {
                background-color: #111827;
                border: 1px solid #374151;
                border-radius: 10px;
                margin-top: 10px;
            }
            QWidget#textCard QLabel {
                background: transparent;
            }
        """)
        text_layout = QVBoxLayout(text_card)
        text_layout.setContentsMargins(14, 14, 14, 14)
        text_layout.setSpacing(10)
        
        text_title_layout = QHBoxLayout()
        text_title_layout.setContentsMargins(0, 0, 0, 0)
        text_title_layout.setSpacing(6)
        
        lbl_text_title = QLabel("TEXT REDACTION")
        lbl_text_title.setStyleSheet("font-weight: 700; font-size: 11px; color: #10B981; letter-spacing: 0.5px; text-transform: uppercase; background: transparent;")
        text_title_layout.addWidget(lbl_text_title)
        text_title_layout.addStretch()
        
        SVG_REGIONS = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E5E7EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>'''
        SVG_SEARCH = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E5E7EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>'''
        
        self.btn_select_regions = QPushButton(" Regions (1)")
        self.btn_select_regions.setIcon(svg_to_icon(SVG_REGIONS))
        self.btn_select_regions.setStyleSheet("""
            QPushButton {
                background-color: #1F2937;
                color: #E5E7EB;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 3px 8px;
                font-size: 10px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #374151;
                border-color: #10B981;
                color: #FFFFFF;
            }
        """)
        self.btn_select_regions.setFixedHeight(24)
        self.btn_select_regions.clicked.connect(self._show_regions_selector)
        text_title_layout.addWidget(self.btn_select_regions)
        
        self.btn_toggle_search = QPushButton()
        self.btn_toggle_search.setIcon(svg_to_icon(SVG_SEARCH))
        self.btn_toggle_search.setToolTip("Search custom patterns")
        self.btn_toggle_search.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_search.setFixedWidth(24)
        self.btn_toggle_search.setFixedHeight(24)
        
        def get_search_toggle_style(active):
            if active:
                return """
                    QPushButton {
                        background-color: #10B981;
                        border: 1px solid #10B981;
                        border-radius: 6px;
                    }
                """
            else:
                return """
                    QPushButton {
                        background-color: #1F2937;
                        border: 1px solid #374151;
                        border-radius: 6px;
                    }
                    QPushButton:hover {
                        background-color: #374151;
                        border-color: #10B981;
                    }
                """
                
        self.btn_toggle_search.setStyleSheet(get_search_toggle_style(False))
        self.btn_toggle_search.setVisible(False)
        
        def toggle_search_bar():
            is_visible = self.txt_search_patterns.isVisible()
            self.txt_search_patterns.setVisible(not is_visible)
            self.btn_toggle_search.setStyleSheet(get_search_toggle_style(not is_visible))
            if not is_visible:
                self.txt_search_patterns.setFocus()
            else:
                self.txt_search_patterns.clear()
                
        self.btn_toggle_search.clicked.connect(toggle_search_bar)
        text_title_layout.addWidget(self.btn_toggle_search)
        text_layout.addLayout(text_title_layout)
        
        self.txt_search_patterns = QLineEdit()
        self.txt_search_patterns.setPlaceholderText("Search custom patterns...")
        self.txt_search_patterns.setStyleSheet("""
            QLineEdit {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 6px 10px;
                color: #E5E7EB;
                font-size: 13px;
                font-family: 'Segoe UI', Arial, sans-serif;
                margin-top: 4px;
                margin-bottom: 4px;
            }
            QLineEdit:focus {
                border-color: #10B981;
            }
        """)
        self.txt_search_patterns.textChanged.connect(self._filter_text_patterns)
        self.txt_search_patterns.setVisible(False)
        text_layout.addWidget(self.txt_search_patterns)
        
        # Scroll Area for Text Patterns
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #111827;
                width: 6px;
            }
            QScrollBar::handle:vertical {
                background: #374151;
                min-height: 20px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: #10B981;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        
        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background: transparent;")
        self.text_patterns_layout = QVBoxLayout(scroll_widget)
        self.text_patterns_layout.setContentsMargins(0, 0, 0, 0)
        self.text_patterns_layout.setSpacing(8)
        self.text_patterns_layout.setAlignment(Qt.AlignTop)
        
        scroll_area.setWidget(scroll_widget)
        text_layout.addWidget(scroll_area, 1)
        
        SVG_PLUS = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E5E7EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14"/><path d="M5 12h14"/></svg>'''
        SVG_IMPORT = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E5E7EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>'''
        SVG_EXPORT = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E5E7EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>'''

        self.btn_add_text = QPushButton(" Text")
        self.btn_add_text.setIcon(svg_to_icon(SVG_PLUS))
        self.btn_add_text.clicked.connect(lambda: self.add_pattern_row(is_regex=False))
        
        self.btn_add_regex = QPushButton(" Regex")
        self.btn_add_regex.setIcon(svg_to_icon(SVG_PLUS))
        self.btn_add_regex.clicked.connect(lambda: self.add_pattern_row(is_regex=True))
        
        self.btn_import = QPushButton()
        self.btn_import.setIcon(svg_to_icon(SVG_IMPORT))
        self.btn_import.setToolTip("Import Custom Patterns")
        self.btn_import.clicked.connect(self.import_custom_patterns)
        
        self.btn_export = QPushButton()
        self.btn_export.setIcon(svg_to_icon(SVG_EXPORT))
        self.btn_export.setToolTip("Export Custom Patterns")
        self.btn_export.clicked.connect(self.export_custom_patterns)
        
        for b in (self.btn_add_text, self.btn_add_regex):
            b.setStyleSheet("""
                QPushButton {
                    background-color: #1F2937;
                    color: #E5E7EB;
                    border: 1px solid #374151;
                    border-radius: 6px;
                    padding: 5px 8px;
                    font-weight: 600;
                    font-size: 11px;
                    min-height: 28px;
                }
                QPushButton:hover {
                    background-color: #374151;
                    border-color: #10B981;
                    color: #FFFFFF;
                }
            """)
            
        for b in (self.btn_import, self.btn_export):
            b.setFixedWidth(28)
            b.setFixedHeight(28)
            b.setStyleSheet("""
                QPushButton {
                    background-color: #111827;
                    color: #9CA3AF;
                    border: 1px solid #374151;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #1F2937;
                    border-color: #10B981;
                    color: #FFFFFF;
                }
            """)
            
        action_row_layout = QHBoxLayout()
        action_row_layout.setContentsMargins(0, 0, 0, 0)
        action_row_layout.setSpacing(6)
        action_row_layout.addWidget(self.btn_add_text, 2)
        action_row_layout.addWidget(self.btn_add_regex, 2)
        action_row_layout.addWidget(self.btn_import)
        action_row_layout.addWidget(self.btn_export)
        
        text_layout.addLayout(action_row_layout)
        
        right_panel_layout.addWidget(settings_card)
        right_panel_layout.addWidget(text_card, 1)

        self.splitter.addWidget(sidebar_widget)

        # === Preview Area ===
        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        
        self.preview_widget = PreviewWidget()
        self.preview_widget.setStyleSheet("""
            border: 1px solid #374151;
            border-radius: 10px;
            background-color: #0B0F19;
        """)
        self.preview_widget.on_manual_hit_added = lambda: self.btn_redact_next.setEnabled(True)
        self.preview_widget.identityRequested.connect(self.on_quick_add_identity)
        preview_layout.addWidget(self.preview_widget)

        # Draw and Zoom Tools
        draw_layout = QHBoxLayout()
        draw_layout.setSpacing(8)
        
        # Center-align the entire toolbar by placing stretch on both sides
        draw_layout.addStretch(1)
        
        self.btn_draw_mode = QPushButton(" Draw Box")
        self.btn_draw_mode.setIcon(svg_to_icon(SVG_DRAW))
        self.btn_draw_mode.setCheckable(True)
        self.btn_draw_mode.setToolTip("Draw custom manual redaction boxes (D)")
        self.btn_draw_mode.clicked.connect(self.toggle_draw_mode)
        
        self.btn_persistent_mode = QPushButton(" Persist")
        self.btn_persistent_mode.setIcon(svg_to_icon(SVG_PIN))
        self.btn_persistent_mode.setCheckable(True)
        self.btn_persistent_mode.setToolTip("Persist manual custom boxes across pages / files (Shift+D)")
        self.btn_persistent_mode.clicked.connect(self.toggle_persistent_mode)
        
        self.btn_zoom_in = QPushButton()
        self.btn_zoom_in.setIcon(svg_to_icon(SVG_ZOOM_IN))
        self.btn_zoom_in.setToolTip("Zoom In (Ctrl++ or Ctrl+=)")
        self.btn_zoom_in.clicked.connect(self.preview_widget.zoom_in)
        
        self.btn_zoom_out = QPushButton()
        self.btn_zoom_out.setIcon(svg_to_icon(SVG_ZOOM_OUT))
        self.btn_zoom_out.setToolTip("Zoom Out (Ctrl+-)")
        self.btn_zoom_out.clicked.connect(self.preview_widget.zoom_out)
        
        self.btn_reset_zoom = QPushButton()
        self.btn_reset_zoom.setIcon(svg_to_icon(SVG_ZOOM_RESET))
        self.btn_reset_zoom.setToolTip("Reset Zoom (Ctrl+0)")
        self.btn_reset_zoom.clicked.connect(self.preview_widget.reset_zoom)
        
        self.btn_rescan = QPushButton()
        self.btn_rescan.setIcon(svg_to_icon(SVG_REFRESH))
        self.btn_rescan.setToolTip("Rescan current image (F5)")
        self.btn_rescan.clicked.connect(self._rescan_current)

        tool_style = """
            QPushButton {
                background-color: #1F2937;
                color: #E5E7EB;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 0px 16px;
                min-height: 36px;
                max-height: 36px;
                font-weight: 600;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #374151;
                border-color: #4B5563;
                color: #FFFFFF;
            }
            QPushButton:checked {
                background-color: #0D9488;
                border-color: #0F766E;
                color: #FFFFFF;
            }
            QPushButton:disabled {
                background-color: #111827;
                color: #4B5563;
                border-color: #1F2937;
            }
        """

        icon_only_style = """
            QPushButton {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 8px;
                min-width: 36px;
                max-width: 36px;
                min-height: 36px;
                max-height: 36px;
            }
            QPushButton:hover {
                background-color: #374151;
                border-color: #4B5563;
            }
            QPushButton:pressed {
                background-color: #111827;
            }
            QPushButton:disabled {
                background-color: #111827;
                border-color: #1F2937;
            }
        """

        self.btn_draw_mode.setStyleSheet(tool_style)
        self.btn_persistent_mode.setStyleSheet(tool_style)
        
        from PySide6.QtCore import QSize
        for btn in (self.btn_zoom_in, self.btn_zoom_out, self.btn_reset_zoom, self.btn_rescan):
            btn.setStyleSheet(icon_only_style)
            btn.setIconSize(QSize(18, 18))

        draw_layout.addWidget(self.btn_draw_mode)
        draw_layout.addWidget(self.btn_persistent_mode)
        
        from PySide6.QtWidgets import QFrame
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.VLine)
        sep1.setFrameShadow(QFrame.Sunken)
        sep1.setStyleSheet("color: #374151; margin: 4px 2px;")
        draw_layout.addWidget(sep1)
        
        draw_layout.addWidget(self.btn_zoom_in)
        draw_layout.addWidget(self.btn_zoom_out)
        draw_layout.addWidget(self.btn_reset_zoom)
        
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.VLine)
        sep2.setFrameShadow(QFrame.Sunken)
        sep2.setStyleSheet("color: #374151; margin: 4px 2px;")
        draw_layout.addWidget(sep2)
        
        draw_layout.addWidget(self.btn_rescan)
        draw_layout.addStretch(1)
        preview_layout.addLayout(draw_layout)
        
        # Shortcuts
        from PySide6.QtGui import QShortcut
        self.shortcut_draw = QShortcut(QKeySequence(self.shortcuts_config["toggle_draw"]), self)
        self.shortcut_draw.activated.connect(self._on_shortcut_draw)

        self.shortcut_persistent = QShortcut(QKeySequence(self.shortcuts_config["toggle_persistent"]), self)
        self.shortcut_persistent.activated.connect(self._on_shortcut_persistent)

        self.shortcut_zoom_in = QShortcut(QKeySequence(self.shortcuts_config["zoom_in"]), self)
        self.shortcut_zoom_in.activated.connect(self._on_shortcut_zoom_in)

        self.shortcut_zoom_in2 = QShortcut(QKeySequence(self.shortcuts_config["zoom_in_alt"]), self)
        self.shortcut_zoom_in2.activated.connect(self._on_shortcut_zoom_in)

        self.shortcut_zoom_out = QShortcut(QKeySequence(self.shortcuts_config["zoom_out"]), self)
        self.shortcut_zoom_out.activated.connect(self._on_shortcut_zoom_out)

        self.shortcut_zoom_reset = QShortcut(QKeySequence(self.shortcuts_config["zoom_reset"]), self)
        self.shortcut_zoom_reset.activated.connect(self._on_shortcut_zoom_reset)

        self.shortcut_rescan = QShortcut(QKeySequence(self.shortcuts_config["rescan"]), self)
        self.shortcut_rescan.activated.connect(self._on_shortcut_rescan)

        # Action Buttons
        actions_layout = QHBoxLayout()
        
        self.btn_previous = QPushButton(" Previous")
        self.btn_previous.setIcon(svg_to_icon(SVG_ARROW_LEFT))
        self.btn_previous.setEnabled(False)
        self.btn_previous.hide()
        self.btn_previous.clicked.connect(self.go_previous)
        self.btn_previous.setStyleSheet("""
            QPushButton {
                background-color: #1F2937;
                color: #E5E7EB;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 10px 16px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #374151;
                border-color: #4B5563;
                color: #FFFFFF;
            }
            QPushButton:disabled {
                background-color: #111827;
                color: #4B5563;
                border-color: #1F2937;
            }
        """)
        
        self.btn_skip = QPushButton(" Skip")
        self.btn_skip.setIcon(svg_to_icon(SVG_ARROW_RIGHT))
        self.btn_skip.hide()
        self.btn_skip.clicked.connect(self.skip_current)
        self.btn_skip.setStyleSheet("""
            QPushButton {
                background-color: #1F2937;
                color: #E5E7EB;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 10px 16px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #374151;
                border-color: #4B5563;
                color: #FFFFFF;
            }
            QPushButton:disabled {
                background-color: #111827;
                color: #4B5563;
                border-color: #1F2937;
            }
        """)
        
        self.btn_redact_next = QPushButton(" Redact & Next")
        self.btn_redact_next.setIcon(svg_to_icon(SVG_PLAY))
        self.btn_redact_next.setEnabled(False)
        self.btn_redact_next.hide()
        self.btn_redact_next.clicked.connect(self.redact_current)
        self.btn_redact_next.setStyleSheet("""
            QPushButton {
                background-color: #E11D48;
                color: #FFFFFF;
                border: 1px solid #BE123C;
                border-radius: 8px;
                padding: 10px 18px;
                font-weight: 700;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #F43F5E;
                border-color: #E11D48;
            }
            QPushButton:disabled {
                background-color: #4B5563;
                border-color: #374151;
                color: #9CA3AF;
            }
        """)
        
        self.btn_stop_review = QPushButton(" Stop Review")
        self.btn_stop_review.setIcon(svg_to_icon(SVG_SQUARE))
        self.btn_stop_review.hide()
        self.btn_stop_review.clicked.connect(self.cancel_batch_mode)
        self.btn_stop_review.setStyleSheet("""
            QPushButton {
                background-color: #374151;
                color: #E5E7EB;
                border: 1px solid #4B5563;
                border-radius: 8px;
                padding: 10px 16px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #4B5563;
                border-color: #6B7280;
                color: #FFFFFF;
            }
        """)

        actions_layout.addWidget(self.btn_previous)
        actions_layout.addWidget(self.btn_skip)
        actions_layout.addWidget(self.btn_redact_next)
        actions_layout.addWidget(self.btn_stop_review)
        
        self.btn_start_review = QPushButton(" Start Review Process")
        self.btn_start_review.setIcon(svg_to_icon(SVG_PLAY))
        self.btn_start_review.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: #FFFFFF;
                border: 1px solid #059669;
                border-radius: 8px;
                padding: 12px;
                font-size: 15px;
                font-weight: 700;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background-color: #059669;
                border-color: #047857;
            }
            QPushButton:pressed {
                background-color: #047857;
            }
        """)
        self.btn_start_review.clicked.connect(self.start_batch)

        preview_layout.addLayout(actions_layout)
        preview_layout.addWidget(self.btn_start_review)

        # Batch Navigation Shortcuts
        from PySide6.QtGui import QShortcut
        self.shortcut_start_redact = QShortcut(QKeySequence(self.shortcuts_config["redact_next"]), self)
        self.shortcut_start_redact.activated.connect(self._on_shortcut_start_redact)
        
        self.shortcut_start_redact_ent = QShortcut(QKeySequence(self.shortcuts_config["redact_next_alt"]), self)
        self.shortcut_start_redact_ent.activated.connect(self._on_shortcut_start_redact)

        # Skip Shortcuts (Space or S)
        self.shortcut_skip_space = QShortcut(QKeySequence(self.shortcuts_config["skip_space"]), self)
        self.shortcut_skip_space.activated.connect(self._on_shortcut_skip_space)

        self.shortcut_skip_s = QShortcut(QKeySequence(self.shortcuts_config["skip_s"]), self)
        self.shortcut_skip_s.activated.connect(self._on_shortcut_skip_s)

        # Previous Shortcuts (Backspace or P)
        self.shortcut_prev_bs = QShortcut(QKeySequence(self.shortcuts_config["previous_bs"]), self)
        self.shortcut_prev_bs.activated.connect(self._on_shortcut_previous)

        self.shortcut_prev_p = QShortcut(QKeySequence(self.shortcuts_config["previous_p"]), self)
        self.shortcut_prev_p.activated.connect(self._on_shortcut_previous)

        self.shortcut_escape = QShortcut(QKeySequence(self.shortcuts_config["escape"]), self)
        self.shortcut_escape.activated.connect(self._on_shortcut_escape)

        # Global Application Shortcuts
        self.shortcut_add_file = QShortcut(QKeySequence(self.shortcuts_config["add_file"]), self)
        self.shortcut_add_file.activated.connect(self._on_shortcut_add_file)

        self.shortcut_add_folder = QShortcut(QKeySequence(self.shortcuts_config["add_folder"]), self)
        self.shortcut_add_folder.activated.connect(self._on_shortcut_add_folder)

        self.shortcut_remove_file = QShortcut(QKeySequence(self.shortcuts_config["remove_file"]), self)
        self.shortcut_remove_file.activated.connect(self._on_shortcut_remove_file)

        self.shortcut_settings = QShortcut(QKeySequence(self.shortcuts_config["settings"]), self)
        self.shortcut_settings.activated.connect(self._on_shortcut_settings)

        self.shortcut_clear_queue = QShortcut(QKeySequence(self.shortcuts_config["clear_queue"]), self)
        self.shortcut_clear_queue.activated.connect(self._on_shortcut_clear_queue)

        self.shortcut_paste = QShortcut(QKeySequence(self.shortcuts_config["paste"]), self)
        self.shortcut_paste.activated.connect(self._on_shortcut_paste)

        sidebar_widget.setMinimumWidth(200)
        preview_container.setMinimumWidth(300)
        right_panel_widget.setMinimumWidth(310)

        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(preview_container)
        self.splitter.addWidget(right_panel_widget)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 4)
        self.splitter.setStretchFactor(2, 1)
        QTimer.singleShot(50, self._apply_default_splitter_sizes)

        self.shortcut_reset_layout = QShortcut(QKeySequence(self.shortcuts_config["reset_layout"]), self)
        self.shortcut_reset_layout.activated.connect(self._on_shortcut_reset_layout)

        # Hit Navigation/Toggle Shortcuts
        self.shortcut_hit_next = QShortcut(QKeySequence(self.shortcuts_config["hit_next"]), self)
        self.shortcut_hit_next.activated.connect(self._on_shortcut_hit_next)

        self.shortcut_hit_prev = QShortcut(QKeySequence(self.shortcuts_config["hit_prev"]), self)
        self.shortcut_hit_prev.activated.connect(self._on_shortcut_hit_prev)

        self.shortcut_hit_toggle = QShortcut(QKeySequence(self.shortcuts_config["hit_toggle"]), self)
        self.shortcut_hit_toggle.activated.connect(self._on_shortcut_hit_toggle)

        self.current_file_path = None
        self.user_selections_cache = {}
        self.current_hits = []
        
        # Batch Mode State
        self.is_batch_mode = False
        try:
            from src.core.patterns import REGIONS
            self.active_regions = {r: (r == "Global") for r in REGIONS}
        except Exception:
            self.active_regions = {"Global": True, "Pakistan": False, "United States": False, "European Union": False}
        self.batch_index = -1
        self.batch_success_count = 0
        
        # PDF Sub-loop State
        self.active_pdf_pages = []
        self.active_pdf_index = -1
        self.active_pdf_outputs = []
        self.active_pdf_source = None

        # Apply StrongFocus focus policy to all interactive widgets for a consistent tabbing experience
        interactive_widgets = [
            self.btn_settings,
            self.file_list,
            self.btn_add_file,
            self.btn_add_folder,
            self.btn_paste,
            self.btn_remove,
            self.btn_clear,
            self.cmb_vision_mode,
            self.btn_select_people,
            self.btn_select_regions,
            self.btn_add_text,
            self.btn_add_regex,
            self.btn_import,
            self.btn_export,
            self.btn_draw_mode,
            self.btn_persistent_mode,
            self.btn_zoom_in,
            self.btn_zoom_out,
            self.btn_reset_zoom,
            self.btn_rescan,
            self.chk_auto_skip,
            self.chk_skip_review,
            self.btn_start_review,
            self.btn_redact_next,
            self.btn_skip,
            self.btn_previous,
            self.btn_stop_review
        ]
        for w in interactive_widgets:
            if hasattr(w, "setFocusPolicy"):
                w.setFocusPolicy(Qt.StrongFocus)
        apply_focus_indicators(self)
        self.update_toolbar_state()
        self.update_review_button_tooltips()
        self.focus_filter = FocusEventFilter(self)
        QApplication.instance().installEventFilter(self.focus_filter)

    def _apply_default_splitter_sizes(self):
        """Compute splitter sizes from actual width so nothing clips."""
        total = self.splitter.width()
        handles = self.splitter.handleWidth() * 2  # 2 handles between 3 panes
        usable = total - handles
        left = 260
        right = 310
        middle = max(300, usable - left - right)
        self.splitter.setSizes([left, middle, right])

    def toggle_draw_mode(self, checked):
        self.preview_widget.set_drawing_mode(checked)

    def toggle_persistent_mode(self, checked):
        if checked:
            is_pdf = bool(self.active_pdf_pages)
            dialog = PersistentRangeDialog(is_pdf, self)
            if dialog.exec() == QDialog.Accepted:
                scope = dialog.get_selected_scope()
                pdf_source = self.active_pdf_source if is_pdf else None
                self.preview_widget.set_persistent_mode(True, scope=scope, pdf_source=pdf_source)
                # Automatically activate Draw mode.
                if not self.btn_draw_mode.isChecked():
                    self.btn_draw_mode.setChecked(True)
                    self.toggle_draw_mode(True)
            else:
                self.btn_persistent_mode.setChecked(False)
        else:
            self.preview_widget.set_persistent_mode(False)

    def update_toolbar_state(self):
        has_file = self.current_file_path is not None
        self.btn_draw_mode.setEnabled(has_file)
        self.btn_persistent_mode.setEnabled(has_file)
        self.btn_zoom_in.setEnabled(has_file)
        self.btn_zoom_out.setEnabled(has_file)
        self.btn_reset_zoom.setEnabled(has_file)
        self.btn_rescan.setEnabled(has_file)

    def cancel_batch_mode(self):
        if self.current_file_path:
            manuals = self.preview_widget.active_hits.copy()
            ckey = self.get_current_cache_key()
            self.user_selections_cache[ckey] = {
                "active_hits": manuals,
                "reviewed": True
            }

        self.is_batch_mode = False
        self.batch_index = -1
        self.batch_success_count = 0
        self.cleanup_temp_resources(full=False)
        self.active_pdf_pages = []
        self.active_pdf_outputs = []
        self.active_pdf_index = -1
        
        self.btn_previous.hide()
        self.btn_skip.hide()
        self.btn_redact_next.hide()
        self.btn_stop_review.hide()
        self.btn_start_review.show()
        self.preview_widget.clear_preview()
        self.current_file_path = None
        self.current_hits = []
        self.file_list.setEnabled(True)
        self.update_toolbar_state()
        
        # Re-enable controls when batch review stops.
        self.btn_settings.setEnabled(True)
        self.btn_add_file.setEnabled(True)
        self.btn_add_folder.setEnabled(True)
        self.btn_paste.setEnabled(True)
        self.btn_remove.setEnabled(True)
        self.btn_clear.setEnabled(True)
        
        # Reset draw mode.
        if self.btn_draw_mode.isChecked():
            self.btn_draw_mode.setChecked(False)
            self.toggle_draw_mode(False)

        # Reset persistent mode.
        if self.btn_persistent_mode.isChecked():
            self.btn_persistent_mode.setChecked(False)
            self.preview_widget.set_persistent_mode(False)

    def _is_input_focused(self):
        if QApplication.activeModalWidget() is not None:
            return True
        focused = QApplication.focusWidget()
        if not focused:
            return False
        from PySide6.QtWidgets import QLineEdit, QTextEdit, QPlainTextEdit
        return isinstance(focused, (QLineEdit, QTextEdit, QPlainTextEdit))

    def _on_shortcut_draw(self):
        if self._is_input_focused():
            return
        self.btn_draw_mode.click()

    def _on_shortcut_persistent(self):
        if self._is_input_focused():
            return
        self.btn_persistent_mode.click()

    def _on_shortcut_zoom_in(self):
        if self._is_input_focused():
            return
        self.preview_widget.zoom_in()

    def _on_shortcut_zoom_out(self):
        if self._is_input_focused():
            return
        self.preview_widget.zoom_out()

    def _on_shortcut_zoom_reset(self):
        if self._is_input_focused():
            return
        self.preview_widget.reset_zoom()

    def _on_shortcut_rescan(self):
        if self._is_input_focused():
            return
        self._rescan_current()

    def _on_shortcut_start_redact(self):
        self.on_return_pressed()

    def _on_shortcut_skip_space(self):
        if self._is_input_focused():
            return
        if self.preview_widget.has_focused_hit():
            self.preview_widget.toggle_focused_hit()
            return
        if self.btn_skip.isVisible() and self.btn_skip.isEnabled():
            self.btn_skip.click()

    def _on_shortcut_skip_s(self):
        if self._is_input_focused():
            return
        if self.btn_skip.isVisible() and self.btn_skip.isEnabled():
            self.btn_skip.click()

    def _on_shortcut_previous(self):
        if self._is_input_focused():
            return
        self.preview_widget.clear_hit_focus()
        if self.btn_previous.isVisible() and self.btn_previous.isEnabled():
            self.btn_previous.click()

    def _on_shortcut_escape(self):
        focused = QApplication.focusWidget()
        if focused and focused is not self and focused.property("focused_via_keyboard") == "true":
            focused.clearFocus()
            self.setFocus()
            return
        from PySide6.QtWidgets import QLineEdit, QTextEdit, QPlainTextEdit
        if focused and isinstance(focused, (QLineEdit, QTextEdit, QPlainTextEdit)):
            focused.clearFocus()
            self.setFocus()
            return
        self.on_escape_pressed()

    def _on_shortcut_hit_next(self):
        if self._is_input_focused():
            return
        self.preview_widget.focus_next_hit()

    def _on_shortcut_hit_prev(self):
        if self._is_input_focused():
            return
        self.preview_widget.focus_previous_hit()

    def _on_shortcut_hit_toggle(self):
        if self._is_input_focused():
            return
        self.preview_widget.toggle_focused_hit()

    def _on_shortcut_add_file(self):
        if self._is_input_focused():
            return
        self.add_files()

    def _on_shortcut_add_folder(self):
        if self._is_input_focused():
            return
        self.add_folder()

    def _on_shortcut_remove_file(self):
        if self._is_input_focused():
            return
        self.remove_selected_file()

    def _on_shortcut_settings(self):
        if self._is_input_focused():
            return
        self.open_settings()

    def _on_shortcut_clear_queue(self):
        if self._is_input_focused():
            return
        self.clear_queue()

    def _on_shortcut_paste(self):
        focused = QApplication.focusWidget()
        from PySide6.QtWidgets import QLineEdit, QTextEdit, QPlainTextEdit
        if focused and isinstance(focused, (QLineEdit, QTextEdit, QPlainTextEdit)):
            focused.paste()
            return
        self.on_paste()

    def _on_shortcut_reset_layout(self):
        if self._is_input_focused():
            return
        self._apply_default_splitter_sizes()

    def update_shortcut_key(self, action_name: str, new_sequence: str):
        """Dynamically update key sequence of QShortcut objects in MainWindow."""
        self.shortcuts_config[action_name] = new_sequence
        
        # Mapping from config key to self.shortcut_* attribute name(s)
        shortcut_mapping = {
            "add_file": ["shortcut_add_file"],
            "add_folder": ["shortcut_add_folder"],
            "remove_file": ["shortcut_remove_file"],
            "clear_queue": ["shortcut_clear_queue"],
            "settings": ["shortcut_settings"],
            "paste": ["shortcut_paste"],
            "reset_layout": ["shortcut_reset_layout"],
            "zoom_in": ["shortcut_zoom_in"],
            "zoom_in_alt": ["shortcut_zoom_in2"],
            "zoom_out": ["shortcut_zoom_out"],
            "zoom_reset": ["shortcut_zoom_reset"],
            "toggle_draw": ["shortcut_draw"],
            "toggle_persistent": ["shortcut_persistent"],
            "rescan": ["shortcut_rescan"],
            "redact_next": ["shortcut_start_redact"],
            "redact_next_alt": ["shortcut_start_redact_ent"],
            "skip_s": ["shortcut_skip_s"],
            "skip_space": ["shortcut_skip_space"],
            "previous_p": ["shortcut_prev_p"],
            "previous_bs": ["shortcut_prev_bs"],
            "escape": ["shortcut_escape"],
            "hit_next": ["shortcut_hit_next"],
            "hit_prev": ["shortcut_hit_prev"],
            "hit_toggle": ["shortcut_hit_toggle"]
        }
        
        from PySide6.QtGui import QKeySequence
        if action_name in shortcut_mapping:
            for attr_name in shortcut_mapping[action_name]:
                shortcut_obj = getattr(self, attr_name, None)
                if shortcut_obj:
                    shortcut_obj.setKey(QKeySequence(new_sequence))
        self.update_review_button_tooltips()

    def update_review_button_tooltips(self):
        """Update review action buttons' tooltips dynamically based on active keyboard shortcuts."""
        redact_shortcut = self.shortcuts_config.get("redact_next", "Shift+Enter")
        redact_alt = self.shortcuts_config.get("redact_next_alt", "Enter")
        self.btn_redact_next.setToolTip(f"Redact current document and proceed to the next ({redact_shortcut} or {redact_alt})")

        skip_shortcut = self.shortcuts_config.get("skip_space", "Space")
        skip_alt = self.shortcuts_config.get("skip_s", "S")
        self.btn_skip.setToolTip(f"Skip current document without redacting ({skip_shortcut} or {skip_alt})")

        prev_shortcut = self.shortcuts_config.get("previous_bs", "Backspace")
        prev_alt = self.shortcuts_config.get("previous_p", "P")
        self.btn_previous.setToolTip(f"Go back to the previous document ({prev_shortcut} or {prev_alt})")

        stop_shortcut = self.shortcuts_config.get("escape", "Esc")
        self.btn_stop_review.setToolTip(f"Stop the active batch review process ({stop_shortcut})")

    def set_shortcuts_enabled(self, enabled: bool):
        """Enable or disable all window-level QShortcut instances to prevent interception during text entry."""
        shortcut_attrs = [
            "shortcut_draw",
            "shortcut_persistent",
            "shortcut_zoom_in",
            "shortcut_zoom_in2",
            "shortcut_zoom_out",
            "shortcut_zoom_reset",
            "shortcut_rescan",
            "shortcut_start_redact",
            "shortcut_start_redact_ent",
            "shortcut_skip_space",
            "shortcut_skip_s",
            "shortcut_prev_bs",
            "shortcut_prev_p",
            "shortcut_escape",
            "shortcut_add_file",
            "shortcut_add_folder",
            "shortcut_remove_file",
            "shortcut_settings",
            "shortcut_clear_queue",
            "shortcut_paste",
            "shortcut_reset_layout",
            "shortcut_hit_next",
            "shortcut_hit_prev",
            "shortcut_hit_toggle"
        ]
        for attr in shortcut_attrs:
            shortcut = getattr(self, attr, None)
            if shortcut:
                try:
                    shortcut.setEnabled(enabled)
                except Exception:
                    pass



    def on_return_pressed(self):
        focused_widget = QApplication.focusWidget()
        if isinstance(focused_widget, QLineEdit):
            focused_widget.clearFocus()
            return

        if self.btn_start_review.isVisible():
            self.btn_start_review.click()
        elif self.btn_redact_next.isVisible() and self.btn_redact_next.isEnabled():
            self.btn_redact_next.click()

    def on_escape_pressed(self):
        if self.btn_stop_review.isVisible():
            self.btn_stop_review.click()

    def open_settings(self):
        dialog = SettingsDialog(self.scanner, self)
        dialog.exec()
        if self.scanner:
            self.scanner.clear_cache()
        self._rescan_current()

    def add_pattern_row(self, is_regex=False):
        row_widget = QWidget()
        row_widget.setStyleSheet("background: transparent;")
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(4)
        
        input_field = PatternLineEdit(is_regex, self)
        input_field.setPlaceholderText("Regex pattern..." if is_regex else "Text pattern...")
        input_field.setProperty("is_regex", is_regex)
        input_field.setStyleSheet("""
            QLineEdit {
                background-color: #1F2937;
                color: #F3F4F6;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 5px 8px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #10B981;
            }
        """)
        input_field.editingFinished.connect(self.update_text_patterns)
        row_layout.addWidget(input_field, 1)
        
        if not is_regex:
            SVG_WHOLE_WORD = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E5E7EB" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M6 5H4v14h2"/>
                <path d="M18 5h2v14h-2"/>
                <path d="M8 9l2 6l2-5l2 5l2-6"/>
            </svg>'''
            
            btn_whole = QPushButton()
            btn_whole.setObjectName("btn_whole")
            btn_whole.setCheckable(True)
            btn_whole.setChecked(True)
            btn_whole.setIcon(svg_to_icon(SVG_WHOLE_WORD))
            btn_whole.setToolTip("Whole Word Match")
            btn_whole.setCursor(Qt.PointingHandCursor)
            btn_whole.setFixedWidth(28)
            btn_whole.setFixedHeight(28)
            
            def get_whole_style(checked):
                if checked:
                    return """
                        QPushButton {
                            background-color: #10B981;
                            border: 1px solid #10B981;
                            border-radius: 6px;
                        }
                    """
                else:
                    return """
                        QPushButton {
                            background-color: #1F2937;
                            border: 1px solid #374151;
                            border-radius: 6px;
                        }
                        QPushButton:hover {
                            background-color: #374151;
                            border-color: #4B5563;
                        }
                    """
            
            btn_whole.setStyleSheet(get_whole_style(True))
            btn_whole.clicked.connect(lambda checked, b=btn_whole: [b.setStyleSheet(get_whole_style(checked)), self.update_text_patterns()])
            btn_whole.setFocusPolicy(Qt.StrongFocus)
            row_layout.addWidget(btn_whole)
            
        btn_remove = QPushButton()
        btn_remove.setIcon(svg_to_icon(SVG_X_CIRCLE))
        btn_remove.setFixedWidth(28)
        btn_remove.setFixedHeight(28)
        btn_remove.setStyleSheet("""
            QPushButton {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #E11D48;
                border-color: #BE123C;
            }
        """)
        btn_remove.clicked.connect(lambda checked=False, rw=row_widget: self.remove_pattern_row(rw))
        btn_remove.setFocusPolicy(Qt.StrongFocus)
        row_layout.addWidget(btn_remove)
        
        self.text_patterns_layout.addWidget(row_widget)
        apply_focus_indicators(row_widget)
        if hasattr(self, "btn_toggle_search"):
            self.btn_toggle_search.setVisible(True)
        self.update_text_patterns()
        input_field.setFocus()
        
    def remove_pattern_row(self, row_widget):
        row_widget.hide()  # Hide immediately so it gets filtered out
        self.text_patterns_layout.removeWidget(row_widget)
        row_widget.deleteLater()
        has_patterns = self.text_patterns_layout.count() > 0
        if hasattr(self, "btn_toggle_search"):
            self.btn_toggle_search.setVisible(has_patterns)
            if not has_patterns:
                self.txt_search_patterns.setVisible(False)
                self.txt_search_patterns.clear()
                self.btn_toggle_search.setStyleSheet("background-color: #1F2937; color: #9CA3AF; border: 1px solid #374151; border-radius: 4px;")
        self.update_text_patterns()

    def import_custom_patterns(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Custom Patterns", "", "SafeMARC Patterns (*.json)")
        if not file_path:
            return
            
        import json
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if not isinstance(data, list):
                raise ValueError("JSON content must be a list of patterns.")
                
            # Clear current custom pattern rows first.
            while self.text_patterns_layout.count() > 0:
                item = self.text_patterns_layout.takeAt(0)
                if item and item.widget():
                    item.widget().deleteLater()
                    
            # Load imported patterns.
            for item in data:
                pattern_str = item.get("pattern", "").strip()
                is_regex = item.get("is_regex", False)
                whole_word = item.get("whole_word", False)
                
                if pattern_str:
                    self.add_pattern_row(is_regex=is_regex)
                    # Find the newly added row widget.
                    last_idx = self.text_patterns_layout.count() - 1
                    if last_idx >= 0:
                        row_widget = self.text_patterns_layout.itemAt(last_idx).widget()
                        if row_widget:
                            input_field = row_widget.findChild(QLineEdit)
                            if input_field:
                                input_field.setText(pattern_str)
                            btn_whole = row_widget.findChild(QPushButton, "btn_whole")
                            if btn_whole:
                                btn_whole.setChecked(whole_word)
                                style = """
                                    QPushButton {
                                        background-color: #10B981;
                                        border: 1px solid #10B981;
                                        border-radius: 6px;
                                    }
                                """ if whole_word else """
                                    QPushButton {
                                        background-color: #1F2937;
                                        border: 1px solid #374151;
                                        border-radius: 6px;
                                    }
                                    QPushButton:hover {
                                        background-color: #374151;
                                        border-color: #4B5563;
                                    }
                                """
                                btn_whole.setStyleSheet(style)
                                
            self.update_text_patterns()
            has_patterns = self.text_patterns_layout.count() > 0
            if hasattr(self, "btn_toggle_search"):
                self.btn_toggle_search.setVisible(has_patterns)
                if not has_patterns:
                    self.txt_search_patterns.setVisible(False)
                    self.txt_search_patterns.clear()
                    self.btn_toggle_search.setStyleSheet("background-color: #1F2937; color: #9CA3AF; border: 1px solid #374151; border-radius: 4px;")
            QMessageBox.information(self, "Success", "Custom patterns imported successfully!")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to import patterns: {str(e)}")

    def export_custom_patterns(self):
        # Gather custom patterns.
        patterns = []
        for i in range(self.text_patterns_layout.count()):
            item = self.text_patterns_layout.itemAt(i)
            if item:
                row_widget = item.widget()
                if row_widget and row_widget.isVisible():
                    input_field = row_widget.findChild(QLineEdit)
                    btn_whole = row_widget.findChild(QPushButton, "btn_whole")
                    is_whole_word = btn_whole.isChecked() if btn_whole else False
                    
                    if input_field and input_field.text().strip():
                        patterns.append({
                            "pattern": input_field.text(),
                            "is_regex": bool(input_field.property("is_regex")),
                            "whole_word": is_whole_word
                        })
                        
        if not patterns:
            QMessageBox.warning(self, "Export", "No custom patterns found to export.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Custom Patterns", "", "SafeMARC Patterns (*.json)")
        if not file_path:
            return
            
        import json
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(patterns, f, indent=4)
            QMessageBox.information(self, "Success", f"Successfully exported {len(patterns)} patterns!")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to export patterns: {str(e)}")

    def focus_last_pattern_field(self):
        count = self.text_patterns_layout.count()
        for i in range(count - 1, -1, -1):
            item = self.text_patterns_layout.itemAt(i)
            if item:
                row_widget = item.widget()
                if row_widget:
                    input_field = row_widget.findChild(QLineEdit)
                    if input_field:
                        input_field.setFocus()
                        break
        
    def _filter_queue_list(self, text):
        text = text.lower().strip()
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            item.setHidden(text not in item.text().lower())

    def _filter_text_patterns(self, text):
        text = text.lower().strip()
        for i in range(self.text_patterns_layout.count()):
            item = self.text_patterns_layout.itemAt(i)
            if item and item.widget():
                row_widget = item.widget()
                input_field = row_widget.findChild(PatternLineEdit)
                if input_field:
                    row_widget.setHidden(text not in input_field.text().lower())

    def update_text_patterns(self):
        if not self.scanner:
            return
            
        patterns = []
        
        # 1. Load active predefined region patterns from patterns.py
        try:
            from src.core.patterns import PREDEFINED_PATTERNS
            for region_name, is_active in getattr(self, "active_regions", {}).items():
                if is_active:
                    for pat_id, p_info in PREDEFINED_PATTERNS.items():
                        if region_name in p_info["regions"]:
                            patterns.append({
                                "label": p_info["label"],
                                "pattern": p_info["regex"],
                                "is_regex": True,
                                "keywords": p_info["keywords"]
                            })
        except Exception as e:
            print(f"Error loading predefined patterns: {e}")
            
        # 2. Gather custom patterns from rows
        for i in range(self.text_patterns_layout.count()):
            item = self.text_patterns_layout.itemAt(i)
            if item:
                row_widget = item.widget()
                if row_widget and row_widget.isVisible():
                    input_field = row_widget.findChild(QLineEdit)
                    btn_whole = row_widget.findChild(QPushButton, "btn_whole")
                    is_whole_word = btn_whole.isChecked() if btn_whole else False
                    
                    if input_field and input_field.text().strip():
                        patterns.append({
                            "label": "REGEX" if input_field.property("is_regex") else "TEXT",
                            "pattern": input_field.text(),
                            "is_regex": input_field.property("is_regex"),
                            "whole_word": is_whole_word
                        })
                    
        self.scanner.set_text_patterns(patterns)
        
        # Auto-rescan if a file is loaded
        if self.current_file_path:
            # Cache current selections before rescanning
            manuals = self.preview_widget.active_hits.copy()
            ckey = self.get_current_cache_key()
            self.user_selections_cache[ckey] = {
                "active_hits": manuals,
                "reviewed": False
            }
            self._rescan_current()

    def on_vision_mode_changed(self, index):
        if not self.scanner:
            return
            
        mode = self.cmb_vision_mode.itemData(index)
        try:
            self.scanner.set_vision_mode(mode)
            if self.is_batch_mode and self.current_file_path:
                self.btn_redact_next.setEnabled(False)
                from PySide6.QtCore import QTimer
                QTimer.singleShot(0, self.load_next_batch_item)
        except Exception as e:
            print(f"Error switching vision mode: {e}")

    def _update_face_mode(self, text):
        if not self.scanner:
            return
        
        mode_map = {
            "All": "ALL",
            "Blacklist": "BLACKLIST",
            "Whitelist": "WHITELIST"
        }
        internal_mode = mode_map.get(text, "ALL")
        self.scanner.set_face_redaction_mode(internal_mode)
        print(f"Face redaction mode set to: {internal_mode}")
        
        # Show/hide Select People button based on mode
        if text in ("Blacklist", "Whitelist"):
            self.btn_select_people.show()
        else:
            self.btn_select_people.hide()
        
        self._rescan_current()

    def on_quick_add_identity(self, hit):
        if not self.current_file_path or not self.scanner:
            return
            
        from PySide6.QtWidgets import QMessageBox
        
        # Retrieve existing identity names.
        existing_names = sorted(list(set(self.scanner.identity_manager.identity_map.values())))
        
        dialog = QuickAddIdentityDialog(existing_names, self)
        if dialog.exec() == QDialog.Accepted:
            name = dialog.get_name()
            if name:
                # Check if identity exists.
                if name in existing_names:
                    # Determine if identity is session-specific or permanent.
                    is_session = False
                    if os.path.exists(os.path.join(self.scanner.identity_manager.session_temp, name)):
                        is_session = True
                else:
                    # Prompt user to select storage type.
                    msg = QMessageBox(self)
                    msg.setWindowTitle("Save Type")
                    msg.setText(f"How do you want to save '{name}'?")
                    btn_perm = msg.addButton("Permanently", QMessageBox.ActionRole)
                    btn_session = msg.addButton("This Session Only", QMessageBox.ActionRole)
                    msg.addButton("Cancel", QMessageBox.RejectRole)
                    msg.exec()
                    
                    is_session = msg.clickedButton() == btn_session
                    if msg.clickedButton() not in [btn_perm, btn_session]:
                        return

                import cv2
                img = cv2.imread(self.current_file_path)
                if img is not None:
                    face_crop = img[hit.y:hit.y+hit.h, hit.x:hit.x+hit.w]
                    
                    # Write temporary face crop to file.
                    temp_path = os.path.join(self.scanner.identity_manager.identities_dir, "temp_quick_add.jpg")
                    cv2.imwrite(temp_path, face_crop)
                    
                    if is_session:
                        self.scanner.identity_manager.add_session_identity(name, temp_path)
                        QMessageBox.information(self, "Success", f"Added '{name}' (Session Only).")
                    else:
                        self.scanner.identity_manager.add_identity(name, [temp_path])
                        QMessageBox.information(self, "Success", f"Added '{name}' permanently.")
                    
                    os.remove(temp_path)
                    if self.scanner:
                        self.scanner.clear_vision_cache()
                    self._rescan_current()

    def _show_regions_selector(self):
        from PySide6.QtWidgets import QMenu, QWidgetAction, QCheckBox, QVBoxLayout, QWidget, QLabel
        from PySide6.QtCore import QPoint
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #1F2937; color: #E5E7EB; border: 1px solid #374151; padding: 10px; border-radius: 8px; }
        """)
        
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)
        
        lbl_header = QLabel("Active Regions")
        lbl_header.setStyleSheet("font-size: 11px; font-weight: bold; color: #10B981; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;")
        layout.addWidget(lbl_header)
        
        try:
            from src.core.patterns import REGIONS
            regions_list = REGIONS
        except Exception:
            regions_list = ["Global", "Pakistan", "United States", "European Union"]
        for r_name in regions_list:
            chk = QCheckBox(r_name)
            chk.setCursor(Qt.PointingHandCursor)
            chk.setChecked(self.active_regions.get(r_name, False))
            chk.setStyleSheet("""
                QCheckBox { spacing: 8px; color: #E5E7EB; font-size: 13px; font-family: 'Segoe UI', Arial, sans-serif; }
                QCheckBox::indicator { width: 16px; height: 16px; border-radius: 4px; border: 1px solid #374151; background-color: #1F2937; }
                QCheckBox::indicator:hover { border-color: #4B5563; }
                QCheckBox::indicator:checked { background-color: #10B981; border-color: #10B981; }
            """)
            
            def make_toggle_region(name):
                return lambda checked: self._toggle_active_region(name, checked)
            chk.toggled.connect(make_toggle_region(r_name))
            layout.addWidget(chk)
            
        action = QWidgetAction(menu)
        action.setDefaultWidget(container)
        menu.addAction(action)
        menu.exec(self.btn_select_regions.mapToGlobal(QPoint(0, self.btn_select_regions.height())))

    def _toggle_active_region(self, name, checked):
        self.active_regions[name] = checked
        active_count = sum(1 for val in self.active_regions.values() if val)
        self.btn_select_regions.setText(f" Select Regions ({active_count})")
        self.update_text_patterns()

    def _show_engine_status_popup(self):
        """Displays the detailed Engine & Environment Status dialog."""
        dialog = EngineStatusDialog(self.scanner, self)
        dialog.exec()

    def _show_people_selector(self):
        if not self.scanner: return
        
        from PySide6.QtWidgets import QMenu, QWidgetAction, QCheckBox, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QLabel
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #1F2937; color: #E5E7EB; border: 1px solid #374151; padding: 10px; border-radius: 8px; }
        """)
        
        # Get all identities.
        all_names = sorted(self.scanner.identity_manager.identity_map.values())
        
        if not all_names:
            menu.addAction("No identities found").setEnabled(False)
        else:
            container = QWidget()
            container.setStyleSheet("background: transparent;")
            layout = QVBoxLayout(container)
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setSpacing(8)
            
            # Header label.
            lbl_header = QLabel("Target Selection")
            lbl_header.setStyleSheet("font-size: 11px; font-weight: bold; color: #10B981; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;")
            layout.addWidget(lbl_header)
            
            from PySide6.QtWidgets import QLineEdit
            txt_search = QLineEdit()
            txt_search.setPlaceholderText("Search people...")
            txt_search.setStyleSheet("""
                QLineEdit {
                    background-color: #1F2937;
                    border: 1px solid #374151;
                    border-radius: 6px;
                    padding: 5px 8px;
                    color: #E5E7EB;
                    font-size: 11px;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    margin-bottom: 4px;
                }
                QLineEdit:focus { border-color: #10B981; }
            """)
            layout.addWidget(txt_search)
            
            # Checkboxes.
            checkboxes = []
            for name in all_names:
                chk = QCheckBox(name)
                chk.setCursor(Qt.PointingHandCursor)
                chk.setChecked(name in self.scanner.target_identities)
                chk.setStyleSheet("""
                    QCheckBox { spacing: 8px; color: #E5E7EB; font-size: 13px; font-family: 'Segoe UI', Arial, sans-serif; }
                    QCheckBox::indicator { width: 16px; height: 16px; border-radius: 4px; border: 1px solid #374151; background-color: #1F2937; }
                    QCheckBox::indicator:hover { border-color: #4B5563; }
                    QCheckBox::indicator:checked { background-color: #10B981; border-color: #10B981; }
                """)
                
                def make_toggle_cb(n, cb_widget):
                    return lambda checked: self._toggle_target_identity(n, checked)
                chk.toggled.connect(make_toggle_cb(name, chk))
                layout.addWidget(chk)
                checkboxes.append(chk)
                
            def filter_checkboxes(text):
                text = text.lower().strip()
                for cb in checkboxes:
                    cb.setHidden(text not in cb.text().lower())
                menu.adjustSize()
            txt_search.textChanged.connect(filter_checkboxes)
                
            # Quick actions layout.
            layout.addSpacing(4)
            btn_layout = QHBoxLayout()
            btn_layout.setSpacing(8)
            
            btn_all = QPushButton("Select All")
            btn_all.setCursor(Qt.PointingHandCursor)
            btn_all.setStyleSheet("""
                QPushButton {
                    background-color: #1F2937;
                    color: #10B981;
                    border: 1px solid #374151;
                    border-radius: 6px;
                    padding: 4px 8px;
                    font-size: 11px;
                    font-weight: 600;
                }
                QPushButton:hover { background-color: #10B981; color: white; border-color: #10B981; }
                QPushButton:pressed { background-color: #059669; }
            """)
            
            def on_select_all():
                self.scanner.target_identities = list(all_names)
                for cb in checkboxes:
                    cb.blockSignals(True)
                    cb.setChecked(True)
                    cb.blockSignals(False)
                if self.scanner:
                    self.scanner._scan_cache.clear()
                self._rescan_current()
            btn_all.clicked.connect(on_select_all)
            
            btn_clear = QPushButton("Clear")
            btn_clear.setCursor(Qt.PointingHandCursor)
            btn_clear.setStyleSheet("""
                QPushButton {
                    background-color: #1F2937;
                    color: #E11D48;
                    border: 1px solid #374151;
                    border-radius: 6px;
                    padding: 4px 8px;
                    font-size: 11px;
                    font-weight: 600;
                }
                QPushButton:hover { background-color: #E11D48; color: white; border-color: #E11D48; }
                QPushButton:pressed { background-color: #BE123C; }
            """)
            
            def on_clear_all():
                self.scanner.target_identities = []
                for cb in checkboxes:
                    cb.blockSignals(True)
                    cb.setChecked(False)
                    cb.blockSignals(False)
                if self.scanner:
                    self.scanner._scan_cache.clear()
                self._rescan_current()
            btn_clear.clicked.connect(on_clear_all)
            
            btn_layout.addWidget(btn_all)
            btn_layout.addWidget(btn_clear)
            layout.addLayout(btn_layout)
            
            wa = QWidgetAction(menu)
            wa.setDefaultWidget(container)
            menu.addAction(wa)

        menu.exec(self.btn_select_people.mapToGlobal(self.btn_select_people.rect().bottomLeft()))

    def _toggle_target_identity(self, name, checked):
        if checked:
            if name not in self.scanner.target_identities:
                self.scanner.target_identities.append(name)
        else:
            if name in self.scanner.target_identities:
                self.scanner.target_identities.remove(name)
        print(f"Target identities: {self.scanner.target_identities}")
        if self.scanner:
            self.scanner._scan_cache.clear()
        self._rescan_current()

    def _clear_target_identities(self):
        self.scanner.target_identities = []
        if self.scanner:
            self.scanner._scan_cache.clear()
        self._rescan_current()

    def _rescan_current(self):
        """Re-scan the currently loaded image with current settings."""
        if not self.current_file_path:
            return
            
        # Cache manual boxes before rescanning.
        manuals = self.preview_widget.active_hits.copy()
        ckey = self.get_current_cache_key()
        self.user_selections_cache[ckey] = {
            "active_hits": manuals,
            "reviewed": False
        }
        
        pdf_words = None
        if hasattr(self, "active_pdf_pages") and self.active_pdf_pages and self.active_pdf_index < len(self.active_pdf_pages):
            page_data = self.active_pdf_pages[self.active_pdf_index]
            if isinstance(page_data, dict):
                pdf_words = page_data.get("words", None)
                
        show_anim = True
        if hasattr(self.scanner, "text_detector") and self.scanner.text_detector.cached_image_path == self.current_file_path:
            show_anim = False
            
        try:
            cache_key = self.get_current_cache_key()
            hits = self.run_scan_with_overlay(self.current_file_path, pdf_words=pdf_words, show_animation=show_anim, cache_key=cache_key)
            self.current_hits = hits
            is_pdf = bool(self.active_pdf_pages)
            pdf_source = self.active_pdf_source if is_pdf else None
            
            cached_data = self.user_selections_cache.get(cache_key, None)
            if isinstance(cached_data, dict):
                cached_active_hits = cached_data.get("active_hits", None)
                reviewed = cached_data.get("reviewed", False)
            else:
                cached_active_hits = cached_data
                reviewed = False
                
            self.preview_widget.display_hits(hits, is_pdf=is_pdf, pdf_source=pdf_source, cached_active_hits=cached_active_hits, reviewed=reviewed)
            self.btn_redact_next.setEnabled(bool(hits))
        except Exception as e:
            print(f"Re-scan failed: {e}")

    def add_files(self):
        exts = " ".join([f"*{ext}" for ext in SUPPORTED_EXTENSIONS])
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files", "", f"Supported ({exts})")
        if files:
            self.add_dropped_paths(files)

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.add_dropped_paths([folder])

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [url.toLocalFile() for url in event.mimeData().urls()]
        self.add_dropped_paths(paths)

    def add_dropped_paths(self, paths):
        for path in paths:
            if os.path.isdir(path):
                # Recursively add supported files.
                for root, _, files in os.walk(path):
                    for f in files:
                        if f.lower().endswith(tuple(SUPPORTED_EXTENSIONS)):
                            full_p = os.path.join(root, f)
                            if not self.is_path_in_list(full_p):
                                item = QListWidgetItem(os.path.basename(full_p))
                                item.setData(Qt.UserRole, full_p)
                                item.setToolTip(full_p)
                                self.file_list.addItem(item)
            else:
                if path.lower().endswith(tuple(SUPPORTED_EXTENSIONS)):
                    if not self.is_path_in_list(path):
                        item = QListWidgetItem(os.path.basename(path))
                        item.setData(Qt.UserRole, path)
                        item.setToolTip(path)
                        self.file_list.addItem(item)
        
        self.update_stats()

    def is_path_in_list(self, path):
        for i in range(self.file_list.count()):
            if self.file_list.item(i).data(Qt.UserRole) == path:
                return True
        return False


    def remove_selected_file(self):
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            return
            
        for item in selected_items:
            path = item.data(Qt.UserRole)
            # Clear preview if removed item is currently loaded.
            if path == self.current_file_path:
                self.preview_widget.clear_preview()
                self.current_file_path = None
                self.current_hits = []
                
            row = self.file_list.row(item)
            self.file_list.takeItem(row)
            keys_to_remove = [k for k in self.user_selections_cache if k == path or k.startswith(f"{path}_page_")]
            for k in keys_to_remove:
                self.user_selections_cache.pop(k, None)
            
            # Handle batch mode index adjustment.
            if self.is_batch_mode:
                if row < self.batch_index:
                    self.batch_index -= 1
                elif row == self.batch_index:
                    # Advance batch if current item was removed.
                    self.load_next_batch_item()
        self.update_stats()
        self.update_toolbar_state()

    def clear_queue(self):
        self.file_list.clear()
        self.preview_widget.clear_preview()
        self.current_file_path = None
        self.current_hits = []
        self.user_selections_cache.clear()
        self.update_toolbar_state()
        
        # Reset batch mode if active
        if self.is_batch_mode:
            self.cancel_batch_mode()
        self.update_stats()

    def on_paste(self):
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if mime_data.hasImage():
            image = clipboard.image()
            if image.isNull():
                return
            
            # Use system temp directory
            import tempfile
            temp_dir = os.path.join(tempfile.gettempdir(), "safemarc_temp", "clipboard")
            os.makedirs(temp_dir, exist_ok=True)
            
            # Create unique filename
            import time
            timestamp = int(time.time() * 1000)
            temp_path = os.path.join(temp_dir, f"paste_{timestamp}.png")
            
            if image.save(temp_path, "PNG"):
                print(f"Pasted image from clipboard to: {temp_path}")
                self.add_dropped_paths([temp_path])
                
                # Optional: select the new item and load it
                for i in range(self.file_list.count()):
                    item = self.file_list.item(i)
                    if item.data(Qt.UserRole) == temp_path:
                        self.file_list.setCurrentItem(item)
                        self.on_file_selected(item)
                        break
            else:
                QMessageBox.warning(self, "Error", "Failed to save image from clipboard.")
        elif mime_data.hasUrls():
            paths = [url.toLocalFile() for url in mime_data.urls()]
            self.add_dropped_paths(paths)
        else:
            QMessageBox.information(self, "Clipboard", "No image or file found in clipboard.")


    def on_file_selected(self, item):
        # If user manually clicks an item during batch mode, cancel batch mode
        if self.is_batch_mode and self.file_list.row(item) != self.batch_index:
            self.cancel_batch_mode()
            
        if self.current_file_path:
            manuals = self.preview_widget.active_hits.copy()
            ckey = self.get_current_cache_key()
            self.user_selections_cache[ckey] = {
                "active_hits": manuals,
                "reviewed": False
            }
                
        file_path = item.data(Qt.UserRole)
        is_pdf = file_path.lower().endswith('.pdf')
        if not is_pdf:
            self.active_pdf_pages = []
            self.active_pdf_outputs = []
            self.active_pdf_index = -1
            self.active_pdf_source = None
            
        self.current_file_path = file_path
        self.current_hits = []
        
        # Load preview
        if is_pdf:
            try:
                preview_page = PDFHandler.extract_first_page(file_path)
                if preview_page:
                    self.preview_widget.load_image(preview_page)
            except Exception as e:
                print(f"Failed to load PDF preview: {e}")
        elif file_path.lower().endswith(tuple(SUPPORTED_EXTENSIONS)):
            self.preview_widget.load_image(file_path)
            
        # Restore any cached manual boxes or scan results for this newly selected file
        ckey = self.get_current_cache_key(file_path)
        has_scanner_cache = self.scanner and ckey in self.scanner._scan_cache
        has_selection_cache = ckey in self.user_selections_cache
        
        if has_scanner_cache:
            hits = self.run_scan_with_overlay(file_path, cache_key=ckey)
            self.current_hits = hits
            
            cached_active_hits = None
            reviewed = False
            if has_selection_cache:
                cached_data = self.user_selections_cache[ckey]
                if isinstance(cached_data, dict):
                    cached_active_hits = cached_data.get("active_hits", None)
                    reviewed = cached_data.get("reviewed", False)
                else:
                    cached_active_hits = cached_data
            
            self.preview_widget.display_hits(
                hits,
                is_pdf=is_pdf,
                pdf_source=self.active_pdf_source if is_pdf else None,
                cached_active_hits=cached_active_hits,
                reviewed=reviewed
            )
        elif has_selection_cache:
            cached_data = self.user_selections_cache[ckey]
            if isinstance(cached_data, dict):
                cached_hits = cached_data.get("active_hits", [])
                reviewed = cached_data.get("reviewed", False)
            else:
                cached_hits = cached_data
                reviewed = False
            
            if cached_hits:
                self.preview_widget.display_hits(
                    cached_hits,
                    is_pdf=is_pdf,
                    pdf_source=self.active_pdf_source if is_pdf else None,
                    cached_active_hits=cached_hits,
                    reviewed=reviewed
                )
        self.update_toolbar_state()

    def get_current_cache_key(self, path=None):
        if not path:
            path = self.current_file_path
        if not path:
            return None
        if self.active_pdf_pages and self.active_pdf_source:
            for idx, page_data in enumerate(self.active_pdf_pages):
                page_path = page_data["image_path"] if isinstance(page_data, dict) else page_data
                if page_path == path:
                    return f"{self.active_pdf_source}_page_{idx}"
        return path

    def get_redacted_output_path(self, input_path: str) -> str:
        from PySide6.QtCore import QSettings, QStandardPaths
        settings = QSettings("SafeMARC", "SafeMARC")
        
        always_global = settings.value("always_use_global_output", "false") == "true" or settings.value("always_use_global_output", False) is True
        
        global_dir = settings.value("global_output_dir", "")
        if not global_dir:
            pictures_dir = QStandardPaths.writableLocation(QStandardPaths.PicturesLocation)
            if not pictures_dir:
                pictures_dir = os.path.expanduser("~/Pictures")
            global_dir = os.path.join(pictures_dir, "SafeMARC_Output")
            settings.setValue("global_output_dir", global_dir)
            
        os.makedirs(global_dir, exist_ok=True)
        
        import tempfile
        is_temp = input_path.startswith(tempfile.gettempdir())
        
        if always_global or is_temp:
            return self.processor.get_output_path(
                input_path,
                output_dir=global_dir,
                use_suffix=self.chk_suffix.isChecked()
            )
        else:
            return self.processor.get_output_path(
                input_path,
                use_suffix=self.chk_suffix.isChecked()
            )

    def run_scan_with_overlay(self, path, pdf_words=None, show_animation=True, cache_key=None):
        ckey = cache_key if cache_key else path
        if self.scanner and ckey in self.scanner._scan_cache:
            # Instant cache hit!
            merged_hits = list(self.scanner._scan_cache[ckey])
            # Inject persistent manual hits from the preview widget
            for ph in self.preview_widget.persistent_manual_hits:
                if not any(ph.x == h.x and ph.y == h.y and ph.w == h.w and ph.h == h.h for h in merged_hits):
                    merged_hits.append(ph)
            # Inject cached MANUAL hits (user-drawn boxes) that the AI wouldn't re-detect
            if ckey in self.user_selections_cache:
                cached_data = self.user_selections_cache[ckey]
                cached_hits = cached_data.get("active_hits", []) if isinstance(cached_data, dict) else cached_data
                for ch in cached_hits:
                    if ch.label == "MANUAL" and not any(ch.x == h.x and ch.y == h.y and ch.w == h.w and ch.h == h.h for h in merged_hits):
                        merged_hits.append(ch)
            return merged_hits

        if show_animation:
            self.preview_widget.show_loading("Scanning document for sensitive data...")
        from PySide6.QtCore import QEventLoop
        loop = QEventLoop()
        
        worker = ScanWorker(self.scanner, path, pdf_words, cache_key=cache_key)
        worker.finished.connect(loop.quit)
        worker.error.connect(loop.quit)
        
        worker.start()
        loop.exec()
        
        worker.wait()
        
        if show_animation:
            self.preview_widget.hide_loading()
            
        # Start with AI-detected hits
        merged_hits = list(worker.hits)
        
        # Inject persistent manual hits from the preview widget
        for ph in self.preview_widget.persistent_manual_hits:
            if not any(ph.x == h.x and ph.y == h.y and ph.w == h.w and ph.h == h.h for h in merged_hits):
                merged_hits.append(ph)
        
        # Inject cached MANUAL hits (user-drawn boxes) that the AI wouldn't re-detect
        if ckey in self.user_selections_cache:
            cached_data = self.user_selections_cache[ckey]
            cached_hits = cached_data.get("active_hits", []) if isinstance(cached_data, dict) else cached_data
            for ch in cached_hits:
                if ch.label == "MANUAL" and not any(ch.x == h.x and ch.y == h.y and ch.w == h.w and ch.h == h.h for h in merged_hits):
                    merged_hits.append(ch)
                
        return merged_hits

    def redact_current(self):
        if not self.scanner or not self.current_file_path:
            return

        # Explicitly cache manual hits BEFORE any redaction processing
        manuals = self.preview_widget.active_hits.copy()
        ckey = self.get_current_cache_key()
        self.user_selections_cache[ckey] = {
            "active_hits": manuals,
            "reviewed": True
        }

        selected_hits = self.preview_widget.get_selected_hits()   
        if not selected_hits:
            QMessageBox.warning(self, "Warning", "No hits selected for redaction.")
            return

        out_path = self.get_redacted_output_path(self.current_file_path)
        
        # Handle PDF sub-loop
        if self.active_pdf_pages:
            import tempfile
            redacted_dir = os.path.join(tempfile.gettempdir(), "safemarc_temp", "redacted")
            os.makedirs(redacted_dir, exist_ok=True)
            fd, temp_path = tempfile.mkstemp(suffix=".png", dir=redacted_dir)
            os.close(fd)
            success = self.scanner.redact(self.current_file_path, temp_path, selected_hits)
            if success:
                self.active_pdf_has_redactions = True
                self.active_pdf_outputs.append(temp_path)
                self.active_pdf_index += 1
                self.load_next_batch_item()
            else:
                QMessageBox.warning(self, "Error", "Failed to redact PDF page.")
            return
        
        success = self.scanner.redact(self.current_file_path, out_path, selected_hits)
        if success:
            self.batch_success_count += 1
            self.file_list.item(self.batch_index).setForeground(QColor("#4CAF50"))
            self.batch_index += 1
            self.load_next_batch_item()
        else:
            QMessageBox.warning(self, "Error", "Failed to redact image.")

    def start_batch(self):
        if not self.processor or self.file_list.count() == 0:
            QMessageBox.warning(self, "Warning", "Queue is empty.")
            return

        if self.current_file_path:
            manuals = self.preview_widget.active_hits.copy()
            ckey = self.get_current_cache_key()
            self.user_selections_cache[ckey] = {
                "active_hits": manuals,
                "reviewed": False
            }

        self.is_batch_mode = True
        self.batch_index = 0
        self.batch_success_count = 0

        for i in range(self.file_list.count()):
            from PySide6.QtGui import QColor
            self.file_list.item(i).setForeground(QColor("#E5E7EB"))
            
        has_pdf = any(self.file_list.item(i).data(Qt.UserRole).lower().endswith('.pdf') for i in range(self.file_list.count()))
        if has_pdf:
            QMessageBox.information(self, "PDF Rasterization", "PDFs in the queue will be rasterized to guarantee redaction security. Hidden text layers and vectors will be destroyed.")

        self.file_list.setEnabled(False)
        
        # Disable sidebar/toolbar controls during batch review
        self.btn_settings.setEnabled(False)
        self.btn_add_file.setEnabled(False)
        self.btn_add_folder.setEnabled(False)
        self.btn_paste.setEnabled(False)
        self.btn_remove.setEnabled(False)
        self.btn_clear.setEnabled(False)

        # Clear any widget focus so no button/control has auto-focus
        focused = QApplication.focusWidget()
        if focused:
            focused.clearFocus()
        self.setFocus()

        # Update UI state
        self.btn_start_review.hide()
        self.btn_previous.show()
        self.btn_skip.show()
        self.btn_skip.setEnabled(True)
        self.btn_redact_next.show()
        self.btn_redact_next.setEnabled(False)
        self.btn_stop_review.show()
        
        self.load_next_batch_item()

    def skip_current(self):
        if not self.is_batch_mode:
            return
            
        # Explicitly cache manual hits BEFORE skipping
        if self.current_file_path:
            manuals = self.preview_widget.active_hits.copy()
            ckey = self.get_current_cache_key()
            self.user_selections_cache[ckey] = {
                "active_hits": manuals,
                "reviewed": True
            }
            
        if self.active_pdf_pages:
            from PySide6.QtWidgets import QMessageBox
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Skip Action")
            msg_box.setText("Would you like to skip only the current page or the entire PDF?")
            btn_page = msg_box.addButton("Current Page", QMessageBox.AcceptRole)
            btn_pdf = msg_box.addButton("Entire PDF", QMessageBox.ActionRole)
            btn_cancel = msg_box.addButton("Cancel", QMessageBox.RejectRole)
            msg_box.setStyleSheet("""
                QMessageBox { background-color: #0B0F19; }
                QMessageBox QLabel { color: #F3F4F6; font-size: 13px; background: transparent; }
                QPushButton {
                    background-color: #1F2937;
                    color: #E5E7EB;
                    border: 1px solid #374151;
                    border-radius: 8px;
                    padding: 6px 14px;
                    font-weight: 600;
                    font-size: 13px;
                }
                QPushButton:hover { background-color: #374151; border-color: #4B5563; color: #FFFFFF; }
                QPushButton:focus { background-color: #374151; border-color: #10B981; color: #FFFFFF; }
            """)
            msg_box.exec()
            
            if msg_box.clickedButton() == btn_page:
                self.active_pdf_outputs.append(self.current_file_path)
                self.active_pdf_index += 1
                self.load_next_batch_item()
                return
            elif msg_box.clickedButton() == btn_pdf:
                self.active_pdf_pages = []
                self.active_pdf_outputs = []
                self.active_pdf_index = 0
            else:
                return
            
        self.file_list.item(self.batch_index).setForeground(QColor("#888888"))
        self.batch_index += 1
        self.load_next_batch_item()

    def go_previous(self):
        if not self.is_batch_mode:
            return
            
        self.is_navigating_backward = True
        
        # Explicitly cache manual hits BEFORE going previous
        if self.current_file_path:
            manuals = self.preview_widget.active_hits.copy()
            ckey = self.get_current_cache_key()
            self.user_selections_cache[ckey] = {
                "active_hits": manuals,
                "reviewed": True
            }
            
        # Scenario A: Inside a PDF sub-loop
        if self.active_pdf_pages and self.active_pdf_index > 0:
            if self.active_pdf_outputs:
                self.active_pdf_outputs.pop()
            self.active_pdf_index -= 1
            self.load_next_batch_item()
            return
            
        # Scenario B: Moving to the previous queue item
        if self.batch_index > 0:
            if self.active_pdf_pages and self.active_pdf_index == 0:
                self.active_pdf_pages = []
                self.active_pdf_outputs = []
                self.active_pdf_index = 0
                self.active_pdf_source = None
            
            prev_index = self.batch_index - 1
            prev_item = self.file_list.item(prev_index)
            prev_path = prev_item.data(Qt.UserRole)
            
            if prev_path.lower().endswith('.pdf'):
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Finished PDF")
                msg_box.setText("The previous item is a completed PDF. Re-entering it will restart from Page 1 to ensure correct PDF compilation.\n\nWhat would you like to do?")
                
                btn_restart = msg_box.addButton("Restart PDF (Page 1)", QMessageBox.AcceptRole)
                btn_skip = msg_box.addButton("Go Back Further", QMessageBox.ActionRole)
                btn_cancel = msg_box.addButton("Cancel", QMessageBox.RejectRole)
                
                msg_box.setStyleSheet("""
                    QMessageBox { background-color: #0B0F19; }
                    QMessageBox QLabel { color: #F3F4F6; font-size: 13px; background: transparent; }
                    QPushButton {
                        background-color: #1F2937;
                        color: #E5E7EB;
                        border: 1px solid #374151;
                        border-radius: 8px;
                        padding: 6px 14px;
                        font-weight: 600;
                        font-size: 13px;
                    }
                    QPushButton:hover { background-color: #374151; border-color: #4B5563; color: #FFFFFF; }
                    QPushButton:focus { background-color: #374151; border-color: #10B981; color: #FFFFFF; }
                """)
                
                msg_box.exec()
                clicked_btn = msg_box.clickedButton()
                
                if clicked_btn == btn_restart:
                    self.is_navigating_backward = False  # Reset to ensure we load page 1 and build sequentially
                    self._undo_queue_item(prev_index)
                    self.batch_index = prev_index
                    self.load_next_batch_item()
                elif clicked_btn == btn_skip:
                    self.is_navigating_backward = True
                    self._undo_queue_item(prev_index)
                    self.batch_index = prev_index
                    self.go_previous()
                else:
                    return
            else:
                self._undo_queue_item(prev_index)
                self.batch_index = prev_index
                self.load_next_batch_item()

    def _undo_queue_item(self, index):
        item = self.file_list.item(index)
        if item.foreground().color() == QColor("#4CAF50"):
            self.batch_success_count -= 1
        item.setData(Qt.ForegroundRole, None)

    def load_next_batch_item(self):
        # Update Previous button state
        can_go_back = bool(self.batch_index > 0 or (self.active_pdf_pages and self.active_pdf_index > 0))
        self.btn_previous.setEnabled(can_go_back)

        is_backward = getattr(self, "is_navigating_backward", False)

        # PDF Sub-loop
        if self.active_pdf_pages:
            if self.active_pdf_index < len(self.active_pdf_pages):
                page_data = self.active_pdf_pages[self.active_pdf_index]
                page_path = page_data["image_path"] if isinstance(page_data, dict) else page_data
                pdf_words = page_data.get("words", None) if isinstance(page_data, dict) else None
                self.current_file_path = page_path
                self.current_hits = []
                self.update_toolbar_state()
                self.title_label.setText(f"🛡️ SafeMARC - Page {self.active_pdf_index + 1}/{len(self.active_pdf_pages)}")
                
                self.preview_widget.load_image(page_path)
                try:
                    cache_key = f"{self.active_pdf_source}_page_{self.active_pdf_index}" if getattr(self, "active_pdf_pages", None) else None
                    hits = self.run_scan_with_overlay(page_path, pdf_words=pdf_words, cache_key=cache_key)
                    self.current_hits = hits
                    if self.chk_skip_review.isChecked():
                        import tempfile
                        redacted_dir = os.path.join(tempfile.gettempdir(), "safemarc_temp", "redacted")
                        os.makedirs(redacted_dir, exist_ok=True)
                        fd, temp_path = tempfile.mkstemp(suffix=".png", dir=redacted_dir)
                        os.close(fd)
                        success = self.scanner.redact(page_path, temp_path, hits)
                        if success:
                            self.active_pdf_outputs.append(temp_path)
                        else:
                            self.active_pdf_outputs.append(page_path)
                        self.active_pdf_index += 1
                        QTimer.singleShot(0, self.load_next_batch_item)
                        return
                    elif not hits and self.chk_auto_skip.isChecked() and not is_backward:
                        self.active_pdf_outputs.append(page_path)
                        self.active_pdf_index += 1
                        QTimer.singleShot(0, self.load_next_batch_item)
                        return
                    else:
                        is_pdf = bool(self.active_pdf_pages)
                        pdf_source = self.active_pdf_source if is_pdf else None
                        
                        cached_data = self.user_selections_cache.get(cache_key, None)
                        if isinstance(cached_data, dict):
                            cached_active_hits = cached_data.get("active_hits", None)
                            reviewed = cached_data.get("reviewed", False)
                        else:
                            cached_active_hits = cached_data
                            reviewed = False
                            
                        self.is_navigating_backward = False
                        self.preview_widget.display_hits(hits, is_pdf=is_pdf, pdf_source=pdf_source, cached_active_hits=cached_active_hits, reviewed=reviewed)
                        self.btn_redact_next.setEnabled(True)
                        
                        # Clear any auto-relocated focus if not focused via keyboard
                        focused = QApplication.focusWidget()
                        if not focused or focused.property("focused_via_keyboard") != "true":
                            if focused:
                                focused.clearFocus()
                            self.setFocus()
                except Exception as e:
                    self.is_navigating_backward = False
                    print(f"Error processing page: {e}")
                    self.active_pdf_outputs.append(page_path)
                    self.active_pdf_index += 1
                    QTimer.singleShot(0, self.load_next_batch_item)
                return
            else:
                # Finished PDF, rebuild
                out_path = self.get_redacted_output_path(
                    self.file_list.item(self.batch_index).data(Qt.UserRole)
                )
                if not self.active_pdf_has_redactions and not self.chk_always_rasterize.isChecked():
                    import shutil
                    try:
                        shutil.copy2(self.file_list.item(self.batch_index).data(Qt.UserRole), out_path)
                        success = True
                    except Exception as e:
                        print(f"Error copying original PDF: {e}")
                        success = False
                else:
                    success = PDFHandler.build_pdf(self.active_pdf_outputs, out_path)

                if success:
                    self.batch_success_count += 1
                    self.file_list.item(self.batch_index).setForeground(QColor("#4CAF50"))
                else:
                    self.file_list.item(self.batch_index).setForeground(QColor("#d32f2f"))
                
                # Cleanup and move to next item
                self.active_pdf_pages = []
                self.active_pdf_outputs = []
                self.batch_index += 1
                self.title_label.setText("🛡️ SafeMARC")
                QTimer.singleShot(0, self.load_next_batch_item)
                return

        # Base case: Finished queue
        if self.batch_index >= self.file_list.count():
            self.is_navigating_backward = False
            final_count = self.batch_success_count
            self.cancel_batch_mode()
            self.title_label.setText("🛡️ SafeMARC")
            QMessageBox.information(self, "Complete", f"Review complete.\nSuccessfully redacted {final_count} files.")
            return
            
        # Highlight current item in the list
        item = self.file_list.item(self.batch_index)
        self.file_list.setCurrentItem(item)
        file_path = item.data(Qt.UserRole)
        
        # Check if it's a PDF
        if file_path.lower().endswith('.pdf'):
            try:
                self.active_pdf_source = file_path
                self.active_pdf_pages = PDFHandler.extract_pages(file_path)
                if is_backward:
                    self.active_pdf_index = len(self.active_pdf_pages) - 1
                else:
                    self.active_pdf_index = 0
                self.active_pdf_outputs = []
                self.active_pdf_has_redactions = False
                QTimer.singleShot(0, self.load_next_batch_item)
                return
            except Exception as e:
                self.is_navigating_backward = False
                item.setForeground(QColor("#d32f2f"))
                print(f"Error extracting PDF: {e}")
                self.batch_index += 1
                QTimer.singleShot(0, self.load_next_batch_item)
                return
        
        self.current_file_path = file_path
        self.current_hits = []
        
        # Clear PDF state for standard image
        self.active_pdf_pages = []
        self.active_pdf_outputs = []
        self.active_pdf_index = -1
        self.active_pdf_source = None
        
        self.update_toolbar_state()
        
        # Attempt to load and auto-scan
        if file_path.lower().endswith(tuple(SUPPORTED_EXTENSIONS)):
            self.preview_widget.load_image(file_path)
            
            try:
                hits = self.run_scan_with_overlay(file_path)
                self.current_hits = hits
                if self.chk_skip_review.isChecked():
                    out_path = self.get_redacted_output_path(file_path)
                    success = self.scanner.redact(file_path, out_path, hits)
                    if success:
                        self.batch_success_count += 1
                        self.file_list.item(self.batch_index).setForeground(QColor("#4CAF50"))
                    else:
                        self.file_list.item(self.batch_index).setForeground(QColor("#d32f2f"))
                    self.batch_index += 1
                    QTimer.singleShot(0, self.load_next_batch_item)
                    return
                elif not hits and self.chk_auto_skip.isChecked() and not is_backward:
                    self.file_list.item(self.batch_index).setForeground(QColor("#888888"))
                    self.batch_index += 1
                    QTimer.singleShot(0, self.load_next_batch_item)
                    return
                else:
                    is_pdf = bool(self.active_pdf_pages)
                    pdf_source = self.active_pdf_source if is_pdf else None
                    
                    ckey = self.get_current_cache_key(file_path)
                    cached_data = self.user_selections_cache.get(ckey, None)
                    if isinstance(cached_data, dict):
                        cached_active_hits = cached_data.get("active_hits", None)
                        reviewed = cached_data.get("reviewed", False)
                    else:
                        cached_active_hits = cached_data
                        reviewed = False
                        
                    self.is_navigating_backward = False
                    self.preview_widget.display_hits(hits, is_pdf=is_pdf, pdf_source=pdf_source, cached_active_hits=cached_active_hits, reviewed=reviewed)
                    self.btn_redact_next.setEnabled(True)
                    
                    # Clear any auto-relocated focus if not focused via keyboard
                    focused = QApplication.focusWidget()
                    if not focused or focused.property("focused_via_keyboard") != "true":
                        if focused:
                            focused.clearFocus()
                        self.setFocus()
            except Exception as e:
                self.is_navigating_backward = False
                item.setForeground(QColor("#d32f2f"))
                print(f"Error processing {file_path}: {e}")
                self.batch_index += 1
                QTimer.singleShot(0, self.load_next_batch_item)
        else:
            # Skip unhandled file types for now
            self.is_navigating_backward = False
            self.batch_index += 1
            QTimer.singleShot(0, self.load_next_batch_item)

    def update_stats(self):
        count = self.file_list.count()
        self.lbl_count.setText(f"Files: {count}")
        if hasattr(self, "txt_queue_search"):
            self.txt_queue_search.setVisible(count > 0)

    def cleanup_temp_resources(self, full=False):
        print(f"[SafeMARC] Cleaning up temporary resources (full={full})...")
        import shutil
        import tempfile
        safemarc_temp = os.path.join(tempfile.gettempdir(), "safemarc_temp")
        if os.path.exists(safemarc_temp):
            if full:
                try:
                    shutil.rmtree(safemarc_temp)
                    print("[SafeMARC] Successfully cleaned up entire safemarc_temp directory.")
                except Exception as e:
                    print(f"[SafeMARC] Error cleaning up temporary directory: {e}")
            else:
                # Keep clipboard images intact so queue is not broken, only clean intermediate pdf/redacted
                for sub in ["pdf", "redacted"]:
                    sub_path = os.path.join(safemarc_temp, sub)
                    if os.path.exists(sub_path):
                        try:
                            shutil.rmtree(sub_path)
                            print(f"[SafeMARC] Cleaned up temporary {sub} directory.")
                        except Exception as e:
                            print(f"[SafeMARC] Error cleaning up {sub}: {e}")

    def closeEvent(self, event):
        self.cleanup_temp_resources(full=True)
        event.accept()

    def showEvent(self, event):
        super().showEvent(event)
        self.setFocus()




class PersistentRangeDialog(QDialog):
    def __init__(self, is_pdf: bool, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Persistent Scope Settings")
        self.setFixedSize(420, 260)
        self.setStyleSheet("""
            QDialog { background-color: #0B0F19; border: 1px solid #1F2937; border-radius: 12px; }
            QLabel { color: #E5E7EB; font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; }
            QLabel#title { color: #10B981; font-size: 15px; font-weight: bold; }
            QRadioButton {
                color: #E5E7EB;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
                padding: 4px;
                background: transparent;
            }
            QRadioButton:hover { color: #FFFFFF; }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border-radius: 8px;
                border: 2px solid #374151;
            }
            QRadioButton::indicator:checked {
                background-color: #10B981;
                border: 2px solid #10B981;
            }
            QPushButton {
                background-color: #1F2937;
                color: #E5E7EB;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 4px 12px;
                font-weight: 600;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
                min-width: 80px;
                min-height: 28px;
            }
            QPushButton:hover { background-color: #374151; border-color: #4B5563; color: #FFFFFF; }
            QPushButton#btnSave { background-color: #10B981; color: white; border: none; }
            QPushButton#btnSave:hover { background-color: #059669; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        title = QLabel("Persistent Redaction Scope")
        title.setObjectName("title")
        layout.addWidget(title)
        
        desc = QLabel("How would you like manual redaction boxes to persist?")
        desc.setStyleSheet("color: #9CA3AF; font-size: 12px;")
        layout.addWidget(desc)
        
        self.radio_group = QButtonGroup(self)
        
        if is_pdf:
            self.opt1 = QRadioButton("Apply to current PDF only (all pages)")
            self.opt2 = QRadioButton("Apply to current PDF and upcoming PDFs")
            self.opt3 = QRadioButton("Apply to all upcoming items (including images)")
            self.opt1.setChecked(True)
            self.options = [("current_pdf_only", self.opt1), ("pdf_upcoming", self.opt2), ("all_upcoming", self.opt3)]
        else:
            self.opt1 = QRadioButton("Apply to upcoming images only")
            self.opt2 = QRadioButton("Apply to all upcoming items (including PDFs)")
            self.opt1.setChecked(True)
            self.options = [("image_upcoming", self.opt1), ("all_upcoming", self.opt2)]
            
        for val, radio in self.options:
            radio.setFocusPolicy(Qt.TabFocus)
            self.radio_group.addButton(radio)
            layout.addWidget(radio)
            
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setFocusPolicy(Qt.TabFocus)
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_save = QPushButton("Apply")
        self.btn_save.setObjectName("btnSave")
        self.btn_save.setFocusPolicy(Qt.TabFocus)
        self.btn_save.setDefault(True)
        self.btn_save.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)
        
        # Configure tab order explicitly
        prev_radio = None
        for val, radio in self.options:
            if prev_radio:
                self.setTabOrder(prev_radio, radio)
            prev_radio = radio
        self.setTabOrder(prev_radio, self.btn_cancel)
        self.setTabOrder(self.btn_cancel, self.btn_save)
        apply_focus_indicators(self)
        
    def get_selected_scope(self) -> str:
        for val, radio in self.options:
            if radio.isChecked():
                return val
        return "all_upcoming"

