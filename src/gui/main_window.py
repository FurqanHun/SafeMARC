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
from PySide6.QtGui import QFont, QIcon, QColor

from src.core.scanner import SafeScanner
from src.core.batch_processor import BatchProcessor
from src.gui.preview_widget import PreviewWidget


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
        self.title_label = QLabel("🛡️ SafeMARC")
        self.title_label.setStyleSheet(
            "font-size: 28px; font-weight: 800; color: #4CAF50; letter-spacing: 2px;"
        )
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        self.status_label = QLabel(engine_status)
        self.status_label.setStyleSheet("font-size: 14px; color: #aaaaaa;")
        header_layout.addWidget(self.status_label)
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
        self.file_list.setStyleSheet(
            "QListWidget { background-color: #1e1e1e; border-radius: 8px; padding: 5px; font-size: 14px; }"
            "QListWidget::item:selected { background-color: #2e7d32; border-radius: 4px; }"
        )
        self.file_list.itemClicked.connect(self.on_file_selected)
        sidebar_layout.addWidget(QLabel("Queue:"))
        sidebar_layout.addWidget(self.file_list, 1)

        # Queue Buttons
        queue_btns_layout = QHBoxLayout()
        self.btn_add_file = QPushButton("📄 Add Files")
        self.btn_add_file.clicked.connect(self.add_files)
        self.btn_add_folder = QPushButton("📁 Add Folder")
        self.btn_add_folder.clicked.connect(self.add_folder)
        self.btn_remove = QPushButton("➖ Remove")
        self.btn_remove.clicked.connect(self.remove_selected_file)
        self.btn_clear = QPushButton("🗑️ Clear")
        self.btn_clear.clicked.connect(self.clear_queue)
        
        for btn in (self.btn_add_file, self.btn_add_folder, self.btn_remove, self.btn_clear):
            btn.setStyleSheet("padding: 8px; border-radius: 4px; background-color: #333;")
        
        queue_btns_layout.addWidget(self.btn_add_file)
        queue_btns_layout.addWidget(self.btn_add_folder)
        queue_btns_layout.addWidget(self.btn_remove)
        queue_btns_layout.addWidget(self.btn_clear)
        sidebar_layout.addLayout(queue_btns_layout)

        # Settings Group
        settings_group = QGroupBox("Vision Settings")
        settings_group.setStyleSheet("QGroupBox { font-weight: bold; padding-top: 15px; margin-top: 10px; }")
        settings_layout = QVBoxLayout(settings_group)
        
        # Vision Mode Dropdown
        self.cmb_vision_mode = QComboBox()
        self.cmb_vision_mode.addItem("Faces Only", "faces")
        self.cmb_vision_mode.addItem("Full Body", "bodies")
        self.cmb_vision_mode.currentIndexChanged.connect(self.on_vision_mode_changed)
        
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Vision Target:"))
        mode_layout.addWidget(self.cmb_vision_mode)
        settings_layout.addLayout(mode_layout)
        
        self.chk_suffix = QCheckBox("Append '_safemarc_redacted' suffix")
        self.chk_suffix.setChecked(False)  # Default uses folder
        self.chk_suffix.setToolTip("If unchecked, creates a 'safemarc_redacted_output' folder.")
        settings_layout.addWidget(self.chk_suffix)

        sidebar_layout.addWidget(settings_group)
        
        # Text Patterns Group
        text_group = QGroupBox("Text Redaction")
        text_group.setStyleSheet("QGroupBox { font-weight: bold; padding-top: 15px; margin-top: 10px; }")
        text_layout = QVBoxLayout(text_group)
        
        self.text_patterns_layout = QVBoxLayout()
        text_layout.addLayout(self.text_patterns_layout)
        
        btn_add_text = QPushButton("➕ Add Text")
        btn_add_text.clicked.connect(lambda: self.add_pattern_row(is_regex=False))
        btn_add_regex = QPushButton("➕ Add Regex")
        btn_add_regex.clicked.connect(lambda: self.add_pattern_row(is_regex=True))
        
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
        self.preview_widget.setStyleSheet("border: 2px dashed #4CAF50; border-radius: 8px; background-color: #121212;")
        preview_layout.addWidget(self.preview_widget)

        # Action Buttons
        action_layout = QHBoxLayout()

        self.btn_skip = QPushButton("⏭️ Skip")
        self.btn_skip.setStyleSheet("padding: 12px; font-size: 16px; font-weight: bold; background-color: #555555; color: white; border-radius: 6px;")
        self.btn_skip.hide()
        self.btn_skip.clicked.connect(self.skip_current)

        self.btn_redact_next = QPushButton("🛡️ Redact & Next")
        self.btn_redact_next.setStyleSheet("padding: 12px; font-size: 16px; font-weight: bold; background-color: #d32f2f; color: white; border-radius: 6px;")
        self.btn_redact_next.hide()
        self.btn_redact_next.clicked.connect(self.redact_current)

        self.btn_start_review = QPushButton("🚀 Start Review Process")
        self.btn_start_review.setStyleSheet("padding: 12px; font-size: 16px; font-weight: bold; background-color: #388E3C; color: white; border-radius: 6px;")
        self.btn_start_review.clicked.connect(self.start_batch)

        action_layout.addWidget(self.btn_skip)
        action_layout.addWidget(self.btn_redact_next)
        action_layout.addWidget(self.btn_start_review)
        preview_layout.addLayout(action_layout)

        self.splitter.addWidget(preview_container)
        self.splitter.setSizes([300, 700])

        self.current_file_path = None
        self.current_hits = []
        
        # Batch Mode State
        self.is_batch_mode = False
        self.batch_index = -1
        self.batch_success_count = 0

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
        files, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", "Supported (*.png *.jpg *.jpeg *.pdf)")
        if files:
            for f in files:
                self.add_to_queue(f)

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Directory")
        if folder:
            for root, _, filenames in os.walk(folder):
                for filename in filenames:
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.pdf')):
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

    def cancel_batch_mode(self):
        self.is_batch_mode = False
        self.btn_start_review.show()
        self.btn_skip.hide()
        self.btn_redact_next.hide()

    def on_file_selected(self, item):
        # If user manually clicks an item during batch mode, cancel batch mode
        if self.is_batch_mode and self.file_list.row(item) != self.batch_index:
            self.cancel_batch_mode()
            
        file_path = item.data(Qt.UserRole)
        self.current_file_path = file_path
        self.current_hits = []
        
        # Load preview (PDFs might need special handling, but for images it works directly)
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            self.preview_widget.load_image(file_path)

    def redact_current(self):
        if not self.scanner or not self.current_file_path or not self.current_hits:
            return

        selected_hits = self.preview_widget.get_selected_hits()
        if not selected_hits:
            QMessageBox.warning(self, "Warning", "No hits selected for redaction.")
            return

        out_path = self.processor.get_output_path(
            self.current_file_path, 
            use_suffix=self.chk_suffix.isChecked()
        )
        
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

        self.is_batch_mode = True
        self.batch_index = 0
        self.batch_success_count = 0
        
        # Update UI state
        self.btn_start_review.hide()
        self.btn_skip.show()
        self.btn_redact_next.show()
        self.btn_redact_next.setEnabled(False)
        
        self.load_next_batch_item()

    def skip_current(self):
        if not self.is_batch_mode:
            return
            
        self.file_list.item(self.batch_index).setForeground(QColor("#888888"))
        self.batch_index += 1
        self.load_next_batch_item()

    def load_next_batch_item(self):
        # Base case: Finished queue
        if self.batch_index >= self.file_list.count():
            self.cancel_batch_mode()
            QMessageBox.information(self, "Complete", f"Review complete.\nSuccessfully redacted {self.batch_success_count} files.")
            return
            
        # Highlight current item in the list
        item = self.file_list.item(self.batch_index)
        self.file_list.setCurrentItem(item)
        file_path = item.data(Qt.UserRole)
        
        self.current_file_path = file_path
        self.current_hits = []
        
        # Attempt to load and auto-scan
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            self.preview_widget.load_image(file_path)
            
            try:
                hits = self.scanner.scan(file_path)
                if not hits:
                    # Auto skip if no hits found
                    item.setForeground(QColor("#888888"))
                    self.batch_index += 1
                    # Use QTimer to prevent recursion depth issues on huge empty queues
                    from PySide6.QtCore import QTimer
                    QTimer.singleShot(0, self.load_next_batch_item)
                    return
                else:
                    self.current_hits = hits
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
