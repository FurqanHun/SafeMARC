from typing import List, Callable
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsPixmapItem, QGraphicsTextItem
from PySide6.QtGui import QPixmap, QPen, QColor, QBrush, QFont
from PySide6.QtCore import Qt, QRectF

from src.core.types import SensitiveHit

class SelectableHitItem(QGraphicsRectItem):
    def __init__(self, hit: SensitiveHit, on_toggle: Callable):
        super().__init__(QRectF(hit.x, hit.y, hit.w, hit.h))
        self.hit = hit
        self.on_toggle = on_toggle
        self.is_selected = True
        
        self.setAcceptHoverEvents(True)
        
        # Identity Label
        self.text_item = None
        if hit.identity:
            self.text_item = QGraphicsTextItem(hit.identity, self)
            self.text_item.setPos(hit.x, hit.y - 20)
            self.text_item.setDefaultTextColor(QColor("#10B981"))
            font = QFont("Segoe UI", 10, QFont.Bold)
            self.text_item.setFont(font)

        self.update_style()

    def update_style(self):
        if self.is_selected:
            color = QColor(16, 185, 129, 200) if self.hit.identity else QColor(255, 0, 0, 200)
            self.setPen(QPen(color, 3))
            self.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), 50)))
            if self.text_item: self.text_item.setVisible(True)
        else:
            self.setPen(QPen(QColor(100, 100, 100, 200), 2, Qt.DashLine))
            self.setBrush(QBrush(QColor(0, 0, 0, 0)))
            if self.text_item: self.text_item.setVisible(False)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_selected = not self.is_selected
            self.update_style()
            self.on_toggle(self.hit, self.is_selected)
            event.accept()
        else:
            super().mousePressEvent(event)

    def contextMenuEvent(self, event):
        if self.hit.label == "FACE":
            from PySide6.QtWidgets import QMenu
            menu = QMenu()
            add_action = menu.addAction("Add as Known Identity...")
            
            action = menu.exec(event.screenPos())
            if action == add_action:
                # We need to notify the parent to handle cropping and naming
                self.scene().views()[0].on_add_identity_requested(self.hit)
        
        event.accept()

from PySide6.QtGui import QPainter

from PySide6.QtCore import Qt, QRectF, Signal

class PreviewWidget(QGraphicsView):
    identityRequested = Signal(object) # Passes the SensitiveHit
    
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        self.setRenderHint(self.renderHints() | QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.current_pixmap_item = None
        self.hit_items = []
        self.active_hits = []
        
        self.drawing_mode = False
        self.draw_start_point = None
        self.current_drawing_rect = None
        self.on_manual_hit_added = None
        self.zoom_factor = 1.0

    def on_add_identity_requested(self, hit: SensitiveHit):
        self.identityRequested.emit(hit)

    def set_drawing_mode(self, enabled: bool):
        self.drawing_mode = enabled
        if enabled:
            self.setDragMode(QGraphicsView.NoDrag)
            self.viewport().setCursor(Qt.CrossCursor)
        else:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self.viewport().setCursor(Qt.ArrowCursor)

    def load_image(self, file_path: str):
        self.scene.clear()
        self.current_pixmap_item = None
        self.hit_items = []
        self.active_hits = []
        self.zoom_factor = 1.0
        
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
        if self.current_pixmap_item and self.zoom_factor == 1.0:
            self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def mousePressEvent(self, event):
        if self.drawing_mode and event.button() == Qt.LeftButton:
            self.draw_start_point = self.mapToScene(event.pos())
            self.current_drawing_rect = QGraphicsRectItem()
            self.current_drawing_rect.setPen(QPen(QColor(255, 0, 0), 2, Qt.DashLine))
            self.current_drawing_rect.setBrush(QBrush(QColor(255, 0, 0, 30)))
            self.scene.addItem(self.current_drawing_rect)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.drawing_mode and self.draw_start_point and self.current_drawing_rect:
            current_point = self.mapToScene(event.pos())
            rect = QRectF(self.draw_start_point, current_point).normalized()
            self.current_drawing_rect.setRect(rect)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.drawing_mode and event.button() == Qt.LeftButton and self.current_drawing_rect:
            current_point = self.mapToScene(event.pos())
            rect = QRectF(self.draw_start_point, current_point).normalized()
            
            self.scene.removeItem(self.current_drawing_rect)
            self.current_drawing_rect = None
            self.draw_start_point = None
            
            if rect.width() > 5 and rect.height() > 5:
                # Constrain to image bounds
                if self.current_pixmap_item:
                    pixmap_rect = self.current_pixmap_item.boundingRect()
                    rect = rect.intersected(pixmap_rect)
                    
                if rect.width() > 0 and rect.height() > 0:
                    hit = SensitiveHit(
                        label="MANUAL",
                        text_content="",
                        confidence=1.0,
                        x=int(rect.x()),
                        y=int(rect.y()),
                        w=int(rect.width()),
                        h=int(rect.height())
                    )
                    self.active_hits.append(hit)
                    item = SelectableHitItem(hit, self.on_hit_toggled)
                    self.scene.addItem(item)
                    self.hit_items.append(item)
                    
                    if self.on_manual_hit_added:
                        self.on_manual_hit_added()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def zoom_in(self):
        self.scale(1.25, 1.25)
        self.zoom_factor *= 1.25

    def zoom_out(self):
        self.scale(1/1.25, 1/1.25)
        self.zoom_factor /= 1.25

    def reset_zoom(self):
        self.zoom_factor = 1.0
        if self.current_pixmap_item:
            self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)
