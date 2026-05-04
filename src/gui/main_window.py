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
)
from PySide6.QtCore import Qt, QSize
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


class SafeMARCMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SafeMARC - v0.1 (DEV)")
        self.setGeometry(100, 100, 1000, 700)

        # Core Engines
        try:
            self.scanner = SafeScanner()
            self.processor = BatchProcessor(self.scanner)
            engine_status = "✅ AI Engine: Online"
        except Exception as e:
            self.scanner = None
            self.processor = None
            engine_status = f"❌ AI Engine Error: {e}"

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
        self.status_label.setStyleSheet("font-size: 13px; color: #9CA3AF; margin-right: 12px; font-weight: 500;")
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
        
        lbl_queue = QLabel("Queue")
        lbl_queue.setStyleSheet("font-size: 13px; font-weight: 700; color: #9CA3AF; margin-top: 5px; margin-left: 2px; text-transform: uppercase; letter-spacing: 0.5px;")
        sidebar_layout.addWidget(lbl_queue)
        sidebar_layout.addWidget(self.file_list, 1)

         # Queue Buttons
        queue_btns_layout = QHBoxLayout()
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
        
        btn_style = """
            QPushButton {
                background-color: #1F2937;
                color: #E5E7EB;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 8px 10px;
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
        
        for btn in (self.btn_add_file, self.btn_add_folder, self.btn_remove, self.btn_clear):
            btn.setStyleSheet(btn_style)
        
        queue_btns_layout.addWidget(self.btn_add_file)
        queue_btns_layout.addWidget(self.btn_add_folder)
        queue_btns_layout.addWidget(self.btn_remove)
        queue_btns_layout.addWidget(self.btn_clear)
        sidebar_layout.addLayout(queue_btns_layout)

        # Settings Group
        settings_group = QGroupBox("Vision Settings")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                font-size: 13px;
                color: #10B981;
                padding-top: 28px;
                margin-top: 15px;
                border: 1px solid #374151;
                border-radius: 10px;
                background-color: #111827;
            }
        """)
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setSpacing(10)
        
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

        sidebar_layout.addWidget(settings_group)
        
        # Text Patterns Group
        text_group = QGroupBox("Text Redaction")
        text_group.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                font-size: 13px;
                color: #10B981;
                padding-top: 28px;
                margin-top: 15px;
                border: 1px solid #374151;
                border-radius: 10px;
                background-color: #111827;
            }
        """)
        text_layout = QVBoxLayout(text_group)
        text_layout.setSpacing(10)
        
        self.text_patterns_layout = QVBoxLayout()
        text_layout.addLayout(self.text_patterns_layout)
        
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
        
        sidebar_layout.addWidget(text_group)

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
        preview_layout.addWidget(self.preview_widget)

        # Draw and Zoom Tools
        draw_layout = QHBoxLayout()
        self.btn_draw_mode = QPushButton("Draw Box (D)")
        self.btn_draw_mode.setCheckable(True)
        self.btn_draw_mode.clicked.connect(self.toggle_draw_mode)
        
        self.btn_zoom_in = QPushButton("Zoom In")
        self.btn_zoom_in.clicked.connect(self.preview_widget.zoom_in)
        
        self.btn_zoom_out = QPushButton("Zoom Out")
        self.btn_zoom_out.clicked.connect(self.preview_widget.zoom_out)
        
        self.btn_reset_zoom = QPushButton("Reset")
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

        self.splitter.addWidget(preview_container)
        self.splitter.setSizes([300, 700])

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
        if self.btn_start_review.isVisible():
            self.btn_start_review.click()
        elif self.btn_redact_next.isVisible() and self.btn_redact_next.isEnabled():
            self.btn_redact_next.click()

    def on_escape_pressed(self):
        if self.btn_stop_review.isVisible():
            self.btn_stop_review.click()

    def open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()

    def add_pattern_row(self, is_regex=False):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel("Regex:" if is_regex else "Text:")
        label.setStyleSheet("color: #aaa;")
        
        input_field = QLineEdit()
        input_field.setPlaceholderText("e.g. \\b\\d{4}\\b" if is_regex else "e.g. CONFIDENTIAL")
        input_field.setProperty("is_regex", is_regex)
        # Use editingFinished so it doesn't trigger Tesseract on every keystroke
        input_field.editingFinished.connect(self.update_text_patterns)
        
        btn_remove = QPushButton("❌")
        btn_remove.setFixedWidth(30)
        btn_remove.clicked.connect(lambda checked=False, rw=row_widget: self.remove_pattern_row(rw))
        
        row_layout.addWidget(label)
        row_layout.addWidget(input_field)
        
        if not is_regex:
            chk_whole = QCheckBox("Whole Word")
            chk_whole.setChecked(True)
            chk_whole.setObjectName("chk_whole")
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
                hits = self.scanner.scan(self.current_file_path)
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
                self.preview_widget.load_image(self.current_file_path)
                self.current_hits = []
                hits = self.scanner.scan(self.current_file_path)
                if hits:
                    self.current_hits = hits
                    self.preview_widget.display_hits(hits)
                    self.btn_redact_next.setEnabled(True)
                else:
                    QMessageBox.information(self, "Result", f"No {mode} found in this image.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load {mode} model: {e}")

    def add_files(self):
        exts = " ".join([f"*{ext}" for ext in SUPPORTED_EXTENSIONS])
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files", "", f"Supported ({exts})")
        if files:
            for f in files:
                self.add_to_queue(f)

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Directory")
        if folder:
            for root, _, filenames in os.walk(folder):
                for filename in filenames:
                    if filename.lower().endswith(tuple(SUPPORTED_EXTENSIONS)):
                        self.add_to_queue(os.path.join(root, filename))

    def add_to_queue(self, file_path):
        # Prevent duplicates
        for i in range(self.file_list.count()):
            if self.file_list.item(i).data(Qt.UserRole) == file_path:
                return
        
        item = QListWidgetItem(os.path.basename(file_path))
        item.setData(Qt.UserRole, file_path)
        item.setToolTip(file_path)
        self.file_list.addItem(item)

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

    def redact_current(self):
        if not self.scanner or not self.current_file_path:
            return

        selected_hits = self.preview_widget.get_selected_hits()   
        if not selected_hits:
            QMessageBox.warning(self, "Warning", "No hits selected for redaction.")
            return

        out_path = self.processor.get_output_path(
            self.current_file_path, 
            use_suffix=self.chk_suffix.isChecked()
        )
        
        # Handle PDF sub-loop
        if self.active_pdf_pages:
            import tempfile
            fd, temp_path = tempfile.mkstemp(suffix=".png")
            os.close(fd)
            success = self.scanner.redact(self.current_file_path, temp_path, selected_hits)
            if success:
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
            self.active_pdf_outputs.append(self.current_file_path)
            self.active_pdf_index += 1
            self.load_next_batch_item()
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
                    hits = self.scanner.scan(page_path, pdf_words=pdf_words)
                    self.current_hits = hits
                    if self.chk_skip_review.isChecked():
                        import tempfile
                        import os
                        fd, temp_path = tempfile.mkstemp(suffix=".png")
                        os.close(fd)
                        success = self.scanner.redact(page_path, temp_path, hits)
                        if success:
                            self.active_pdf_outputs.append(temp_path)
                        else:
                            self.active_pdf_outputs.append(page_path)
                        self.active_pdf_index += 1
                        from PySide6.QtCore import QTimer
                        QTimer.singleShot(0, self.load_next_batch_item)
                        return
                    elif not hits and self.chk_auto_skip.isChecked():
                        # Auto skip page
                        self.active_pdf_outputs.append(page_path)
                        self.active_pdf_index += 1
                        from PySide6.QtCore import QTimer
                        QTimer.singleShot(0, self.load_next_batch_item)
                        return
                    else:
                        self.preview_widget.display_hits(hits)
                        self.btn_redact_next.setEnabled(True)
                except Exception as e:
                    print(f"Error processing page: {e}")
                    self.active_pdf_outputs.append(page_path)
                    self.active_pdf_index += 1
                    from PySide6.QtCore import QTimer
                    QTimer.singleShot(0, self.load_next_batch_item)
                return
            else:
                # Finished PDF, rebuild
                out_path = self.processor.get_output_path(
                    self.file_list.item(self.batch_index).data(Qt.UserRole),
                    use_suffix=self.chk_suffix.isChecked()
                )
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
                from PySide6.QtCore import QTimer
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
                from PySide6.QtCore import QTimer
                QTimer.singleShot(0, self.load_next_batch_item)
                return
            except Exception as e:
                item.setForeground(QColor("#d32f2f"))
                print(f"Error extracting PDF: {e}")
                self.batch_index += 1
                from PySide6.QtCore import QTimer
                QTimer.singleShot(0, self.load_next_batch_item)
                return
        
        self.current_file_path = file_path
        self.current_hits = []
        
        # Attempt to load and auto-scan
        if file_path.lower().endswith(tuple(SUPPORTED_EXTENSIONS)):
            self.preview_widget.load_image(file_path)
            
            try:
                hits = self.scanner.scan(file_path)
                self.current_hits = hits
                if self.chk_skip_review.isChecked():
                    out_path = self.processor.get_output_path(
                        file_path, 
                        use_suffix=self.chk_suffix.isChecked()
                    )
                    success = self.scanner.redact(file_path, out_path, hits)
                    if success:
                        self.batch_success_count += 1
                        self.file_list.item(self.batch_index).setForeground(QColor("#4CAF50"))
                    else:
                        self.file_list.item(self.batch_index).setForeground(QColor("#d32f2f"))
                    self.batch_index += 1
                    from PySide6.QtCore import QTimer
                    QTimer.singleShot(0, self.load_next_batch_item)
                    return
                elif not hits and self.chk_auto_skip.isChecked():
                    # Auto skip if no hits found
                    self.file_list.item(self.batch_index).setForeground(QColor("#888888"))
                    self.batch_index += 1
                    # Use QTimer to prevent recursion depth issues on huge empty queues
                    from PySide6.QtCore import QTimer
                    QTimer.singleShot(0, self.load_next_batch_item)
                    return
                else:
                    self.preview_widget.display_hits(hits)
                    self.btn_redact_next.setEnabled(True)
            except Exception as e:
                item.setForeground(QColor("#d32f2f"))
                print(f"Error processing {file_path}: {e}")
                self.batch_index += 1
                from PySide6.QtCore import QTimer
                QTimer.singleShot(0, self.load_next_batch_item)
        else:
            # Skip unhandled file types for now
            self.batch_index += 1
            from PySide6.QtCore import QTimer
            QTimer.singleShot(0, self.load_next_batch_item)
