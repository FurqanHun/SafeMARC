from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QWidget, QTabWidget, QListWidget, QListWidgetItem, QScrollArea, QFrame, QFileDialog, QMessageBox, QInputDialog, QGridLayout
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPainter, QImage, QPixmap, QColor
from src.core.identity_manager import IdentityManager
import os

# ... (svg_to_icon and SVG_X remain same)

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
        """)

        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Tab 1: General (Current settings)
        self.tab_general = QWidget()
        gen_layout = QVBoxLayout(self.tab_general)
        gen_layout.addWidget(QLabel("General settings will appear here."))
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
            
            lbl = QLabel()
            lbl.setPixmap(pixmap)
            lbl.setFixedSize(100, 100)
            lbl.setStyleSheet("border: 1px solid #374151; border-radius: 4px;")
            self.grid_layout.addWidget(lbl, i // 3, i % 3)

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
