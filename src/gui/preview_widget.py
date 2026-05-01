from typing import List, Callable
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsPixmapItem
from PySide6.QtGui import QPixmap, QPen, QColor, QBrush
from PySide6.QtCore import Qt, QRectF

from src.core.types import SensitiveHit

class SelectableHitItem(QGraphicsRectItem):
    def __init__(self, hit: SensitiveHit, on_toggle: Callable):
        super().__init__(QRectF(hit.x, hit.y, hit.w, hit.h))
        self.hit = hit
        self.on_toggle = on_toggle
        self.is_selected = True
        
        self.setAcceptHoverEvents(True)
        self.update_style()

    def update_style(self):
        if self.is_selected:
            self.setPen(QPen(QColor(255, 0, 0, 200), 3))
            self.setBrush(QBrush(QColor(255, 0, 0, 50)))
        else:
            self.setPen(QPen(QColor(100, 100, 100, 200), 2, Qt.DashLine))
            self.setBrush(QBrush(QColor(0, 0, 0, 0)))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_selected = not self.is_selected
            self.update_style()
            self.on_toggle(self.hit, self.is_selected)
            event.accept()
        else:
            super().mousePressEvent(event)

from PySide6.QtGui import QPainter

class PreviewWidget(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        self.setRenderHint(self.renderHints() | QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        
        self.current_pixmap_item = None
        self.hit_items = []
        self.active_hits = []

    def load_image(self, file_path: str):
        self.scene.clear()
        self.current_pixmap_item = None
        self.hit_items = []
        self.active_hits = []
        
        pixmap = QPixmap(file_path)
        if not pixmap.isNull():
            self.current_pixmap_item = QGraphicsPixmapItem(pixmap)
            self.scene.addItem(self.current_pixmap_item)
            self.scene.setSceneRect(0, 0, pixmap.width(), pixmap.height())
            self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def display_hits(self, hits: List[SensitiveHit]):
        self.active_hits = hits.copy()
        
        for item in self.hit_items:
            self.scene.removeItem(item)
        self.hit_items.clear()
        
        for hit in hits:
            item = SelectableHitItem(hit, self.on_hit_toggled)
            self.scene.addItem(item)
            self.hit_items.append(item)

    def on_hit_toggled(self, hit: SensitiveHit, is_selected: bool):
        if is_selected and hit not in self.active_hits:
            self.active_hits.append(hit)
        elif not is_selected and hit in self.active_hits:
            self.active_hits.remove(hit)

    def get_selected_hits(self) -> List[SensitiveHit]:
        return self.active_hits

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.current_pixmap_item:
            self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
