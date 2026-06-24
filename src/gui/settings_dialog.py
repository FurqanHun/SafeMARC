from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QWidget, QTabWidget, QListWidget, QListWidgetItem, QScrollArea, QFrame, QFileDialog, QMessageBox, QInputDialog, QGridLayout, QCheckBox, QLineEdit, QAbstractItemView, QSlider, QProgressBar
from PySide6.QtCore import Qt, QSize, QSettings, QStandardPaths, QRect, QPoint, Signal
from PySide6.QtGui import QIcon, QPainter, QImage, QPixmap, QColor, QPen, QShortcut, QKeySequence
from src.core.identity_manager import IdentityManager
from src.utils.crypto import encrypt_data, decrypt_data
import os

def svg_to_icon(svg_str: str, size: int = 16) -> QIcon:
    from PySide6.QtSvg import QSvgRenderer
    renderer = QSvgRenderer(svg_str.encode('utf-8'))
    image = QImage(size, size, QImage.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    return QIcon(QPixmap.fromImage(image))


SVG_CLOSE = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>'''

SVG_RESET = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#9CA3AF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>'''

SVG_IMPORT = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E5E7EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>'''
SVG_EXPORT = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E5E7EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>'''

DEFAULT_SHORTCUTS = {
    "add_file": "Ctrl+O",
    "add_folder": "Ctrl+Shift+O",
    "remove_file": "Delete",
    "clear_queue": "Ctrl+Shift+C",
    "settings": "Ctrl+,",
    "paste": "Ctrl+V",
    "reset_layout": "Ctrl+Alt+R",
    "zoom_in": "Ctrl+=",
    "zoom_in_alt": "Ctrl++",
    "zoom_out": "Ctrl+-",
    "zoom_reset": "Ctrl+0",
    "toggle_draw": "D",
    "toggle_persistent": "Shift+D",
    "rescan": "F5",
    "redact_next": "Shift+Return",
    "redact_next_alt": "Shift+Enter",
    "skip_s": "S",
    "skip_space": "Space",
    "previous_p": "P",
    "previous_bs": "Backspace",
    "escape": "Escape",
    "hit_next": "Right",
    "hit_prev": "Left",
    "hit_toggle": "C",
    "id_add_person": "Ctrl+Shift+N",
    "id_rename_person": "F2",
    "id_del_person": "Ctrl+D",
    "id_import_identities": "Ctrl+I",
    "id_export_identities": "Ctrl+E",
    "id_add_image": "Ctrl+Shift+A"
}

SHORTCUT_METADATA = {
    "add_file": {"label": "Add Files", "category": "General", "default": "Ctrl+O"},
    "add_folder": {"label": "Add Folder", "category": "General", "default": "Ctrl+Shift+O"},
    "remove_file": {"label": "Remove Selected File", "category": "General", "default": "Delete"},
    "clear_queue": {"label": "Clear Queue", "category": "General", "default": "Ctrl+Shift+C"},
    "settings": {"label": "Open Settings", "category": "General", "default": "Ctrl+,"},
    "paste": {"label": "Paste from Clipboard", "category": "General", "default": "Ctrl+V"},
    "reset_layout": {"label": "Reset Splitter Layout", "category": "General", "default": "Ctrl+Alt+R"},
    
    "zoom_in": {"label": "Zoom In (Primary)", "category": "Zoom & Navigation", "default": "Ctrl+="},
    "zoom_in_alt": {"label": "Zoom In (Alternative)", "category": "Zoom & Navigation", "default": "Ctrl++"},
    "zoom_out": {"label": "Zoom Out", "category": "Zoom & Navigation", "default": "Ctrl+-"},
    "zoom_reset": {"label": "Reset Zoom", "category": "Zoom & Navigation", "default": "Ctrl+0"},
    
    "toggle_draw": {"label": "Toggle Draw Mode", "category": "Review Actions", "default": "D"},
    "toggle_persistent": {"label": "Toggle Persistent Draw Mode", "category": "Review Actions", "default": "Shift+D"},
    "rescan": {"label": "Rescan Current File", "category": "Review Actions", "default": "F5"},
    
    "redact_next": {"label": "Redact & Next (Primary)", "category": "Batch Workflow", "default": "Shift+Return"},
    "redact_next_alt": {"label": "Redact & Next (Alternative)", "category": "Batch Workflow", "default": "Shift+Enter"},
    "skip_s": {"label": "Skip Item (Primary Key)", "category": "Batch Workflow", "default": "S"},
    "skip_space": {"label": "Skip / Toggle Box (Space)", "category": "Batch Workflow", "default": "Space"},
    "previous_p": {"label": "Previous Item (Primary Key)", "category": "Batch Workflow", "default": "P"},
    "previous_bs": {"label": "Previous Item (Alternative Key)", "category": "Batch Workflow", "default": "Backspace"},
    "escape": {"label": "Stop Review / Cancel", "category": "Batch Workflow", "default": "Escape"},
    
    "hit_next": {"label": "Focus Next Box", "category": "Sensitive Box Keyboard Selection", "default": "Right"},
    "hit_prev": {"label": "Focus Previous Box", "category": "Sensitive Box Keyboard Selection", "default": "Left"},
    "hit_toggle": {"label": "Toggle Selected State", "category": "Sensitive Box Keyboard Selection", "default": "C"},

    "id_add_person": {"label": "Add New Person", "category": "Identities Management", "default": "Ctrl+Shift+N"},
    "id_rename_person": {"label": "Rename Selected Person", "category": "Identities Management", "default": "F2"},
    "id_del_person": {"label": "Delete Selected Person", "category": "Identities Management", "default": "Ctrl+D"},
    "id_import_identities": {"label": "Import Identities Package", "category": "Identities Management", "default": "Ctrl+I"},
    "id_export_identities": {"label": "Export Selected Identities", "category": "Identities Management", "default": "Ctrl+E"},
    "id_add_image": {"label": "Add Image to Person", "category": "Identities Management", "default": "Ctrl+Shift+A"}
}

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


class ShortcutRebindButton(QPushButton):
    keySequenceChanged = Signal(str)

    def __init__(self, current_sequence: str, parent=None):
        super().__init__(current_sequence, parent)
        self.current_sequence = current_sequence
        self.is_listening = False
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)
        self.clicked.connect(self._on_clicked)
        self.update_style()

    def update_style(self):
        if self.is_listening:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #10B981;
                    color: #FFFFFF;
                    border: 1px solid #10B981;
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-weight: bold;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 13px;
                    min-width: 120px;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #1F2937;
                    color: #F3F4F6;
                    border: 1px solid #374151;
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-weight: bold;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 13px;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #374151;
                    border-color: #10B981;
                    color: #FFFFFF;
                }
            """)

    def _on_clicked(self):
        if self.isChecked():
            self.is_listening = True
            self.setText("Press any key...")
            self.update_style()
            self.grabKeyboard()
        else:
            self.is_listening = False
            self.setText(self.current_sequence)
            self.update_style()
            self.releaseKeyboard()

    def keyPressEvent(self, event):
        if self.is_listening:
            key = event.key()
            if key in (Qt.Key_Escape, Qt.Key_Tab, Qt.Key_Backtab):
                self.setChecked(False)
                self.is_listening = False
                self.setText(self.current_sequence)
                self.update_style()
                self.releaseKeyboard()
                return
            if key in (Qt.Key_unknown, Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
                return

            modifiers = event.modifiers()
            key_seq = []
            if modifiers & Qt.ControlModifier:
                key_seq.append("Ctrl")
            if modifiers & Qt.ShiftModifier:
                key_seq.append("Shift")
            if modifiers & Qt.AltModifier:
                key_seq.append("Alt")
            if modifiers & Qt.MetaModifier:
                key_seq.append("Meta")

            from PySide6.QtGui import QKeySequence
            key_text = QKeySequence(key).toString()
            if key_text:
                if key == Qt.Key_Left:
                    key_text = "Left"
                elif key == Qt.Key_Right:
                    key_text = "Right"
                elif key == Qt.Key_Up:
                    key_text = "Up"
                elif key == Qt.Key_Down:
                    key_text = "Down"
                elif key == Qt.Key_Space:
                    key_text = "Space"
                elif key == Qt.Key_Return or key == Qt.Key_Enter:
                    key_text = "Return" if key == Qt.Key_Return else "Enter"
                elif key == Qt.Key_Backspace:
                    key_text = "Backspace"
                elif key == Qt.Key_Escape:
                    key_text = "Escape"
                elif key == Qt.Key_Delete:
                    key_text = "Delete"
                
                key_seq.append(key_text)
            else:
                return

            new_seq = "+".join(key_seq)
            self.current_sequence = new_seq
            self.setText(new_seq)
            self.setChecked(False)
            self.is_listening = False
            self.update_style()
            self.releaseKeyboard()
            self.keySequenceChanged.emit(new_seq)
        else:
            super().keyPressEvent(event)

    def focusOutEvent(self, event):
        if self.is_listening:
            self.setChecked(False)
            self.is_listening = False
            self.setText(self.current_sequence)
            self.update_style()
            self.releaseKeyboard()
        super().focusOutEvent(event)

class SettingsDialog(QDialog):
    def __init__(self, scanner, parent=None):
        super().__init__(parent)
        self.scanner = scanner
        self.identity_manager = scanner.identity_manager if scanner else None
        self.setWindowTitle("Settings")
        self.setMinimumSize(600, 450)
        
        self.setStyleSheet("""
            QDialog { background-color: #0B0F19; font-family: 'Segoe UI', Arial, sans-serif; }
            QTabWidget { background-color: #0B0F19; }
            QTabWidget::pane { border: 1px solid #374151; background: #111827; border-radius: 8px; }
            QTabBar { background-color: #0B0F19; outline: none; }
            QTabBar:focus { outline: none; }
            QTabBar::tab {
                background: #1F2937;
                color: #9CA3AF;
                padding: 10px 20px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 2px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
                font-weight: 500;
                border: 1px solid #374151;
                border-bottom: none;
            }
            QTabBar::tab:selected { background: #111827; color: #10B981; font-weight: bold; border: 1px solid #374151; border-bottom: none; }
            QTabBar[focused_via_keyboard="true"]::tab:selected { border: 1px solid #10B981; border-bottom: none; }
            QListWidget { background-color: #1F2937; border: 1px solid #374151; color: #E5E7EB; border-radius: 8px; outline: 0; font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; }
            QListWidget::item { padding: 8px; border-bottom: 1px solid #374151; }
            QListWidget::item:hover { background-color: #374151; color: #FFFFFF; }
            QListWidget::item:selected { background-color: #10B981; color: #FFFFFF; font-weight: bold; }
            QPushButton {
                background-color: #1F2937;
                color: #E5E7EB;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 8px 14px;
                font-weight: 600;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #374151; border-color: #4B5563; color: #FFFFFF; }
            QPushButton:disabled { background-color: #1F2937; color: #4B5563; border-color: #1F2937; }
            QCheckBox {
                spacing: 8px;
                color: #E5E7EB;
                font-size: 13px;
                font-family: 'Segoe UI', Arial, sans-serif;
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
            QLineEdit {
                background-color: #1F2937;
                color: #F3F4F6;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLineEdit:focus {
                border-color: #10B981;
            }
            QSlider::groove:horizontal {
                border: 1px solid #374151;
                height: 6px;
                background: #1F2937;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #10B981;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #10B981;
                border: 1px solid #10B981;
                width: 14px;
                height: 14px;
                margin-top: -4px;
                margin-bottom: -4px;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: #34D399;
                border-color: #34D399;
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
            QLineEdit:focus {
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
            QSlider::handle:horizontal:focus {
                border: 2px solid #FFFFFF !important;
            }
        """)

        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        self.tabs.tabBar().setCursor(Qt.PointingHandCursor)
        self.tabs.tabBar().setFocusPolicy(Qt.TabFocus)
        layout.addWidget(self.tabs)
        
        self.settings = QSettings("SafeMARC", "SafeMARC")
        default_out = self.settings.value("global_output_dir", "")
        if not default_out:
            pictures_dir = QStandardPaths.writableLocation(QStandardPaths.PicturesLocation)
            if not pictures_dir:
                pictures_dir = os.path.expanduser("~/Pictures")
            default_out = os.path.join(pictures_dir, "SafeMARC_Output")
            self.settings.setValue("global_output_dir", default_out)

        self.tab_general = QWidget()
        self.tab_general.setStyleSheet("background-color: #111827; border: none;")
        gen_layout = QVBoxLayout(self.tab_general)
        gen_layout.setContentsMargins(20, 20, 20, 20)
        gen_layout.setSpacing(15)

        lbl_title = QLabel("Global Redaction Output Configuration")
        lbl_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #10B981;")
        gen_layout.addWidget(lbl_title)

        lbl_desc = QLabel("Configure where redacted files are saved. By default, SafeMARC creates output files in the same directory as the input files.")
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("color: #9CA3AF; font-size: 12px; margin-bottom: 10px;")
        gen_layout.addWidget(lbl_desc)

        self.chk_global_output = QCheckBox("Always save redacted files to the global output folder")
        always_use_global = self.settings.value("always_use_global_output", "false") == "true" or self.settings.value("always_use_global_output", False) is True
        self.chk_global_output.setChecked(always_use_global)
        self.chk_global_output.toggled.connect(self._on_global_output_toggled)
        gen_layout.addWidget(self.chk_global_output)

        path_layout = QHBoxLayout()
        self.txt_output_dir = QLineEdit()
        self.txt_output_dir.setReadOnly(True)
        self.txt_output_dir.setText(default_out)
        self.txt_output_dir.setStyleSheet("""
            QLineEdit {
                background-color: #1F2937;
                color: #F3F4F6;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLineEdit:read-only {
                background-color: #111827;
                color: #9CA3AF;
                border: 1px solid #1F2937;
            }
        """)

        self.btn_browse_dir = QPushButton("Browse...")
        self.btn_browse_dir.setCursor(Qt.PointingHandCursor)
        self.btn_browse_dir.setStyleSheet("""
            QPushButton {
                background-color: #1F2937;
                color: #E5E7EB;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 13px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: #374151;
                border-color: #10B981;
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background-color: #111827;
                border-color: #059669;
            }
        """)
        self.btn_browse_dir.clicked.connect(self._browse_global_dir)

        path_layout.addWidget(self.txt_output_dir, 1)
        path_layout.addWidget(self.btn_browse_dir)
        gen_layout.addLayout(path_layout)

        lbl_clip_note = QLabel("Note: Images pasted directly from your clipboard will always be saved to the global output folder to prevent them from being lost in system temporary files.")
        lbl_clip_note.setWordWrap(True)
        lbl_clip_note.setStyleSheet("color: #10B981; font-size: 11px; font-style: italic; margin-top: 10px;")
        gen_layout.addWidget(lbl_clip_note)

        gen_layout.addStretch()
        self.tabs.addTab(self.tab_general, "General")
        
        self.tab_identities = QWidget()
        self.tab_identities.setStyleSheet("background-color: #111827; border: none;")
        id_layout = QHBoxLayout(self.tab_identities)
        
        left_panel = QVBoxLayout()
        self.list_people = QListWidget()
        self.list_people.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_people.setCursor(Qt.PointingHandCursor)
        self.list_people.itemSelectionChanged.connect(self._on_selection_changed)
        self.list_people.itemDoubleClicked.connect(self._rename_person)
        lbl_people = QLabel("People / Identities")
        lbl_people.setStyleSheet("font-size: 13px; font-weight: bold; color: #10B981; font-family: 'Segoe UI', Arial, sans-serif; margin-bottom: 2px;")
        left_panel.addWidget(lbl_people)
        
        self.search_people = QLineEdit()
        self.search_people.setPlaceholderText("Search identities...")
        self.search_people.setStyleSheet("""
            QLineEdit {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 6px 10px;
                color: #E5E7EB;
                font-size: 13px;
                font-family: 'Segoe UI', Arial, sans-serif;
                margin-bottom: 8px;
            }
            QLineEdit:focus {
                border-color: #10B981;
            }
        """)
        self.search_people.textChanged.connect(self._filter_people_list)
        left_panel.addWidget(self.search_people)
        
        left_panel.addWidget(self.list_people)
        
        btn_people_layout = QHBoxLayout()
        self.btn_add_person = QPushButton("+")
        self.btn_add_person.setToolTip("Add Person")
        self.btn_add_person.setCursor(Qt.PointingHandCursor)
        self.btn_add_person.setStyleSheet("""
            QPushButton {
                background-color: #1F2937;
                color: #10B981;
                border: 1px solid #374151;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #10B981;
                color: white;
                border-color: #10B981;
            }
            QPushButton:pressed {
                background-color: #059669;
            }
        """)
        self.btn_add_person.clicked.connect(self._add_person)
        self.btn_del_person = QPushButton("-")
        self.btn_del_person.setToolTip("Delete Person")
        self.btn_del_person.setCursor(Qt.PointingHandCursor)
        self.btn_del_person.setStyleSheet("""
            QPushButton {
                background-color: #1F2937;
                color: #E11D48;
                border: 1px solid #374151;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #E11D48;
                color: white;
                border-color: #E11D48;
            }
            QPushButton:pressed {
                background-color: #BE123C;
            }
            QPushButton:disabled {
                background-color: #111827;
                color: #4B5563;
                border: 1px solid #1F2937;
            }
        """)
        self.btn_del_person.setEnabled(False)
        self.btn_del_person.clicked.connect(self._del_person)
        
        self.btn_rename_person = QPushButton("✎")
        self.btn_rename_person.setToolTip("Rename Person")
        self.btn_rename_person.setCursor(Qt.PointingHandCursor)
        self.btn_rename_person.setStyleSheet("""
            QPushButton {
                background-color: #1F2937;
                color: #3B82F6;
                border: 1px solid #374151;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #3B82F6;
                color: white;
                border-color: #3B82F6;
            }
            QPushButton:pressed {
                background-color: #2563EB;
            }
            QPushButton:disabled {
                background-color: #111827;
                color: #4B5563;
                border: 1px solid #1F2937;
            }
        """)
        self.btn_rename_person.setEnabled(False)
        self.btn_rename_person.clicked.connect(self._rename_person)
        
        btn_people_layout.addWidget(self.btn_add_person)
        btn_people_layout.addWidget(self.btn_rename_person)
        btn_people_layout.addWidget(self.btn_del_person)
        left_panel.addLayout(btn_people_layout)
        
        import_export_layout = QHBoxLayout()
        self.btn_import_identities = QPushButton()
        self.btn_import_identities.setIcon(svg_to_icon(SVG_IMPORT, 14))
        self.btn_import_identities.setCursor(Qt.PointingHandCursor)
        self.btn_import_identities.setToolTip("Import identities from a .smid package")
        self.btn_import_identities.setStyleSheet("""
            QPushButton {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #374151;
                border-color: #3B82F6;
            }
            QPushButton:pressed {
                background-color: #111827;
            }
        """)
        self.btn_import_identities.clicked.connect(self._import_identities)

        self.btn_export_identities = QPushButton()
        self.btn_export_identities.setIcon(svg_to_icon(SVG_EXPORT, 14))
        self.btn_export_identities.setCursor(Qt.PointingHandCursor)
        self.btn_export_identities.setToolTip("Export identities as a .smid package")
        self.btn_export_identities.setStyleSheet("""
            QPushButton {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #374151;
                border-color: #F59E0B;
            }
            QPushButton:pressed {
                background-color: #111827;
            }
        """)
        self.btn_export_identities.clicked.connect(self._export_identities)

        import_export_layout.addWidget(self.btn_import_identities)
        import_export_layout.addWidget(self.btn_export_identities)
        left_panel.addLayout(import_export_layout)
        
        id_layout.addLayout(left_panel, 1)
        
        right_panel = QVBoxLayout()
        lbl_ref = QLabel("Reference Images")
        lbl_ref.setStyleSheet("font-size: 13px; font-weight: bold; color: #10B981; font-family: 'Segoe UI', Arial, sans-serif; margin-bottom: 2px;")
        right_panel.addWidget(lbl_ref)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea { border: 1px solid #374151; border-radius: 8px; background-color: #111827; }
            QScrollBar:vertical {
                background: #111827;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #374151;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #4B5563;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background-color: #111827;")
        self.grid_layout = QGridLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)
        right_panel.addWidget(self.scroll_area)
        
        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color: #10B981; font-size: 12px; font-style: italic; margin-top: 4px; margin-bottom: 4px;")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        right_panel.addWidget(self.lbl_status)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #374151;
                border-radius: 6px;
                text-align: center;
                background-color: #1F2937;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 11px;
                height: 16px;
            }
            QProgressBar::chunk {
                background-color: #10B981;
                border-radius: 5px;
            }
        """)
        right_panel.addWidget(self.progress_bar)
        
        self.btn_add_img = QPushButton("Add Image")
        self.btn_add_img.setCursor(Qt.PointingHandCursor)
        self.btn_add_img.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 14px;
                font-weight: 600;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:pressed {
                background-color: #047857;
            }
            QPushButton:disabled {
                background-color: #1F2937;
                color: #4B5563;
                border: 1px solid #374151;
            }
        """)
        self.btn_add_img.clicked.connect(self._add_image)
        self.btn_add_img.setEnabled(False)
        right_panel.addWidget(self.btn_add_img)
        
        id_layout.addLayout(right_panel, 2)
        
        self.tabs.addTab(self.tab_identities, "Identities")
        
        self.tab_model = QWidget()
        self.tab_model.setStyleSheet("background-color: #111827; border: none;")
        model_layout = QVBoxLayout(self.tab_model)
        model_layout.setContentsMargins(20, 20, 20, 20)
        model_layout.setSpacing(15)

        lbl_model_title = QLabel("AI Model & Redaction Confidence Settings")
        lbl_model_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #10B981;")
        model_layout.addWidget(lbl_model_title)

        lbl_model_desc = QLabel("Adjust confidence thresholds for various detection models. Higher values improve precision (less false positives) but may miss some occurrences. Lower values improve recall (more detections) but may include false positives.")
        lbl_model_desc.setWordWrap(True)
        lbl_model_desc.setStyleSheet("color: #9CA3AF; font-size: 12px; margin-bottom: 10px;")
        model_layout.addWidget(lbl_model_desc)
        fd_box = QHBoxLayout()
        lbl_fd = QLabel("Face Detection Threshold:")
        lbl_fd.setStyleSheet("color: #E5E7EB; font-size: 13px; font-weight: 500; min-width: 180px;")
        self.slider_fd = QSlider(Qt.Horizontal)
        self.slider_fd.setRange(10, 100)
        fd_val = float(self.settings.value("model_face_detect", 0.20))
        self.slider_fd.setValue(int(fd_val * 100))
        self.lbl_fd_val = QLabel(f"{fd_val:.2f}")
        self.lbl_fd_val.setStyleSheet("color: #10B981; font-size: 13px; font-weight: bold; min-width: 40px;")
        
        def fd_changed(val):
            v = val / 100.0
            self.lbl_fd_val.setText(f"{v:.2f}")
            self.settings.setValue("model_face_detect", v)
        self.slider_fd.valueChanged.connect(fd_changed)
        
        fd_box.addWidget(lbl_fd)
        fd_box.addWidget(self.slider_fd, 1)
        fd_box.addWidget(self.lbl_fd_val)
        model_layout.addLayout(fd_box)

        fm_box = QHBoxLayout()
        lbl_fm = QLabel("Face Matching Similarity:")
        lbl_fm.setStyleSheet("color: #E5E7EB; font-size: 13px; font-weight: 500; min-width: 180px;")
        self.slider_fm = QSlider(Qt.Horizontal)
        self.slider_fm.setRange(10, 100)
        fm_val = float(self.settings.value("model_face_match", 0.36))
        self.slider_fm.setValue(int(fm_val * 100))
        self.lbl_fm_val = QLabel(f"{fm_val:.2f}")
        self.lbl_fm_val.setStyleSheet("color: #10B981; font-size: 13px; font-weight: bold; min-width: 40px;")
        
        def fm_changed(val):
            v = val / 100.0
            self.lbl_fm_val.setText(f"{v:.2f}")
            self.settings.setValue("model_face_match", v)
        self.slider_fm.valueChanged.connect(fm_changed)
        
        fm_box.addWidget(lbl_fm)
        fm_box.addWidget(self.slider_fm, 1)
        fm_box.addWidget(self.lbl_fm_val)
        model_layout.addLayout(fm_box)

        tm_box = QHBoxLayout()
        lbl_tm = QLabel("Text Auto-Redact Cutoff:")
        lbl_tm.setStyleSheet("color: #E5E7EB; font-size: 13px; font-weight: 500; min-width: 180px;")
        self.slider_tm = QSlider(Qt.Horizontal)
        self.slider_tm.setRange(0, 100)
        tm_val = int(self.settings.value("model_text_conf", 70))
        self.slider_tm.setValue(tm_val)
        self.lbl_tm_val = QLabel(f"{tm_val}%")
        self.lbl_tm_val.setStyleSheet("color: #10B981; font-size: 13px; font-weight: bold; min-width: 40px;")
        
        def tm_changed(val):
            self.lbl_tm_val.setText(f"{val}%")
            self.settings.setValue("model_text_conf", val)
        self.slider_tm.valueChanged.connect(tm_changed)
        
        tm_box.addWidget(lbl_tm)
        tm_box.addWidget(self.slider_tm, 1)
        tm_box.addWidget(self.lbl_tm_val)
        model_layout.addLayout(tm_box)

        self.btn_reset_model = QPushButton("Reset to Defaults")
        self.btn_reset_model.setCursor(Qt.PointingHandCursor)
        self.btn_reset_model.setStyleSheet("""
            QPushButton {
                background-color: #1F2937;
                color: #E5E7EB;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 13px;
                font-family: 'Segoe UI', Arial, sans-serif;
                margin-top: 15px;
            }
            QPushButton:hover {
                background-color: #374151;
                border-color: #E11D48;
                color: #FFFFFF;
            }
        """)
        
        def reset_to_defaults():
            self.slider_fd.setValue(20)
            self.slider_fm.setValue(36)
            self.slider_tm.setValue(70)
        self.btn_reset_model.clicked.connect(reset_to_defaults)
        model_layout.addWidget(self.btn_reset_model, 0, Qt.AlignLeft)

        model_layout.addStretch()
        self.tabs.addTab(self.tab_model, "Model Settings")

        # Shortcuts tab initialization.
        self.tab_shortcuts = QWidget()
        self.tab_shortcuts.setStyleSheet("background-color: #111827; border: none;")
        self._init_shortcuts_tab()
        self.tabs.addTab(self.tab_shortcuts, "Shortcuts")
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)

        # Apply StrongFocus focus policy.
        settings_widgets = [
            self.tabs,
            self.chk_global_output,
            self.btn_browse_dir,
            self.search_people,
            self.list_people,
            self.btn_add_person,
            self.btn_rename_person,
            self.btn_del_person,
            self.btn_import_identities,
            self.btn_export_identities,
            self.btn_add_img,
            self.slider_fd,
            self.slider_fm,
            self.slider_tm,
            self.btn_reset_model,
            self.btn_reset_all_shortcuts,
            self.close_btn
        ]
        for w in settings_widgets:
            if hasattr(w, "setFocusPolicy"):
                w.setFocusPolicy(Qt.StrongFocus)
        
        # Initialize local keyboard shortcuts for the Identities page.
        self.local_shortcuts = {}
        for key in ["id_add_person", "id_rename_person", "id_del_person", "id_import_identities", "id_export_identities", "id_add_image"]:
            val = self.settings.value(f"shortcut_{key}", DEFAULT_SHORTCUTS[key])
            shortcut = QShortcut(QKeySequence(val), self)
            self.local_shortcuts[key] = shortcut
            
        self.local_shortcuts["id_add_person"].activated.connect(lambda: self._trigger_identity_shortcut(self._add_person))
        self.local_shortcuts["id_rename_person"].activated.connect(lambda: self._trigger_identity_shortcut(self._rename_person))
        self.local_shortcuts["id_del_person"].activated.connect(lambda: self._trigger_identity_shortcut(self._del_person))
        self.local_shortcuts["id_import_identities"].activated.connect(lambda: self._trigger_identity_shortcut(self._import_identities))
        self.local_shortcuts["id_export_identities"].activated.connect(lambda: self._trigger_identity_shortcut(self._export_identities))
        self.local_shortcuts["id_add_image"].activated.connect(lambda: self._trigger_identity_shortcut(self._add_image))

        self._refresh_people_list()
        apply_focus_indicators(self)
        self.chk_global_output.setFocus()

    def _trigger_identity_shortcut(self, callback):
        if self.tabs.currentIndex() == 1:
            callback()

    def _refresh_people_list(self):
        self.list_people.clear()
        self.btn_del_person.setEnabled(False)
        self.btn_rename_person.setEnabled(False)
        self.btn_add_img.setEnabled(False)
        self._clear_grid()
        if not self.identity_manager: return
        
        # Permanent identities.
        identities_dir = self.identity_manager.identities_dir
        if os.path.exists(identities_dir):
            for name in sorted(os.listdir(identities_dir)):
                if name == "session_temp": continue
                path = os.path.join(identities_dir, name)
                if os.path.isdir(path):
                    item = QListWidgetItem(name)
                    item.setData(Qt.UserRole, {"name": name, "is_session": False})
                    self.list_people.addItem(item)
                    
        # Session identities.
        session_dir = os.path.join(identities_dir, "session_temp")
        if os.path.exists(session_dir):
            for name in sorted(os.listdir(session_dir)):
                path = os.path.join(session_dir, name)
                if os.path.isdir(path):
                    item = QListWidgetItem(f"{name} (Session)")
                    item.setData(Qt.UserRole, {"name": name, "is_session": True})
                    item.setForeground(QColor("#10B981"))
                    self.list_people.addItem(item)

    def _filter_people_list(self, text):
        text = text.lower().strip()
        for i in range(self.list_people.count()):
            item = self.list_people.item(i)
            item.setHidden(text not in item.text().lower())

    def _on_selection_changed(self):
        selected_items = self.list_people.selectedItems()
        num_selected = len(selected_items)
        
        self.btn_del_person.setEnabled(num_selected > 0)
        self.btn_rename_person.setEnabled(num_selected == 1)
        
        if num_selected == 1:
            item = selected_items[0]
            data = item.data(Qt.UserRole)
            self.btn_add_img.setEnabled(True)
            self._load_person_images(data["name"], data["is_session"])
        else:
            self.btn_add_img.setEnabled(False)
            self._clear_grid()
            if num_selected > 1:
                lbl_feedback = QLabel("Multiple identities selected. Click '-' to delete them.")
                lbl_feedback.setStyleSheet("color: #9CA3AF; font-size: 13px; font-family: 'Segoe UI', Arial, sans-serif;")
                lbl_feedback.setAlignment(Qt.AlignCenter)
                self.grid_layout.addWidget(lbl_feedback, 0, 0)

    def _clear_grid(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _load_person_images(self, name, is_session=False):
        self._clear_grid()
        base = os.path.join(self.identity_manager.identities_dir, "session_temp") if is_session else self.identity_manager.identities_dir
        person_dir = os.path.join(base, name)
        
        if not os.path.exists(person_dir): return
        
        images = [f for f in os.listdir(person_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        for i, img_name in enumerate(images):
            path = os.path.join(person_dir, img_name)
            pixmap = QPixmap(path).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            container = QWidget()
            container.setFixedSize(100, 100)
            layout = QGridLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            
            lbl = QLabel()
            lbl.setPixmap(pixmap)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFixedSize(100, 100)
            lbl.setStyleSheet("border: 1px solid #374151; border-radius: 6px; background-color: #1F2937;")
            
            del_btn = QPushButton()
            del_btn.setIcon(svg_to_icon(SVG_CLOSE, 10))
            del_btn.setIconSize(QSize(10, 10))
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setToolTip("Delete Reference Image")
            del_btn.setFixedSize(18, 18)
            del_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(225, 29, 72, 220);
                    border: none;
                    border-radius: 9px;
                    margin-top: 4px;
                    margin-right: 4px;
                }
                QPushButton:hover { background-color: #E11D48; }
            """)
            del_btn.clicked.connect(lambda _, p=path: self._delete_individual_image(p, name, is_session))
            
            layout.addWidget(lbl, 0, 0)
            layout.addWidget(del_btn, 0, 0, Qt.AlignTop | Qt.AlignRight)
            
            self.grid_layout.addWidget(container, i // 3, i % 3)

    def _add_person(self):
        dialog = NewIdentityDialog(self)
        if dialog.exec() == QDialog.Accepted:
            name = dialog.get_name()
            if name:
                person_dir = os.path.join(self.identity_manager.identities_dir, name)
                os.makedirs(person_dir, exist_ok=True)
                self._refresh_people_list()
                items = self.list_people.findItems(name, Qt.MatchExactly)
                if items:
                    self.list_people.setCurrentItem(items[0])

    def _del_person(self):
        selected_items = self.list_people.selectedItems()
        if not selected_items: return
        
        num_selected = len(selected_items)
        if num_selected == 1:
            data = selected_items[0].data(Qt.UserRole)
            prompt = f"Are you sure you want to delete identity '{data['name']}'?"
        else:
            prompt = f"Are you sure you want to delete {num_selected} selected identities?"
            
        res = QMessageBox.question(self, "Confirm Delete", prompt)
        if res == QMessageBox.Yes:
            from PySide6.QtWidgets import QApplication
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.setEnabled(False)
            self.lbl_status.setText("Deleting identity & re-indexing...")
            QApplication.processEvents()
            try:
                import shutil
                for item in selected_items:
                    data = item.data(Qt.UserRole)
                    base = os.path.join(self.identity_manager.identities_dir, "session_temp") if data["is_session"] else self.identity_manager.identities_dir
                    person_dir = os.path.join(base, data["name"])
                    if os.path.exists(person_dir):
                        shutil.rmtree(person_dir)
                self._refresh_people_list()
                self.identity_manager.reload_identities()
            finally:
                self.lbl_status.setText("")
                self.setEnabled(True)
                QApplication.restoreOverrideCursor()

    def _rename_person(self, item=None):
        if not item or isinstance(item, bool):
            selected_items = self.list_people.selectedItems()
            if len(selected_items) != 1:
                return
            item = selected_items[0]
            
        data = item.data(Qt.UserRole)
        if not data:
            return
            
        old_name = data["name"]
        is_session = data["is_session"]
        
        from PySide6.QtWidgets import QInputDialog
        new_name, ok = QInputDialog.getText(
            self,
            "Rename Identity",
            f"Enter new name for '{old_name}':",
            text=old_name
        )
        if not ok or not new_name.strip():
            return
            
        new_name = new_name.strip()
        if new_name == old_name:
            return
            
        if "/" in new_name or "\\" in new_name or ".." in new_name:
            QMessageBox.warning(self, "Invalid Name", "Name cannot contain slashes or dot-dot path traversal.")
            return
            
        base_dir = os.path.join(self.identity_manager.identities_dir, "session_temp") if is_session else self.identity_manager.identities_dir
        old_dir = os.path.join(base_dir, old_name)
        new_dir = os.path.join(base_dir, new_name)
        
        if os.path.exists(new_dir):
            QMessageBox.warning(self, "Rename Error", f"An identity named '{new_name}' already exists.")
            return
            
        try:
            from PySide6.QtWidgets import QApplication
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.setEnabled(False)
            self.lbl_status.setText("Renaming identity...")
            QApplication.processEvents()
            
            os.rename(old_dir, new_dir)
            self.identity_manager.reload_identities()
            self._refresh_people_list()
            
            for i in range(self.list_people.count()):
                list_item = self.list_people.item(i)
                item_data = list_item.data(Qt.UserRole)
                if item_data and item_data["name"] == new_name and item_data["is_session"] == is_session:
                    self.list_people.setCurrentItem(list_item)
                    break
        except Exception as e:
            QMessageBox.critical(self, "Rename Failed", f"Failed to rename identity: {e}")
        finally:
            self.lbl_status.setText("")
            self.setEnabled(True)
            QApplication.restoreOverrideCursor()

    def _export_identities(self):
        selected_items = self.list_people.selectedItems()
        if selected_items:
            names_to_export = [item.data(Qt.UserRole)["name"] for item in selected_items]
        else:
            names_to_export = [self.list_people.item(i).data(Qt.UserRole)["name"] for i in range(self.list_people.count())]
            
        names_to_export = [name for name in names_to_export if name != "session_temp"]
        
        permanent_names = []
        for i in range(self.list_people.count()):
            item = self.list_people.item(i)
            data = item.data(Qt.UserRole)
            if data and not data.get("is_session") and data["name"] in names_to_export:
                permanent_names.append(data["name"])
                
        if not permanent_names:
            QMessageBox.warning(self, "Export Identities", "No permanent identities selected/available to export.")
            return
            
        from PySide6.QtCore import QDir
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Identities",
            QDir.homePath(),
            "SafeMARC Identity Packages (*.smid)"
        )
        if not file_path:
            return
            
        if not file_path.endswith(".smid"):
            file_path += ".smid"
            
        from PySide6.QtWidgets import QInputDialog, QLineEdit, QApplication
        password, ok = QInputDialog.getText(
            self,
            "Export Password",
            "Set a password to encrypt and lock the exported archive:",
            QLineEdit.Password
        )
        if not ok:
            return
            
        if not password:
            QMessageBox.warning(self, "Export Identities", "Password cannot be empty. Export cancelled.")
            return
            
        import zipfile
        import io
        
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.setEnabled(False)
        self.lbl_status.setText("Exporting identities...")
        QApplication.processEvents()
        
        try:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
                for name in permanent_names:
                    person_dir = os.path.join(self.identity_manager.identities_dir, name)
                    if not os.path.isdir(person_dir):
                        continue
                    for filename in os.listdir(person_dir):
                        if filename.endswith(".npy") or ".lbph.png" in filename:
                            continue
                        full_path = os.path.join(person_dir, filename)
                        if os.path.isfile(full_path):
                            zip_ref.write(full_path, arcname=os.path.join(name, filename))
            
            plaintext_bytes = zip_buffer.getvalue()
            encrypted_bytes = encrypt_data(plaintext_bytes, password)
            
            with open(file_path, 'wb') as f:
                f.write(encrypted_bytes)
                
            self.lbl_status.setText("Export complete.")
            QMessageBox.information(
                self,
                "Export Success",
                f"Successfully exported {len(permanent_names)} identities to:\n{file_path}"
            )
        except Exception as e:
            self.lbl_status.setText("Export failed.")
            QMessageBox.critical(self, "Export Error", f"Failed to export identities: {e}")
        finally:
            self.lbl_status.setText("")
            self.setEnabled(True)
            QApplication.restoreOverrideCursor()

    def _import_identities(self):
        from PySide6.QtCore import QDir
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Identities",
            QDir.homePath(),
            "SafeMARC Identity Packages (*.smid)"
        )
        if not file_path:
            return
            
        from PySide6.QtWidgets import QInputDialog, QLineEdit, QApplication
        password, ok = QInputDialog.getText(
            self,
            "Import Password",
            "Enter the password for this identity package:",
            QLineEdit.Password
        )
        if not ok:
            return
            
        if not password:
            QMessageBox.warning(self, "Import Identities", "Password cannot be empty. Import cancelled.")
            return
            
        import zipfile
        import tempfile
        import shutil
        import io
        
        import time
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.setEnabled(False)
        self.lbl_status.setText("Decrypting archive...")
        self.progress_bar.setValue(5)
        self.progress_bar.setVisible(True)
        QApplication.processEvents()
        
        try:
            with open(file_path, 'rb') as f:
                encrypted_bytes = f.read()
                
            plaintext_bytes = decrypt_data(encrypted_bytes, password)
            
            if not plaintext_bytes.startswith(b"PK\x03\x04"):
                raise zipfile.BadZipFile("Incorrect password or corrupted file.")
                
            temp_extract_dir = tempfile.mkdtemp(prefix="safemarc_import_")
            
            try:
                time.sleep(0.3)
                self.lbl_status.setText("Extracting package...")
                self.progress_bar.setValue(15)
                QApplication.processEvents()
                
                zip_buffer = io.BytesIO(plaintext_bytes)
                with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
                    for member in zip_ref.namelist():
                        normalized_path = os.path.normpath(member)
                        if os.path.isabs(normalized_path) or normalized_path.startswith("..") or "/.." in normalized_path or "\\.." in normalized_path:
                            raise ValueError(f"Malicious path detected in archive: {member}")
                    
                    zip_ref.extractall(temp_extract_dir)
                
                candidate_entries = sorted(os.listdir(temp_extract_dir))
                valid_identities = []
                for entry in candidate_entries:
                    entry_path = os.path.join(temp_extract_dir, entry)
                    if os.path.isdir(entry_path):
                        image_files = []
                        for filename in os.listdir(entry_path):
                            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp')):
                                image_files.append(os.path.join(entry_path, filename))
                        if image_files:
                            valid_identities.append((entry, image_files))
                            
                total_identities = len(valid_identities)
                time.sleep(0.3)
                self.lbl_status.setText(f"Found {total_identities} identities to import.")
                self.progress_bar.setValue(25)
                QApplication.processEvents()
                time.sleep(0.6)
                
                import glob
                imported_count = 0
                start_loop_time = time.time()
                
                total_images = sum(len(paths) for _, paths in valid_identities)
                if self.identity_manager.use_sface:
                    rebuild_eta = max(2, int(total_images * 3.0))
                else:
                    rebuild_eta = max(1, int(total_images * 1.5))
                
                for idx, (name, image_paths) in enumerate(valid_identities):
                    elapsed = time.time() - start_loop_time
                    if idx > 0:
                        avg_time = elapsed / idx
                        remaining = total_identities - idx
                        eta_seconds = (avg_time * remaining) + rebuild_eta
                        if eta_seconds < 1:
                            eta_str = " (ETA: <1s)"
                        elif eta_seconds < 60:
                            eta_str = f" (ETA: {int(eta_seconds)}s)"
                        else:
                            eta_str = f" (ETA: {int(eta_seconds // 60)}m {int(eta_seconds % 60)}s)"
                    else:
                        eta_seconds = (0.4 * total_identities) + rebuild_eta
                        eta_str = f" (ETA: {int(eta_seconds)}s)"
                        
                    self.lbl_status.setText(f"Importing identity {idx+1}/{total_identities}: {name}{eta_str}...")
                    progress_val = 25 + int(60 * idx / total_identities)
                    self.progress_bar.setValue(progress_val)
                    QApplication.processEvents()
                    time.sleep(0.4)
                    
                    person_dir = os.path.join(self.identity_manager.identities_dir, name)
                    os.makedirs(person_dir, exist_ok=True)
                    
                    existing_files = glob.glob(os.path.join(person_dir, "ref_*"))
                    start_idx = len(existing_files)
                    
                    for i, path in enumerate(image_paths):
                        ext = os.path.splitext(path)[1]
                        target = os.path.join(person_dir, f"ref_{start_idx + i}{ext}")
                        shutil.copy2(path, target)
                        
                    imported_count += 1
                    
                if imported_count > 0:
                    time.sleep(0.3)
                    self.lbl_status.setText(f"Rebuilding biometric recognition model (ETA: ~{rebuild_eta}s)...")
                    self.progress_bar.setValue(90)
                    QApplication.processEvents()
                    self.identity_manager.reload_identities()
                    
                self.progress_bar.setValue(100)
                time.sleep(0.2)
                self.progress_bar.setVisible(False)
                self._refresh_people_list()
                
                if imported_count > 0:
                    self.lbl_status.setText(f"Successfully imported {imported_count} identities.")
                    QMessageBox.information(
                        self,
                        "Import Success",
                        f"Successfully imported {imported_count} identities from package."
                    )
                else:
                    self.lbl_status.setText("No identities imported.")
                    QMessageBox.warning(
                        self,
                        "Import",
                        "The package did not contain any valid identities with reference images."
                    )
            finally:
                shutil.rmtree(temp_extract_dir, ignore_errors=True)
                
        except zipfile.BadZipFile:
            self.lbl_status.setText("Import failed: incorrect password.")
            QMessageBox.critical(self, "Import Error", "Incorrect password or corrupted archive.")
        except Exception as e:
            self.lbl_status.setText("Import failed.")
            QMessageBox.critical(self, "Import Error", f"Failed to import identities: {e}")
        finally:
            self.lbl_status.setText("")
            self.progress_bar.setVisible(False)
            self.setEnabled(True)
            QApplication.restoreOverrideCursor()

    def _add_image(self):
        selected_items = self.list_people.selectedItems()
        if len(selected_items) != 1: return
        
        data = selected_items[0].data(Qt.UserRole)
        files, _ = QFileDialog.getOpenFileNames(self, "Select Reference Images", "", "Images (*.png *.jpg *.jpeg)")
        if files:
            import tempfile
            import cv2
            from PySide6.QtWidgets import QApplication
            
            cropped_paths = []
            for idx, f in enumerate(files):
                self.lbl_status.setText(f"Loading & detecting face in image {idx+1} of {len(files)}...")
                QApplication.processEvents()
                
                dialog = FaceCropDialog(f, self)
                if dialog.exec() == QDialog.Accepted:
                    cropped_bgr = dialog.cropped_image
                    if cropped_bgr is not None:
                        fd, temp_file_path = tempfile.mkstemp(suffix=".png")
                        os.close(fd)
                        cv2.imwrite(temp_file_path, cropped_bgr)
                        cropped_paths.append(temp_file_path)
                        
            if cropped_paths:
                import time
                QApplication.setOverrideCursor(Qt.WaitCursor)
                self.setEnabled(False)
                self.progress_bar.setValue(10)
                self.progress_bar.setVisible(True)
                
                total_images = len(cropped_paths)
                if self.identity_manager.use_sface:
                    rebuild_eta = max(2, int(total_images * 3.0))
                else:
                    rebuild_eta = max(1, int(total_images * 1.5))
                
                self.lbl_status.setText(f"Adding {total_images} reference image(s) to '{data['name']}'...")
                QApplication.processEvents()
                time.sleep(0.3)
                
                try:
                    if data["is_session"]:
                        for idx, cp in enumerate(cropped_paths):
                            self.lbl_status.setText(f"Saving image {idx+1}/{total_images}...")
                            self.progress_bar.setValue(10 + int(70 * (idx + 1) / total_images))
                            QApplication.processEvents()
                            self.identity_manager.add_session_identity(data["name"], cp)
                    else:
                        self.lbl_status.setText(f"Rebuilding biometric recognition model (ETA: ~{rebuild_eta}s)...")
                        self.progress_bar.setValue(80)
                        QApplication.processEvents()
                        self.identity_manager.add_identity(data["name"], cropped_paths)
                    
                    for cp in cropped_paths:
                        try:
                            if os.path.exists(cp):
                                os.remove(cp)
                        except Exception:
                            pass
                    
                    self.progress_bar.setValue(100)
                    QApplication.processEvents()
                    time.sleep(0.2)
                    self.progress_bar.setVisible(False)
                    self.lbl_status.setText(f"Successfully added {total_images} reference image(s) to '{data['name']}'.")
                    
                    self._load_person_images(data["name"], data["is_session"])
                finally:
                    self.progress_bar.setVisible(False)
                    self.setEnabled(True)
                    QApplication.restoreOverrideCursor()

    def _on_global_output_toggled(self, checked):
        self.settings.setValue("always_use_global_output", checked)
        if self.parent():
            if hasattr(self.parent(), "update_global_output_settings"):
                self.parent().update_global_output_settings()

    def _browse_global_dir(self):
        curr_dir = self.txt_output_dir.text()
        folder = QFileDialog.getExistingDirectory(self, "Select Global Output Folder", curr_dir)
        if folder:
            self.txt_output_dir.setText(folder)
            self.settings.setValue("global_output_dir", folder)
            # Create the directory if it does not exist.
            os.makedirs(folder, exist_ok=True)
            if self.parent():
                if hasattr(self.parent(), "update_global_output_settings"):
                    self.parent().update_global_output_settings()

    def _delete_individual_image(self, img_path, person_name, is_session):
        res = QMessageBox.question(self, "Delete Reference Image", "Are you sure you want to delete this reference image?")
        if res == QMessageBox.Yes:
            from PySide6.QtWidgets import QApplication
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.setEnabled(False)
            self.lbl_status.setText("Retraining face recognition model...")
            QApplication.processEvents()
            try:
                if os.path.exists(img_path):
                    os.remove(img_path)
                
                npy_path = img_path + ".sface.npy"
                if os.path.exists(npy_path):
                    os.remove(npy_path)
                
                lbph_path = img_path + ".lbph.png"
                if os.path.exists(lbph_path):
                    os.remove(lbph_path)
                
                self._load_person_images(person_name, is_session)
                if self.identity_manager:
                    self.identity_manager.reload_identities()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to delete image: {str(e)}")
            finally:
                self.lbl_status.setText("")
                self.setEnabled(True)
                QApplication.restoreOverrideCursor()

    def _init_shortcuts_tab(self):
        layout = QVBoxLayout(self.tab_shortcuts)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        lbl_title = QLabel("Keyboard Shortcut Configuration")
        lbl_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #10B981;")
        layout.addWidget(lbl_title)

        lbl_desc = QLabel("Customize SafeMARC's keyboard-driven workflow. Click any shortcut value to rebind it by pressing your new key combination.")
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("color: #9CA3AF; font-size: 12px; margin-bottom: 5px;")
        layout.addWidget(lbl_desc)

        self.lbl_shortcut_conflict = QLabel("")
        self.lbl_shortcut_conflict.setWordWrap(True)
        self.lbl_shortcut_conflict.setStyleSheet("color: #E11D48; font-size: 12px; font-weight: bold;")
        self.lbl_shortcut_conflict.setVisible(False)
        layout.addWidget(self.lbl_shortcut_conflict)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { border: 1px solid #374151; border-radius: 8px; background-color: #111827; }
            QScrollBar:vertical { background: #111827; width: 8px; }
            QScrollBar::handle:vertical { background: #374151; border-radius: 4px; }
            QScrollBar::handle:vertical:hover { background: #4B5563; }
        """)
        
        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background-color: #111827;")
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(10, 10, 10, 10)
        scroll_layout.setSpacing(15)

        categories = ["General", "Review Actions", "Zoom & Navigation", "Batch Workflow", "Sensitive Box Keyboard Selection", "Identities Management"]
        
        self.shortcut_buttons = {}

        for cat in categories:
            cat_widget = QWidget()
            cat_widget.setObjectName("shortcutCategoryCard")
            cat_widget.setStyleSheet("""
                QWidget#shortcutCategoryCard {
                    background-color: #1F2937;
                    border: 1px solid #374151;
                    border-radius: 8px;
                }
                QLabel { background: transparent; }
            """)
            cat_layout = QVBoxLayout(cat_widget)
            cat_layout.setContentsMargins(12, 12, 12, 12)
            cat_layout.setSpacing(10)

            cat_title = QLabel(cat)
            cat_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #10B981;")
            cat_layout.addWidget(cat_title)

            # Grid layout for shortcuts.
            grid = QGridLayout()
            grid.setSpacing(8)
            grid.setColumnStretch(0, 1) # Action label layout sizing.
            grid.setColumnStretch(1, 0) # Button layout sizing.
            grid.setColumnStretch(2, 0) # Reset button layout sizing.

            row = 0
            for key, meta in SHORTCUT_METADATA.items():
                if meta["category"] != cat:
                    continue

                lbl_action = QLabel(meta["label"])
                lbl_action.setStyleSheet("color: #E5E7EB; font-size: 13px; font-weight: 500;")

                current_val = self.settings.value(f"shortcut_{key}", meta["default"])

                btn_rebind = ShortcutRebindButton(current_val)
                btn_rebind.keySequenceChanged.connect(lambda seq, k=key: self._on_shortcut_changed(k, seq))
                btn_rebind.setFocusPolicy(Qt.StrongFocus)
                self.shortcut_buttons[key] = btn_rebind

                btn_reset = QPushButton()
                btn_reset.setIcon(svg_to_icon(SVG_RESET, 12))
                btn_reset.setIconSize(QSize(12, 12))
                btn_reset.setToolTip("Reset to Default")
                btn_reset.setCursor(Qt.PointingHandCursor)
                btn_reset.setFocusPolicy(Qt.StrongFocus)
                btn_reset.setStyleSheet("""
                    QPushButton {
                        background-color: #1F2937;
                        border: 1px solid #374151;
                        border-radius: 6px;
                        padding: 6px;
                    }
                    QPushButton:hover {
                        background-color: #374151;
                        border-color: #E11D48;
                    }
                """)
                btn_reset.clicked.connect(lambda _, k=key, d=meta["default"]: self._on_shortcut_reset(k, d))

                grid.addWidget(lbl_action, row, 0)
                grid.addWidget(btn_rebind, row, 1)
                grid.addWidget(btn_reset, row, 2)
                row += 1

            cat_layout.addLayout(grid)
            scroll_layout.addWidget(cat_widget)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # Global Reset All Button
        self.btn_reset_all_shortcuts = QPushButton("Reset All Shortcuts to Defaults")
        self.btn_reset_all_shortcuts.setCursor(Qt.PointingHandCursor)
        self.btn_reset_all_shortcuts.setStyleSheet("""
            QPushButton {
                background-color: #1F2937;
                color: #E5E7EB;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 13px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: #374151;
                border-color: #E11D48;
                color: #FFFFFF;
            }
        """)
        self.btn_reset_all_shortcuts.clicked.connect(self._reset_all_shortcuts)
        layout.addWidget(self.btn_reset_all_shortcuts, 0, Qt.AlignLeft)

        # Check for conflicts.
        self._check_for_conflicts()

    def _on_shortcut_changed(self, key: str, new_seq: str):
        self.settings.setValue(f"shortcut_{key}", new_seq)
        if hasattr(self, "local_shortcuts") and key in self.local_shortcuts:
            self.local_shortcuts[key].setKey(QKeySequence(new_seq))
        
        # Propagate to MainWindow if it has the update method
        if self.parent() and hasattr(self.parent(), "update_shortcut_key"):
            self.parent().update_shortcut_key(key, new_seq)
            
        self._check_for_conflicts()

    def _on_shortcut_reset(self, key: str, default_seq: str):
        self.settings.remove(f"shortcut_{key}") # Remove custom setting.
        btn = self.shortcut_buttons[key]
        btn.current_sequence = default_seq
        btn.setText(default_seq)
        btn.update_style()
        if hasattr(self, "local_shortcuts") and key in self.local_shortcuts:
            self.local_shortcuts[key].setKey(QKeySequence(default_seq))
        
        if self.parent() and hasattr(self.parent(), "update_shortcut_key"):
            self.parent().update_shortcut_key(key, default_seq)
            
        self._check_for_conflicts()

    def _reset_all_shortcuts(self):
        reply = QMessageBox.question(
            self, "Reset Shortcuts",
            "Are you sure you want to reset all keyboard shortcuts to their factory defaults?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            for key, meta in SHORTCUT_METADATA.items():
                self.settings.remove(f"shortcut_{key}")
                btn = self.shortcut_buttons[key]
                btn.current_sequence = meta["default"]
                btn.setText(meta["default"])
                btn.update_style()
                if hasattr(self, "local_shortcuts") and key in self.local_shortcuts:
                    self.local_shortcuts[key].setKey(QKeySequence(meta["default"]))
                
                if self.parent() and hasattr(self.parent(), "update_shortcut_key"):
                    self.parent().update_shortcut_key(key, meta["default"])
            
            self._check_for_conflicts()

    def _check_for_conflicts(self):
        # Scan buttons for duplicates.
        seq_to_keys = {}
        for key, btn in self.shortcut_buttons.items():
            seq = btn.current_sequence.strip()
            if seq:
                if seq not in seq_to_keys:
                    seq_to_keys[seq] = []
                seq_to_keys[seq].append(key)

        conflicts = []
        for seq, keys in seq_to_keys.items():
            if len(keys) > 1:
                labels = [SHORTCUT_METADATA[k]["label"] for k in keys]
                conflicts.append(f"'{seq}' is assigned to: " + ", ".join(labels))

        if conflicts:
            self.lbl_shortcut_conflict.setText("⚠️ Shortcut Conflict Detected:\n" + "\n".join(conflicts))
            self.lbl_shortcut_conflict.setVisible(True)
        else:
            self.lbl_shortcut_conflict.setVisible(False)


class InteractiveCropLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.crop_rect = QRect()
        
        self.is_dragging = False
        self.is_resizing = False
        self.drag_start = QPoint()
        self.resize_handle = None
        
    def set_crop_rect(self, rect: QRect):
        self.crop_rect = rect
        self.update()
        
    def get_crop_rect(self) -> QRect:
        return self.crop_rect

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.crop_rect.isValid() and self.pixmap():
            painter = QPainter(self)
            overlay_color = QColor(0, 0, 0, 160)
            painter.fillRect(0, 0, self.width(), self.crop_rect.top(), overlay_color)
            painter.fillRect(0, self.crop_rect.bottom() + 1, self.width(), self.height() - self.crop_rect.bottom() - 1, overlay_color)
            painter.fillRect(0, self.crop_rect.top(), self.crop_rect.left(), self.crop_rect.height(), overlay_color)
            painter.fillRect(self.crop_rect.right() + 1, self.crop_rect.top(), self.width() - self.crop_rect.right() - 1, self.crop_rect.height(), overlay_color)
            
            pen = QPen(QColor("#10B981"), 2, Qt.SolidLine)
            painter.setPen(pen)
            painter.drawRect(self.crop_rect)
            
            handle_color = QColor("#10B981")
            painter.setBrush(handle_color)
            painter.setPen(Qt.NoPen)
            r = 5
            painter.drawEllipse(self.crop_rect.topLeft(), r, r)
            painter.drawEllipse(self.crop_rect.topRight(), r, r)
            painter.drawEllipse(self.crop_rect.bottomLeft(), r, r)
            painter.drawEllipse(self.crop_rect.bottomRight(), r, r)
            painter.end()

    def _get_handle_at(self, pos: QPoint):
        if not self.crop_rect.isValid():
            return None
        
        tl = self.crop_rect.topLeft()
        tr = self.crop_rect.topRight()
        bl = self.crop_rect.bottomLeft()
        br = self.crop_rect.bottomRight()
        
        dist = lambda p1, p2: (p1.x() - p2.x())**2 + (p1.y() - p2.y())**2
        threshold = 12 * 12
        
        if dist(pos, tl) < threshold: return 'TL'
        if dist(pos, tr) < threshold: return 'TR'
        if dist(pos, bl) < threshold: return 'BL'
        if dist(pos, br) < threshold: return 'BR'
        if self.crop_rect.contains(pos): return 'M'
        return None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            handle = self._get_handle_at(event.pos())
            if handle:
                self.drag_start = event.pos()
                self.resize_handle = handle
                if handle == 'M':
                    self.is_dragging = True
                else:
                    self.is_resizing = True
            else:
                self.drag_start = event.pos()
                self.crop_rect = QRect(event.pos(), QSize(0, 0))
                self.resize_handle = 'BR'
                self.is_resizing = True

    def mouseMoveEvent(self, event):
        handle = self._get_handle_at(event.pos())
        if not (self.is_dragging or self.is_resizing):
            if handle in ('TL', 'BR'):
                self.setCursor(Qt.SizeFDiagCursor)
            elif handle in ('TR', 'BL'):
                self.setCursor(Qt.SizeBDiagCursor)
            elif handle == 'M':
                self.setCursor(Qt.SizeAllCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
                
        if self.is_dragging:
            delta = event.pos() - self.drag_start
            self.drag_start = event.pos()
            new_rect = self.crop_rect.translated(delta)
            if self.rect().contains(new_rect):
                self.crop_rect = new_rect
                self.update()
        elif self.is_resizing:
            r = self.crop_rect
            p = event.pos()
            
            if self.resize_handle == 'TL':
                anchor = r.bottomRight()
                dx = anchor.x() - p.x()
                dy = anchor.y() - p.y()
                max_side = min(anchor.x(), anchor.y())
                side = min(max(dx, dy), max_side)
                self.crop_rect = QRect(QPoint(anchor.x() - side, anchor.y() - side), anchor).normalized()
            elif self.resize_handle == 'TR':
                anchor = r.bottomLeft()
                dx = p.x() - anchor.x()
                dy = anchor.y() - p.y()
                max_side = min(self.width() - anchor.x(), anchor.y())
                side = min(max(dx, dy), max_side)
                self.crop_rect = QRect(QPoint(anchor.x(), anchor.y() - side), QPoint(anchor.x() + side, anchor.y())).normalized()
            elif self.resize_handle == 'BL':
                anchor = r.topRight()
                dx = anchor.x() - p.x()
                dy = p.y() - anchor.y()
                max_side = min(anchor.x(), self.height() - anchor.y())
                side = min(max(dx, dy), max_side)
                self.crop_rect = QRect(QPoint(anchor.x() - side, anchor.y()), QPoint(anchor.x(), anchor.y() + side)).normalized()
            elif self.resize_handle == 'BR':
                anchor = r.topLeft()
                dx = p.x() - anchor.x()
                dy = p.y() - anchor.y()
                max_side = min(self.width() - anchor.x(), self.height() - anchor.y())
                side = min(max(dx, dy), max_side)
                self.crop_rect = QRect(anchor, QPoint(anchor.x() + side, anchor.y() + side)).normalized()
            self.update()

    def mouseReleaseEvent(self, event):
        self.is_dragging = False
        self.is_resizing = False
        self.resize_handle = None
        self.setCursor(Qt.ArrowCursor)


class FaceCropDialog(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.raw_image_path = image_path
        self.cropped_image = None
        
        self.setWindowTitle("Adjust Face Crop")
        self.setMinimumSize(540, 600)
        self.setStyleSheet("""
            QDialog { background-color: #0B0F19; }
            QLabel { background: transparent; background-color: transparent; }
            QLabel#titleLabel { font-size: 16px; font-weight: 800; color: #10B981; font-family: 'Segoe UI', Arial, sans-serif; letter-spacing: 0.5px; }
            QLabel#subtitleLabel { color: #9CA3AF; font-size: 12px; font-family: 'Segoe UI', Arial, sans-serif; }
            QPushButton {
                background-color: #1F2937;
                color: #E5E7EB;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 13px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover { background-color: #374151; border-color: #4B5563; color: #FFFFFF; }
            QPushButton#btnConfirm {
                background-color: #10B981;
                color: #FFFFFF;
                border: 1px solid #059669;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 700;
                font-size: 13px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton#btnConfirm:hover {
                background-color: #059669;
                border-color: #047857;
            }
            QPushButton#btnConfirm:pressed {
                background-color: #047857;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        lbl_title = QLabel("Reference Face Cropping")
        lbl_title.setObjectName("titleLabel")
        layout.addWidget(lbl_title)
        
        lbl_sub = QLabel("Drag corners to resize or drag the middle to center the face crop for identity training.")
        lbl_sub.setObjectName("subtitleLabel")
        lbl_sub.setWordWrap(True)
        layout.addWidget(lbl_sub)
        
        self.workspace_card = QWidget()
        self.workspace_card.setObjectName("workspaceCard")
        self.workspace_card.setStyleSheet("""
            QWidget#workspaceCard {
                background-color: #111827;
                border: 1px solid #374151;
                border-radius: 10px;
            }
        """)
        workspace_layout = QHBoxLayout(self.workspace_card)
        workspace_layout.setContentsMargins(15, 15, 15, 15)
        workspace_layout.setAlignment(Qt.AlignCenter)
        
        self.crop_label = InteractiveCropLabel()
        self.crop_label.setAlignment(Qt.AlignCenter)
        self.crop_label.setStyleSheet("border: none; background-color: transparent;")
        workspace_layout.addWidget(self.crop_label)
        
        layout.addWidget(self.workspace_card, 1)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_confirm = QPushButton("Confirm Crop")
        self.btn_confirm.setObjectName("btnConfirm")
        self.btn_confirm.clicked.connect(self._on_confirm)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_confirm)
        layout.addLayout(btn_layout)
        
        self._load_and_detect()
        apply_focus_indicators(self)
        
    def _load_and_detect(self):
        import cv2
        self.raw_img = cv2.imread(self.raw_image_path)
        if self.raw_img is None:
            self.reject()
            return
            
        raw_h, raw_w = self.raw_img.shape[:2]
        display_max = 480
        scale = min(display_max / raw_w, display_max / raw_h, 1.0)
        scaled_w = int(raw_w * scale)
        scaled_h = int(raw_h * scale)
        
        pixmap = QPixmap(self.raw_image_path).scaled(scaled_w, scaled_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.crop_label.setPixmap(pixmap)
        self.crop_label.setFixedSize(scaled_w, scaled_h)
        self.scale_factor = scale
        
        gray = cv2.cvtColor(self.raw_img, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) > 0:
            fx, fy, fw, fh = max(faces, key=lambda f: f[2] * f[3])
            side = max(fw, fh)
            pad = int(side * 0.15)
            raw_side = side + 2 * pad
            
            cx = fx + fw // 2
            cy = fy + fh // 2
            
            rx = max(0, cx - raw_side // 2)
            ry = max(0, cy - raw_side // 2)
            
            if rx + raw_side > raw_w:
                rx = max(0, raw_w - raw_side)
            if ry + raw_side > raw_h:
                ry = max(0, raw_h - raw_side)
                
            rw = rh = min(raw_side, raw_w - rx, raw_h - ry)
        else:
            rw = rh = min(raw_w, raw_h, 180)
            rx = (raw_w - rw) // 2
            ry = (raw_h - rh) // 2
            
        dx = int(rx * scale)
        dy = int(ry * scale)
        dw = int(rw * scale)
        dh = int(rh * scale)
        self.crop_label.set_crop_rect(QRect(dx, dy, dw, dh))
        
    def _on_confirm(self):
        import cv2
        rect = self.crop_label.get_crop_rect()
        if not rect.isValid() or rect.width() < 10 or rect.height() < 10:
            QMessageBox.warning(self, "Invalid Selection", "Please draw a valid crop selection first.")
            return
            
        rx = int(rect.left() / self.scale_factor)
        ry = int(rect.top() / self.scale_factor)
        rw = int(rect.width() / self.scale_factor)
        rh = int(rect.height() / self.scale_factor)
        
        raw_h, raw_w = self.raw_img.shape[:2]
        rx = max(0, min(rx, raw_w - 1))
        ry = max(0, min(ry, raw_h - 1))
        rw = max(10, min(rw, raw_w - rx))
        rh = max(10, min(rh, raw_h - ry))
        
        self.cropped_image = self.raw_img[ry:ry+rh, rx:rx+rw]
        self.accept()


class NewIdentityDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Identity")
        self.setFixedSize(360, 180)
        self.setStyleSheet("""
            QDialog { background-color: #0B0F19; }
            QLabel { color: #E5E7EB; font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; }
            QLineEdit {
                background-color: #1F2937;
                color: #F3F4F6;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLineEdit:focus { border-color: #10B981; }
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
        
        lbl = QLabel("Enter person name:")
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("e.g. John Doe")
        self.txt_name.returnPressed.connect(self._on_save)
        
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
        layout.addWidget(self.txt_name)
        layout.addLayout(btn_layout)
        apply_focus_indicators(self)
        
    def _on_save(self):
        name = self.txt_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Invalid Name", "Please enter a valid person name.")
            return
        self.accept()
        
    def get_name(self):
        return self.txt_name.text().strip()

