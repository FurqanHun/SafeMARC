import os
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPainter, QImage, QPixmap
from PySide6.QtSvg import QSvgRenderer

def svg_to_icon(svg_str: str, size: int = 16) -> QIcon:
    renderer = QSvgRenderer(svg_str.encode('utf-8'))
    image = QImage(size, size, QImage.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    return QIcon(QPixmap.fromImage(image))

SVG_X = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E5E7EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>'''

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(450, 320)
        
        # Consistent background and window style
        self.setStyleSheet("""
            QDialog {
                background-color: #0B0F19;
            }
            QLabel#headingLabel {
                background: transparent;
            }
            QWidget#settingsCard {
                background-color: #111827;
                border: 1px solid #374151;
                border-radius: 10px;
            }
            QWidget#settingsCard QLabel {
                background: transparent;
            }
            QPushButton {
                background-color: #1F2937;
                color: #E5E7EB;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 10px 18px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #374151;
                border-color: #4B5563;
                color: #FFFFFF;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Header
        header_widget = QWidget()
        header_widget.setStyleSheet("background: transparent;")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel("APPLICATION SETTINGS")
        title_label.setObjectName("headingLabel")
        title_label.setStyleSheet("""
            font-size: 16px; 
            font-weight: 800; 
            color: #10B981; 
            letter-spacing: 0.5px;
            font-family: 'Segoe UI', Arial, sans-serif;
            background: transparent;
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addWidget(header_widget)
        
        # Subtle separator
        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #374151;")
        layout.addWidget(sep)
        
        # Content Card
        card = QWidget()
        card.setObjectName("settingsCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        
        msg = QLabel("Settings panel is currently empty for development.")
        msg.setStyleSheet("color: #9CA3AF; font-size: 13px; font-weight: 500; background: transparent;")
        card_layout.addWidget(msg)
        
        layout.addWidget(card)
        layout.addStretch()
        
        # Bottom Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        close_btn = QPushButton(" Close")
        close_btn.setIcon(svg_to_icon(SVG_X))
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
