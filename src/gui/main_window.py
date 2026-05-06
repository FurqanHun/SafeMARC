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
)
from PySide6.QtCore import Qt, QSize, QTimer, QThread, Signal
from PySide6.QtGui import QFont, QIcon, QColor, QKeySequence

from src.core.scanner import SafeScanner
from src.core.batch_processor import BatchProcessor, SUPPORTED_EXTENSIONS
from src.utils.pdf_handler import PDFHandler
from src.gui.preview_widget import PreviewWidget
from src.gui.settings_dialog import SettingsDialog

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

SVG_REFRESH = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E5E7EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 21v-5h5"/></svg>'''
SVG_CLIPBOARD = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E5E7EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/></svg>'''
SVG_FACE = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E5E7EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'''


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

    def __init__(self, scanner, file_path, pdf_words=None):
        super().__init__()
        self.scanner = scanner
        self.file_path = file_path
        self.pdf_words = pdf_words
        self.hits = []

    def run(self):
        try:
            self.hits = self.scanner.scan(self.file_path, pdf_words=self.pdf_words)
            self.finished.emit()
        except Exception as e:
            self.error.emit(e)


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

        # Core Engines
        try:
            self.scanner = SafeScanner()
            self.processor = BatchProcessor(self.scanner)
            engine_status = "AI Engine: Online"
            is_online = True
        except Exception as e:
            self.scanner = None
            self.processor = None
            engine_status = "AI Engine Error"
            is_online = False

        # Central Widget & Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
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

        self.status_label = QLabel(engine_status)
        if is_online:
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
        else:
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
        
        lbl_text_title = QLabel("TEXT REDACTION")
        lbl_text_title.setStyleSheet("font-weight: 700; font-size: 11px; color: #10B981; letter-spacing: 0.5px; text-transform: uppercase;")
        text_layout.addWidget(lbl_text_title)
        
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

        btn_add_text = QPushButton(" Add Text")
        btn_add_text.setIcon(svg_to_icon(SVG_PLUS))
        btn_add_text.clicked.connect(lambda: self.add_pattern_row(is_regex=False))
        btn_add_regex = QPushButton(" Add Regex")
        btn_add_regex.setIcon(svg_to_icon(SVG_PLUS))
        btn_add_regex.clicked.connect(lambda: self.add_pattern_row(is_regex=True))
        
        for b in (btn_add_text, btn_add_regex):
            b.setStyleSheet("""
                QPushButton {
                    background-color: #1F2937;
                    color: #E5E7EB;
                    border: 1px solid #374151;
                    border-radius: 8px;
                    padding: 8px 12px;
                    font-weight: 600;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #374151;
                    border-color: #4B5563;
                    color: #FFFFFF;
                }
            """)
        
        text_btns = QHBoxLayout()
        text_btns.addWidget(btn_add_text)
        text_btns.addWidget(btn_add_regex)
        text_layout.addLayout(text_btns)
        
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
        self.btn_draw_mode = QPushButton(" Draw Box (D)")
        self.btn_draw_mode.setIcon(svg_to_icon(SVG_DRAW))
        self.btn_draw_mode.setCheckable(True)
        self.btn_draw_mode.clicked.connect(self.toggle_draw_mode)
        
        self.btn_zoom_in = QPushButton(" Zoom In")
        self.btn_zoom_in.setIcon(svg_to_icon(SVG_ZOOM_IN))
        self.btn_zoom_in.clicked.connect(self.preview_widget.zoom_in)
        
        self.btn_zoom_out = QPushButton(" Zoom Out")
        self.btn_zoom_out.setIcon(svg_to_icon(SVG_ZOOM_OUT))
        self.btn_zoom_out.clicked.connect(self.preview_widget.zoom_out)
        
        self.btn_reset_zoom = QPushButton(" Reset")
        self.btn_reset_zoom.setIcon(svg_to_icon(SVG_REFRESH))
        self.btn_reset_zoom.clicked.connect(self.preview_widget.reset_zoom)

        tool_style = """
            QPushButton {
                background-color: #1F2937;
                color: #E5E7EB;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 8px 14px;
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
        """

        for btn in (self.btn_draw_mode, self.btn_zoom_in, self.btn_zoom_out, self.btn_reset_zoom):
            btn.setStyleSheet(tool_style)

        draw_layout.addWidget(self.btn_draw_mode)
        draw_layout.addWidget(self.btn_zoom_in)
        draw_layout.addWidget(self.btn_zoom_out)
        draw_layout.addWidget(self.btn_reset_zoom)
        preview_layout.addLayout(draw_layout)
        
        # Shortcuts
        from PySide6.QtGui import QShortcut
        self.shortcut_draw = QShortcut(QKeySequence("D"), self)
        self.shortcut_draw.activated.connect(self.btn_draw_mode.click)

        self.shortcut_zoom_in = QShortcut(QKeySequence("Ctrl+="), self)
        self.shortcut_zoom_in.activated.connect(self.preview_widget.zoom_in)

        self.shortcut_zoom_in2 = QShortcut(QKeySequence("Ctrl++"), self)
        self.shortcut_zoom_in2.activated.connect(self.preview_widget.zoom_in)

        self.shortcut_zoom_out = QShortcut(QKeySequence("Ctrl+-"), self)
        self.shortcut_zoom_out.activated.connect(self.preview_widget.zoom_out)

        self.shortcut_zoom_reset = QShortcut(QKeySequence("Ctrl+0"), self)
        self.shortcut_zoom_reset.activated.connect(self.preview_widget.reset_zoom)

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
        self.shortcut_start_redact = QShortcut(QKeySequence("Return"), self)
        self.shortcut_start_redact.activated.connect(self.on_return_pressed)
        
        self.shortcut_start_redact_ent = QShortcut(QKeySequence("Enter"), self)
        self.shortcut_start_redact_ent.activated.connect(self.on_return_pressed)

        # Skip Shortcuts (Space or S)
        self.shortcut_skip_space = QShortcut(QKeySequence("Space"), self)
        self.shortcut_skip_space.activated.connect(self.btn_skip.click)

        self.shortcut_skip_s = QShortcut(QKeySequence("S"), self)
        self.shortcut_skip_s.activated.connect(self.btn_skip.click)

        # Previous Shortcuts (Backspace or P)
        self.shortcut_prev_bs = QShortcut(QKeySequence("Backspace"), self)
        self.shortcut_prev_bs.activated.connect(self.btn_previous.click)

        self.shortcut_prev_p = QShortcut(QKeySequence("P"), self)
        self.shortcut_prev_p.activated.connect(self.btn_previous.click)

        self.shortcut_escape = QShortcut(QKeySequence("Escape"), self)
        self.shortcut_escape.activated.connect(self.on_escape_pressed)

        # Global Application Shortcuts
        self.shortcut_add_file = QShortcut(QKeySequence("Ctrl+O"), self)
        self.shortcut_add_file.activated.connect(self.add_files)

        self.shortcut_add_folder = QShortcut(QKeySequence("Ctrl+Shift+O"), self)
        self.shortcut_add_folder.activated.connect(self.add_folder)

        self.shortcut_remove_file = QShortcut(QKeySequence("Delete"), self)
        self.shortcut_remove_file.activated.connect(self.remove_selected_file)

        self.shortcut_settings = QShortcut(QKeySequence("Ctrl+,"), self)
        self.shortcut_settings.activated.connect(self.open_settings)

        self.shortcut_clear_queue = QShortcut(QKeySequence("Ctrl+Shift+C"), self)
        self.shortcut_clear_queue.activated.connect(self.clear_queue)

        self.shortcut_paste = QShortcut(QKeySequence("Ctrl+V"), self)
        self.shortcut_paste.activated.connect(self.on_paste)

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

        self.shortcut_reset_layout = QShortcut(QKeySequence("Ctrl+Alt+R"), self)
        self.shortcut_reset_layout.activated.connect(self._apply_default_splitter_sizes)

        self.current_file_path = None
        self.current_hits = []
        
        # Batch Mode State
        self.is_batch_mode = False
        self.batch_index = -1
        self.batch_success_count = 0
        
        # PDF Sub-loop State
        self.active_pdf_pages = []
        self.active_pdf_index = -1
        self.active_pdf_outputs = []

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
        if checked:
            self.btn_draw_mode.setStyleSheet("padding: 8px; font-weight: bold; background-color: #1976D2; color: white; border-radius: 4px;")
        else:
            self.btn_draw_mode.setStyleSheet("padding: 8px; font-weight: bold; background-color: #333; color: white; border-radius: 4px;")

    def cancel_batch_mode(self):
        self.is_batch_mode = False
        self.batch_index = -1
        self.batch_success_count = 0
        self.active_pdf_pages = []
        self.active_pdf_outputs = []
        self.active_pdf_index = -1
        
        self.btn_previous.hide()
        self.btn_skip.hide()
        self.btn_redact_next.hide()
        self.btn_stop_review.hide()
        self.btn_start_review.show()
        self.preview_widget.scene.clear()
        self.current_hits = []
        self.file_list.setEnabled(True)
        
        # Reset draw mode
        if self.btn_draw_mode.isChecked():
            self.btn_draw_mode.setChecked(False)
            self.toggle_draw_mode(False)

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

    def add_pattern_row(self, is_regex=False):
        row_widget = QWidget()
        row_widget.setStyleSheet("background: transparent;")
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(6)
        
        label = QLabel("Regex:" if is_regex else "Text:")
        label.setStyleSheet("color: #9CA3AF; font-weight: 600; font-size: 12px; background: transparent;")
        
        input_field = PatternLineEdit(is_regex, self)
        input_field.setPlaceholderText("e.g. \\b\\d{4}\\b" if is_regex else "e.g. CONFIDENTIAL")
        input_field.setProperty("is_regex", is_regex)
        input_field.setStyleSheet("""
            QLineEdit {
                background-color: #1F2937;
                color: #F3F4F6;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #10B981;
            }
        """)
        # Use editingFinished so it doesn't trigger Tesseract on every keystroke
        input_field.editingFinished.connect(self.update_text_patterns)
        
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
        
        row_layout.addWidget(label)
        row_layout.addWidget(input_field)
        
        if not is_regex:
            chk_whole = QCheckBox("Whole Word")
            chk_whole.setChecked(True)
            chk_whole.setObjectName("chk_whole")
            chk_whole.setStyleSheet("""
                QCheckBox {
                    spacing: 6px;
                    color: #E5E7EB;
                    font-size: 12px;
                    background: transparent;
                }
                QCheckBox::indicator {
                    width: 14px;
                    height: 14px;
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
            """)
            chk_whole.stateChanged.connect(self.update_text_patterns)
            row_layout.addWidget(chk_whole)
            
        row_layout.addWidget(btn_remove)
        
        self.text_patterns_layout.addWidget(row_widget)
        self.update_text_patterns()
        
    def remove_pattern_row(self, row_widget):
        row_widget.hide()  # Hide immediately so it gets filtered out
        self.text_patterns_layout.removeWidget(row_widget)
        row_widget.deleteLater()
        self.update_text_patterns()

    def focus_last_pattern_field(self):
        count = self.text_patterns_layout.count()
        if count > 0:
            item = self.text_patterns_layout.itemAt(count - 1)
            if item:
                row_widget = item.widget()
                if row_widget:
                    input_field = row_widget.findChild(QLineEdit)
                    if input_field:
                        input_field.setFocus()
        
    def update_text_patterns(self):
        if not self.scanner:
            return
            
        patterns = []
        for i in range(self.text_patterns_layout.count()):
            item = self.text_patterns_layout.itemAt(i)
            if item:
                row_widget = item.widget()
                if row_widget and row_widget.isVisible():
                    input_field = row_widget.findChild(QLineEdit)
                    chk_whole = row_widget.findChild(QCheckBox, "chk_whole")
                    is_whole_word = chk_whole.isChecked() if chk_whole else False
                    
                    if input_field and input_field.text().strip():
                        patterns.append({
                            "label": "REGEX" if input_field.property("is_regex") else "TEXT",
                            "pattern": input_field.text(),
                            "is_regex": input_field.property("is_regex"),
                            "whole_word": is_whole_word
                        })
                    
        self.scanner.set_text_patterns(patterns)
        
        # Auto-rescan if in batch mode
        if self.is_batch_mode and self.current_file_path:
            self.btn_redact_next.setEnabled(False)
            self.preview_widget.load_image(self.current_file_path)
            self.current_hits = []
            try:
                hits = self.run_scan_with_overlay(self.current_file_path)
                self.current_hits = hits
                if hits:
                    self.preview_widget.display_hits(hits)
                    self.btn_redact_next.setEnabled(True)
            except Exception as e:
                print(f"Rescan error: {e}")

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
            
        from PySide6.QtWidgets import QInputDialog, QMessageBox
        name, ok = QInputDialog.getText(self, "Add Identity", f"Enter name for this face:")
        if ok and name.strip():
            # Ask if Permanent or Session Only
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
                
                # Use a temp file for the add_identity/add_session_identity calls
                temp_path = os.path.join(self.scanner.identity_manager.identities_dir, "temp_quick_add.jpg")
                cv2.imwrite(temp_path, face_crop)
                
                if is_session:
                    self.scanner.identity_manager.add_session_identity(name.strip(), temp_path)
                    QMessageBox.information(self, "Success", f"Added '{name}' (Session Only).")
                else:
                    self.scanner.identity_manager.add_identity(name.strip(), [temp_path])
                    QMessageBox.information(self, "Success", f"Added '{name}' permanently.")
                
                os.remove(temp_path)
                self.load_next_batch_item() # Trigger rescan

    def _show_people_selector(self):
        if not self.scanner: return
        
        from PySide6.QtWidgets import QMenu, QWidgetAction, QCheckBox, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QLabel
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #1F2937; color: #E5E7EB; border: 1px solid #374151; padding: 10px; border-radius: 8px; }
        """)
        
        # Get all identities (perm + session)
        all_names = sorted(self.scanner.identity_manager.identity_map.values())
        
        if not all_names:
            menu.addAction("No identities found").setEnabled(False)
        else:
            container = QWidget()
            container.setStyleSheet("background: transparent;")
            layout = QVBoxLayout(container)
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setSpacing(8)
            
            # Header Label
            lbl_header = QLabel("Target Selection")
            lbl_header.setStyleSheet("font-size: 11px; font-weight: bold; color: #10B981; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;")
            layout.addWidget(lbl_header)
            
            # Checkboxes
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
                
            # Quick Actions Layout (Select All / Clear)
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
        self._rescan_current()

    def _clear_target_identities(self):
        self.scanner.target_identities = []
        self._rescan_current()

    def _rescan_current(self):
        """Re-scan the currently loaded image with current settings."""
        if not self.current_file_path:
            return
        try:
            hits = self.run_scan_with_overlay(self.current_file_path)
            self.current_hits = hits
            self.preview_widget.display_hits(hits)
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
                # Recursively add all supported files in directory
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
            # If the removed item is the currently loaded file, clear preview
            if item.data(Qt.UserRole) == self.current_file_path:
                self.preview_widget.scene.clear()
                self.current_file_path = None
                self.current_hits = []
                
            row = self.file_list.row(item)
            self.file_list.takeItem(row)
            
            # If we remove something during batch mode, we might mess up the index
            if self.is_batch_mode:
                if row < self.batch_index:
                    self.batch_index -= 1
                elif row == self.batch_index:
                    # If we removed the current batch item, move to the next one
                    self.load_next_batch_item()

    def clear_queue(self):
        self.file_list.clear()
        self.preview_widget.scene.clear()
        self.current_file_path = None
        self.current_hits = []
        
        # Reset batch mode if active
        if self.is_batch_mode:
            self.cancel_batch_mode()

    def on_paste(self):
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if mime_data.hasImage():
            image = clipboard.image()
            if image.isNull():
                return
            
            # Use system temp directory
            import tempfile
            temp_dir = os.path.join(tempfile.gettempdir(), "safemarc_clipboard")
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
            
        file_path = item.data(Qt.UserRole)
        self.current_file_path = file_path
        self.current_hits = []
        
        # Load preview
        if file_path.lower().endswith('.pdf'):
            try:
                preview_page = PDFHandler.extract_first_page(file_path)
                if preview_page:
                    self.preview_widget.load_image(preview_page)
            except Exception as e:
                print(f"Failed to load PDF preview: {e}")
        elif file_path.lower().endswith(tuple(SUPPORTED_EXTENSIONS)):
            self.preview_widget.load_image(file_path)

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

    def run_scan_with_overlay(self, path, pdf_words=None):
        self.preview_widget.show_loading("Scanning document for sensitive data...")
        from PySide6.QtCore import QEventLoop
        loop = QEventLoop()
        
        worker = ScanWorker(self.scanner, path, pdf_words)
        worker.finished.connect(loop.quit)
        worker.error.connect(loop.quit)
        
        worker.start()
        loop.exec()
        
        worker.wait()
        
        self.preview_widget.hide_loading()
        return worker.hits

    def redact_current(self):
        if not self.scanner or not self.current_file_path:
            return

        selected_hits = self.preview_widget.get_selected_hits()   
        if not selected_hits:
            QMessageBox.warning(self, "Warning", "No hits selected for redaction.")
            return

        out_path = self.get_redacted_output_path(self.current_file_path)
        
        # Handle PDF sub-loop
        if self.active_pdf_pages:
            import tempfile
            fd, temp_path = tempfile.mkstemp(suffix=".png")
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

        for i in range(self.file_list.count()):
            from PySide6.QtGui import QColor
            self.file_list.item(i).setForeground(QColor("#E5E7EB"))
            
        has_pdf = any(self.file_list.item(i).data(Qt.UserRole).lower().endswith('.pdf') for i in range(self.file_list.count()))
        if has_pdf:
            QMessageBox.information(self, "PDF Rasterization", "PDFs in the queue will be rasterized to guarantee redaction security. Hidden text layers and vectors will be destroyed.")

        self.is_batch_mode = True
        self.batch_index = 0
        self.batch_success_count = 0
        self.file_list.setEnabled(False)
        
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
                # User wants to go back to a finished PDF
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Finished PDF")
                msg_box.setText(f"The previous item is a completed PDF.\nRe-entering it will restart from Page 1.\n\nWhat would you like to do?")
                
                btn_restart = msg_box.addButton("Restart PDF", QMessageBox.AcceptRole)
                btn_skip = msg_box.addButton("Go Back Further", QMessageBox.ActionRole)
                btn_cancel = msg_box.addButton("Cancel", QMessageBox.RejectRole)
                
                msg_box.exec()
                
                if msg_box.clickedButton() == btn_restart:
                    self._undo_queue_item(prev_index)
                    self.batch_index = prev_index
                    self.load_next_batch_item()
                elif msg_box.clickedButton() == btn_skip:
                    self._undo_queue_item(prev_index)
                    self.batch_index = prev_index
                    self.go_previous() # Recursive call
                else:
                    return # Cancel
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

        # PDF Sub-loop
        if self.active_pdf_pages:
            if self.active_pdf_index < len(self.active_pdf_pages):
                page_data = self.active_pdf_pages[self.active_pdf_index]
                page_path = page_data["image_path"] if isinstance(page_data, dict) else page_data
                pdf_words = page_data.get("words", None) if isinstance(page_data, dict) else None
                self.current_file_path = page_path
                self.current_hits = []
                self.title_label.setText(f"🛡️ SafeMARC - Page {self.active_pdf_index + 1}/{len(self.active_pdf_pages)}")
                
                self.preview_widget.load_image(page_path)
                try:
                    hits = self.run_scan_with_overlay(page_path, pdf_words=pdf_words)
                    self.current_hits = hits
                    if self.chk_skip_review.isChecked():
                        import tempfile
                        fd, temp_path = tempfile.mkstemp(suffix=".png")
                        os.close(fd)
                        success = self.scanner.redact(page_path, temp_path, hits)
                        if success:
                            self.active_pdf_outputs.append(temp_path)
                        else:
                            self.active_pdf_outputs.append(page_path)
                        self.active_pdf_index += 1
                        QTimer.singleShot(0, self.load_next_batch_item)
                        return
                    elif not hits and self.chk_auto_skip.isChecked():
                        self.active_pdf_outputs.append(page_path)
                        self.active_pdf_index += 1
                        QTimer.singleShot(0, self.load_next_batch_item)
                        return
                    else:
                        self.preview_widget.display_hits(hits)
                        self.btn_redact_next.setEnabled(True)
                except Exception as e:
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
                self.active_pdf_pages = PDFHandler.extract_pages(file_path)
                self.active_pdf_index = 0
                self.active_pdf_outputs = []
                self.active_pdf_has_redactions = False
                QTimer.singleShot(0, self.load_next_batch_item)
                return
            except Exception as e:
                item.setForeground(QColor("#d32f2f"))
                print(f"Error extracting PDF: {e}")
                self.batch_index += 1
                QTimer.singleShot(0, self.load_next_batch_item)
                return
        
        self.current_file_path = file_path
        self.current_hits = []
        
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
                elif not hits and self.chk_auto_skip.isChecked():
                    self.file_list.item(self.batch_index).setForeground(QColor("#888888"))
                    self.batch_index += 1
                    QTimer.singleShot(0, self.load_next_batch_item)
                    return
                else:
                    self.preview_widget.display_hits(hits)
                    self.btn_redact_next.setEnabled(True)
            except Exception as e:
                item.setForeground(QColor("#d32f2f"))
                print(f"Error processing {file_path}: {e}")
                self.batch_index += 1
                QTimer.singleShot(0, self.load_next_batch_item)
        else:
            # Skip unhandled file types for now
            self.batch_index += 1
            QTimer.singleShot(0, self.load_next_batch_item)

    def update_stats(self):
        count = self.file_list.count()
        self.lbl_count.setText(f"Files: {count}")

