from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QWidget, QTabWidget, QListWidget, QListWidgetItem, QScrollArea, QFrame, QFileDialog, QMessageBox, QInputDialog, QGridLayout, QCheckBox, QLineEdit
from PySide6.QtCore import Qt, QSize, QSettings, QStandardPaths
from PySide6.QtGui import QIcon, QPainter, QImage, QPixmap, QColor
from src.core.identity_manager import IdentityManager
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

class SettingsDialog(QDialog):
    def __init__(self, scanner, parent=None):
        super().__init__(parent)
        self.scanner = scanner
        self.identity_manager = scanner.identity_manager if scanner else None
        self.setWindowTitle("Settings")
        self.setMinimumSize(600, 450)
        
        self.setStyleSheet("""
            QDialog { background-color: #0B0F19; }
            QTabWidget::pane { border: 1px solid #374151; background: #111827; border-radius: 8px; }
            QTabBar::tab {
                background: #1F2937;
                color: #9CA3AF;
                padding: 10px 20px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 2px;
            }
            QTabBar::tab:selected { background: #111827; color: #10B981; font-weight: bold; border: 1px solid #374151; border-bottom: none; }
            QListWidget { background-color: #1F2937; border: 1px solid #374151; color: #E5E7EB; border-radius: 6px; outline: 0; }
            QListWidget::item { padding: 8px; border-bottom: 1px solid #374151; }
            QListWidget::item:selected { background-color: #10B981; color: #FFFFFF; }
            QPushButton {
                background-color: #1F2937;
                color: #E5E7EB;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 8px 14px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #374151; border-color: #4B5563; }
            QPushButton:disabled { background-color: #1F2937; color: #4B5563; border-color: #1F2937; }
            QCheckBox {
                spacing: 8px;
                color: #E5E7EB;
                font-size: 13px;
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
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #10B981;
            }
        """)

        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Tab 1: General (Current settings)
        self.settings = QSettings("SafeMARC", "SafeMARC")
        default_out = self.settings.value("global_output_dir", "")
        if not default_out:
            pictures_dir = QStandardPaths.writableLocation(QStandardPaths.PicturesLocation)
            if not pictures_dir:
                pictures_dir = os.path.expanduser("~/Pictures")
            default_out = os.path.join(pictures_dir, "SafeMARC_Output")
            self.settings.setValue("global_output_dir", default_out)

        self.tab_general = QWidget()
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

        self.btn_browse_dir = QPushButton("Browse...")
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
        
        # Tab 2: Identities
        self.tab_identities = QWidget()
        id_layout = QHBoxLayout(self.tab_identities)
        
        # Left: People List
        left_panel = QVBoxLayout()
        self.list_people = QListWidget()
        self.list_people.currentRowChanged.connect(self._on_person_selected)
        left_panel.addWidget(QLabel("People / Identities"))
        left_panel.addWidget(self.list_people)
        
        btn_people_layout = QHBoxLayout()
        self.btn_add_person = QPushButton("+")
        self.btn_add_person.setToolTip("Add Person")
        self.btn_add_person.clicked.connect(self._add_person)
        self.btn_del_person = QPushButton("-")
        self.btn_del_person.setToolTip("Delete Person")
        self.btn_del_person.clicked.connect(self._del_person)
        btn_people_layout.addWidget(self.btn_add_person)
        btn_people_layout.addWidget(self.btn_del_person)
        left_panel.addLayout(btn_people_layout)
        
        id_layout.addLayout(left_panel, 1)
        
        # Right: Thumbnails
        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("Reference Images"))
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.grid_layout = QGridLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)
        right_panel.addWidget(self.scroll_area)
        
        self.btn_add_img = QPushButton("Add Image")
        self.btn_add_img.clicked.connect(self._add_image)
        self.btn_add_img.setEnabled(False)
        right_panel.addWidget(self.btn_add_img)
        
        id_layout.addLayout(right_panel, 2)
        
        self.tabs.addTab(self.tab_identities, "Identities")
        
        # Close Button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)
        
        self._refresh_people_list()

    def _refresh_people_list(self):
        self.list_people.clear()
        if not self.identity_manager: return
        
        # Permanent identities
        identities_dir = self.identity_manager.identities_dir
        if os.path.exists(identities_dir):
            for name in sorted(os.listdir(identities_dir)):
                if name == "session_temp": continue
                path = os.path.join(identities_dir, name)
                if os.path.isdir(path):
                    item = QListWidgetItem(name)
                    item.setData(Qt.UserRole, {"name": name, "is_session": False})
                    self.list_people.addItem(item)
                    
        # Session identities
        session_dir = os.path.join(identities_dir, "session_temp")
        if os.path.exists(session_dir):
            for name in sorted(os.listdir(session_dir)):
                path = os.path.join(session_dir, name)
                if os.path.isdir(path):
                    item = QListWidgetItem(f"{name} (Session)")
                    item.setData(Qt.UserRole, {"name": name, "is_session": True})
                    item.setForeground(QColor("#10B981"))
                    self.list_people.addItem(item)

    def _on_person_selected(self, row):
        if row < 0:
            self.btn_add_img.setEnabled(False)
            self._clear_grid()
            return
            
        item = self.list_people.item(row)
        data = item.data(Qt.UserRole)
        self.btn_add_img.setEnabled(True)
        self._load_person_images(data["name"], data["is_session"])

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
        name, ok = QInputDialog.getText(self, "New Identity", "Enter person name:")
        if ok and name.strip():
            person_dir = os.path.join(self.identity_manager.identities_dir, name.strip())
            os.makedirs(person_dir, exist_ok=True)
            self._refresh_people_list()
            # Select the new person
            items = self.list_people.findItems(name.strip(), Qt.MatchExactly)
            if items:
                self.list_people.setCurrentItem(items[0])

    def _del_person(self):
        item = self.list_people.currentItem()
        if not item: return
        
        data = item.data(Qt.UserRole)
        res = QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete identity '{data['name']}'?")
        if res == QMessageBox.Yes:
            import shutil
            base = os.path.join(self.identity_manager.identities_dir, "session_temp") if data["is_session"] else self.identity_manager.identities_dir
            shutil.rmtree(os.path.join(base, data["name"]))
            self._refresh_people_list()
            self.identity_manager.reload_identities()

    def _add_image(self):
        item = self.list_people.currentItem()
        if not item: return
        
        data = item.data(Qt.UserRole)
        files, _ = QFileDialog.getOpenFileNames(self, "Select Reference Images", "", "Images (*.png *.jpg *.jpeg)")
        if files:
            if data["is_session"]:
                for f in files:
                    self.identity_manager.add_session_identity(data["name"], f)
            else:
                self.identity_manager.add_identity(data["name"], files)
            self._load_person_images(data["name"], data["is_session"])

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
            # Create the directory if it doesn't exist
            os.makedirs(folder, exist_ok=True)
            if self.parent():
                if hasattr(self.parent(), "update_global_output_settings"):
                    self.parent().update_global_output_settings()

    def _delete_individual_image(self, img_path, person_name, is_session):
        res = QMessageBox.question(self, "Delete Reference Image", "Are you sure you want to delete this reference image?")
        if res == QMessageBox.Yes:
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

