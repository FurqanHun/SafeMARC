from typing import List, Callable
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsPixmapItem, QGraphicsTextItem
from PySide6.QtGui import QPixmap, QPen, QColor, QBrush, QFont
from PySide6.QtCore import Qt, QRectF, QSettings

from src.core.types import SensitiveHit

class SelectableHitItem(QGraphicsRectItem):
    def __init__(self, hit: SensitiveHit, on_toggle: Callable, is_selected: bool = True):
        super().__init__(QRectF(hit.x, hit.y, hit.w, hit.h))
        self.hit = hit
        self.on_toggle = on_toggle
        self.is_selected = is_selected
        self.is_focused = False
        
        self.setAcceptHoverEvents(True)
        
        self.text_item = None
        if hit.identity:
            self.text_item = QGraphicsTextItem(hit.identity, self)
            self.text_item.setPos(hit.x, hit.y - 20)
            self.text_item.setDefaultTextColor(QColor("#10B981"))
            font = QFont("Segoe UI", 10, QFont.Bold)
            self.text_item.setFont(font)

        self.update_style()

    def update_style(self):
        settings = QSettings("SafeMARC", "SafeMARC")
        threshold = int(settings.value("model_text_conf", 70))
        is_low_conf_text = bool("FACE" not in self.hit.label and "BODY" not in self.hit.label and self.hit.confidence < threshold)
        
        if self.is_focused:
            # Highlight with a bright blue focus border
            color = QColor(59, 130, 246) # Bright blue `#3B82F6`
            self.setPen(QPen(color, 4, Qt.SolidLine))
            if self.is_selected:
                self.setBrush(QBrush(QColor(59, 130, 246, 70)))
            else:
                self.setBrush(QBrush(QColor(59, 130, 246, 25)))
            if self.text_item: self.text_item.setVisible(True)
            return

        if is_low_conf_text:
            # Low confidence "Review Suggested" hit -> Amber/Yellow color state
            color = QColor(245, 158, 11, 200) # Amber `#F59E0B`
            if self.is_selected:
                self.setPen(QPen(color, 3))
                self.setBrush(QBrush(QColor(245, 158, 11, 50)))
            else:
                self.setPen(QPen(color, 2, Qt.DashLine))
                self.setBrush(QBrush(QColor(245, 158, 11, 15)))
            if self.text_item: self.text_item.setVisible(self.is_selected)
        else:
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
from PySide6.QtCore import Qt, QRectF, Signal, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class LoadingOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.dots = 0
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        
        self.setStyleSheet("""
            QWidget {
                background: transparent;
            }
            QLabel {
                color: #10B981;
                font-weight: 600;
                font-size: 14px;
                font-family: 'Inter', 'Segoe UI', sans-serif;
                background: transparent;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)
        
        # Spacer for the custom drawn spinner (60px height)
        self.spinner_spacer = QWidget()
        self.spinner_spacer.setFixedSize(60, 60)
        self.spinner_spacer.setStyleSheet("background: transparent;")
        
        self.lbl_text = QLabel("Scanning document...")
        self.lbl_text.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.spinner_spacer, 0, Qt.AlignCenter)
        layout.addWidget(self.lbl_text)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(16) # ~60 FPS smooth rotation
        
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self.update_dots)
        self.pulse_timer.start(400)
        
    def update_dots(self):
        self.dots = (self.dots + 1) % 4
        base_text = self.lbl_text.text().rstrip(".")
        if "Scanning" in base_text:
            self.lbl_text.setText("Scanning" + "." * self.dots)
        elif "Processing" in base_text:
            self.lbl_text.setText("Processing" + "." * self.dots)

    def animate(self):
        self.angle = (self.angle + 6) % 360
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw translucent dark glassmorphism background
        painter.fillRect(self.rect(), QColor(11, 15, 25, 210))
        
        spacer_pos = self.spinner_spacer.mapTo(self, self.spinner_spacer.rect().topLeft())
        cx = spacer_pos.x() + 30
        cy = spacer_pos.y() + 30
        
        pen_track = QPen(QColor(55, 65, 81, 100), 4)
        painter.setPen(pen_track)
        painter.drawEllipse(cx - 20, cy - 20, 40, 40)
        
        pen_arc = QPen(QColor(16, 185, 129), 4)
        pen_arc.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_arc)
        
        painter.drawArc(cx - 20, cy - 20, 40, 40, -self.angle * 16, 270 * 16)


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
        self.overlay = None
        
        self.persistent_mode = False
        self.persistent_scope = "all_upcoming"
        self.persistent_pdf_source = None
        self.persistent_manual_hits = []

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
            
    def set_persistent_mode(self, enabled: bool, scope: str = "all_upcoming", pdf_source: str = None):
        self.persistent_mode = enabled
        self.persistent_scope = scope
        self.persistent_pdf_source = pdf_source
        if enabled:
            # Capture any current manual hits as persistent templates
            self.persistent_manual_hits = [h for h in self.active_hits if h.label == "MANUAL"]
        else:
            self.persistent_manual_hits = []

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

    def display_hits(self, hits: List[SensitiveHit], is_pdf: bool = False, pdf_source: str = None, cached_active_hits: list = None, reviewed: bool = False):
        settings = QSettings("SafeMARC", "SafeMARC")
        threshold = int(settings.value("model_text_conf", 70))
        
        def _hits_match(a, b):
            """Check if two hits refer to the same detection by coordinates and label."""
            return a.x == b.x and a.y == b.y and a.w == b.w and a.h == b.h and a.label == b.label
        
        if cached_active_hits is not None and reviewed:
            # Full review snapshot: restore user's exact checkbox state
            self.active_hits = []
            for hit in hits:
                if any(_hits_match(hit, ch) for ch in cached_active_hits):
                    self.active_hits.append(hit)
            # Inject cached manual hits that aren't in the new AI hits
            for ch in cached_active_hits:
                if ch.label == "MANUAL" and not any(_hits_match(ch, h) for h in hits):
                    hits.append(ch)
                    self.active_hits.append(ch)
        else:
            # Default or pre-review cache: use confidence filtering for AI hits
            self.active_hits = []
            for hit in hits:
                is_low_conf = bool("FACE" not in hit.label and "BODY" not in hit.label and hit.label != "MANUAL" and hit.confidence < threshold)
                if not is_low_conf:
                    self.active_hits.append(hit)
            # Inject any pre-review manual boxes from cache
            if cached_active_hits:
                for ch in cached_active_hits:
                    if ch.label == "MANUAL" and not any(_hits_match(ch, h) for h in hits):
                        hits.append(ch)
                        self.active_hits.append(ch)
        
        # Inject persistent manual hits if enabled and scope matches
        if self.persistent_mode:
            should_inject = False
            if is_pdf:
                if self.persistent_scope == "all_upcoming":
                    should_inject = True
                elif self.persistent_scope == "pdf_upcoming":
                    should_inject = True
                elif self.persistent_scope == "current_pdf_only":
                    if pdf_source == self.persistent_pdf_source:
                        should_inject = True
            else:
                if self.persistent_scope in ("all_upcoming", "image_upcoming"):
                    should_inject = True
                    
            if should_inject:
                for ph in self.persistent_manual_hits:
                    if not any(_hits_match(ph, h) for h in self.active_hits):
                        self.active_hits.append(ph)
        
        for item in self.hit_items:
            self.scene.removeItem(item)
        self.hit_items.clear()
        
        # Render ALL hits, marking as selected/checked only if they are in self.active_hits
        for hit in hits:
            is_sel = hit in self.active_hits
            item = SelectableHitItem(hit, self.on_hit_toggled, is_selected=is_sel)
            self.scene.addItem(item)
            self.hit_items.append(item)

    def on_hit_toggled(self, hit: SensitiveHit, is_selected: bool):
        if is_selected and hit not in self.active_hits:
            self.active_hits.append(hit)
            if self.persistent_mode and hit.label == "MANUAL" and hit not in self.persistent_manual_hits:
                self.persistent_manual_hits.append(hit)
        elif not is_selected and hit in self.active_hits:
            self.active_hits.remove(hit)
            if hit.label == "MANUAL" and hit in self.persistent_manual_hits:
                self.persistent_manual_hits.remove(hit)

    def get_selected_hits(self) -> List[SensitiveHit]:
        return self.active_hits

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.overlay is not None:
            self.overlay.resize(self.size())
        if self.current_pixmap_item and self.zoom_factor == 1.0:
            self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def show_loading(self, text: str = "Scanning document..."):
        if self.overlay is None:
            self.overlay = LoadingOverlay(self)
        self.overlay.lbl_text.setText(text)
        self.overlay.resize(self.size())
        self.overlay.show()

    def hide_loading(self):
        if self.overlay is not None:
            self.overlay.hide()

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
                    if self.persistent_mode:
                        self.persistent_manual_hits.append(hit)
                        
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

    def has_focused_hit(self) -> bool:
        return any(item.is_focused for item in self.hit_items)

    def focus_next_hit(self):
        if not self.hit_items:
            return
        
        curr_idx = -1
        for i, item in enumerate(self.hit_items):
            if item.is_focused:
                curr_idx = i
                item.is_focused = False
                item.update_style()
                break
                
        next_idx = (curr_idx + 1) % len(self.hit_items)
        self.hit_items[next_idx].is_focused = True
        self.hit_items[next_idx].update_style()
        self.ensureVisible(self.hit_items[next_idx])

    def focus_previous_hit(self):
        if not self.hit_items:
            return
            
        curr_idx = -1
        for i, item in enumerate(self.hit_items):
            if item.is_focused:
                curr_idx = i
                item.is_focused = False
                item.update_style()
                break
                
        prev_idx = (curr_idx - 1) % len(self.hit_items)
        self.hit_items[prev_idx].is_focused = True
        self.hit_items[prev_idx].update_style()
        self.ensureVisible(self.hit_items[prev_idx])

    def toggle_focused_hit(self):
        for item in self.hit_items:
            if item.is_focused:
                item.is_selected = not item.is_selected
                item.update_style()
                self.on_hit_toggled(item.hit, item.is_selected)
                break

    def clear_hit_focus(self):
        for item in self.hit_items:
            if item.is_focused:
                item.is_focused = False
                item.update_style()
