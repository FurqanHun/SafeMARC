# SafeMARC UML Class Architecture

This document contains a comprehensive UML class diagram detailing the properties, methods, and relationships between the core classes of the SafeMARC application.

> **Note**: For clarity, Qt GUI widgets (e.g. `btn_`, `lbl_`, `txt_`) have been explicitly filtered out of this diagram to highlight pure application state.

## Core & Detection Layer

```mermaid
classDiagram
    direction TB
    
    class BaseDetector {
        <<abstract>>
        +detect(image_path: str)* List~SensitiveHit~
    }
    
    class VisionDetector {
        +str mode
        +IdentityManager identity_manager
        +local _local
        +ObjectDetector detector
        +detect(image_path: str, match_identities: bool) List~SensitiveHit~
        +cleanup() void
        -_reclaim_if_needed() void
        -_detect_faces(cv_image: ndarray, match_identities: bool, face_thresh: float) List~SensitiveHit~
        -_detect_bodies(cv_image: ndarray, match_identities: bool) List~SensitiveHit~
        -_depth_clip_bodies(hits: List~SensitiveHit~) List~SensitiveHit~
        -_get_yunet(w: int, h: int, thresh: float) FaceDetectorYN
        -_get_yunet_small(w: int, h: int, thresh: float) FaceDetectorYN
        -_multi_scale_detect(cv_image: ndarray, w_img: int, h_img: int, face_thresh: float) list
        -_nms(detections: list, iou_thresh: float, use_iou: bool) list
        -_yunet_model_path
        -_active_bd_val
    }
    
    class RegexDetector {
        +List custom_patterns
        +str cached_image_path
        +clear_custom_patterns() void
        +add_custom_pattern(label: str, pattern: str, is_regex: bool, is_whole_word: bool, keywords: List) void
        +detect(file_path: str, pdf_words: list) List~SensitiveHit~
        -_scan_data_dict(data: dict, scale: float) List~SensitiveHit~
        +_load_cache() void
        +save_cache() void
        +ocr_cache
    }
    
    class SafeScanner {
        +IdentityManager identity_manager
        +VisionDetector vision_detector
        +RegexDetector text_detector
        +List detectors
        +Redactor redactor
        +str face_redaction_mode
        +List target_identities
        +Dict _vision_cache
        +Dict _regex_cache
        +Dict _scan_cache
        +clear_cache() void
        +clear_scan_cache_only() void
        +clear_text_cache() void
        +clear_vision_cache() void
        +set_vision_mode(mode: str) void
        +set_face_redaction_mode(mode: str) void
        +set_text_patterns(patterns_list: List) void
        +scan(file_path: str, pdf_words: list, cache_key: str) List~SensitiveHit~
        +redact(file_path: str, output_path: str, hits: List~SensitiveHit~) bool
        +cleanup() void
    }

    class Redactor {
        +apply(input_path: str, output_path: str, hits: List~SensitiveHit~) bool
    }

    class SensitiveHit {
        +int x
        +int y
        +int w
        +int h
        +str label
        +float confidence
        +str text_content
        +str identity
    }

    class IdentityManager {
        +str identities_dir
        +str session_temp
        +local _local
        +FaceRecognizerSF sface_recognizer
        +LBPHFaceRecognizer recognizer
        +bool use_sface
        +Dict identity_map
        +Dict sface_embeddings
        +bool is_trained
        +reload_identities() void
        +match_face(face_image: ndarray) Optional~str~
        +match_face_aligned(full_img: ndarray, det_row: ndarray, num_faces: int) Optional~str~
        +add_identity(name: str, image_paths: List~str~) void
        +add_session_identity(name: str, image_path: str) void
        -_extract_face_crop(img: ndarray) ndarray
        -_build_aligned_embedding(img: ndarray) ndarray
        -_rank_sface_embedding(embedding: ndarray, num_faces: int) Optional~str~
        -_match_sface_from_aligned(aligned_face: ndarray, num_faces: int) Optional~str~
        -_match_sface(face_image: ndarray) Optional~str~
        -_match_lbph(face_image: ndarray) Optional~str~
        +_get_sface_recognizer() void
        +sface_model
    }

    BaseDetector <|-- VisionDetector
    BaseDetector <|-- RegexDetector
    SafeScanner *-- VisionDetector
    SafeScanner *-- RegexDetector
    SafeScanner *-- Redactor
    SafeScanner *-- IdentityManager
    VisionDetector --> IdentityManager : uses for face matching
    SafeScanner ..> SensitiveHit : produces
```

---

## Processing & Handler Layer

```mermaid
classDiagram
    direction TB

    class BatchProcessor {
        +SafeScanner scanner
        +_get_supported_files(input_path: str) List~str~
        +get_output_path(input_path: str, output_dir: str, use_suffix: bool) str
        +process(input_path: str, output_dir: str, use_suffix: bool) Generator
    }

    class PDFHandler {
        <<static>>
        +extract_pages(pdf_path: str, progress_callback: Optional~callable~) List~dict~
        +extract_first_page(pdf_path: str) Optional~str~
        +build_pdf(image_paths: List~str~, output_pdf_path: str, page_sizes: Optional~List~Tuple~float, float~~~~) bool
    }

    class PDFExtractWorker {
        +Signal progress
        +Signal finished
        +Signal error
        +str file_path
        +run() void
    }

        class PDFOCRWorker {
        +Signal finished
        +SafeScanner scanner
        +List pages
        +str pdf_source
        +bool is_cancelled
        +run() void
        +cancel() void
    }

    class PDFFinalizeWorker {
        +Signal progress
        +Signal finished
        +Signal error
        +SafeScanner scanner
        +List original_pages
        +Dict cache
        +str active_pdf_source
        +str out_path
        +run() void
    }

    class LoadingDialog {
        +update_progress(current: int, total: int) void
        +QLabel label
        +QProgressBar progress_bar
    }
```

---

## UI Layer (PySide6 Desktop Application)

```mermaid
classDiagram
    direction TB

    class SafeMARCMainWindow {
        +SafeScanner scanner
        +BatchProcessor processor
        +PreviewWidget preview_widget
        +QListWidget file_list
        +Dict active_regions
        +Dict user_selections_cache
        +Dict shortcuts_config
        +str active_pdf_source
        +int active_pdf_index
        +QFrame pdf_nav_container
        +QSpinBox pdf_page_spin
        +QLabel pdf_total_label
        +List active_pdf_pages
        +List active_pdf_outputs
        +bool active_pdf_has_redactions
        +bool is_navigating_backward
        +PDFExtractWorker _pdf_extract_worker
        +PDFFinalizeWorker _pdf_finalize_worker
        +start_batch() void
        +redact_current() void
        +skip_current() void
        +go_previous() void
        +load_next_batch_item() void
        +reclaim_memory() void
        +add_files() void
        +add_folder() void
        +add_dropped_paths(paths: List) void
        +update_shortcut_key(action_name: str, new_sequence: str) void
        +import_custom_patterns() void
        +export_custom_patterns() void
        -_update_face_mode(text: str) void
        -_show_people_selector() void
        -_show_regions_selector() void
        -_toggle_target_identity(name: str, checked: bool) void
        -_toggle_active_region(name: str, checked: bool) void
        +on_manual_rescan() void
        -_rescan_current() void
        -_on_pdf_page_changed(value: int) void
        -_finalize_pdf_redaction() void
        +on_quick_add_identity(hit: SensitiveHit) void
        +toggle_persistent_mode(checked: bool) void
        +cleanup_temp_resources(full: bool) void
        +toggle_draw_mode() void
        +update_toolbar_state() void
        +cancel_batch_mode() void
        +cancel_active_pdf_ocr_worker() void
        +_is_input_focused() void
        +update_review_button_tooltips() void
        +set_shortcuts_enabled() void
        +on_return_pressed() void
        +on_escape_pressed() void
        +open_settings() void
        +add_pattern_row() void
        +remove_pattern_row() void
        +focus_last_pattern_field() void
        +_filter_queue_list() void
        +_filter_text_patterns() void
        +update_text_patterns() void
        +on_vision_mode_changed() void
        +_clear_target_identities() void
        +dragEnterEvent() void
        +dropEvent() void
        +is_path_in_list() void
        +remove_selected_file() void
        +clear_queue() void
        +on_paste() void
        +on_file_selected() void
        +get_current_cache_key() void
        +get_redacted_output_path() void
        +run_scan_with_overlay() void
        +_undo_queue_item() void
        +update_stats() void
        +closeEvent() void
        +showEvent() void
        -_apply_default_splitter_sizes() void
        -_on_shortcut_draw() void
        -_on_shortcut_persistent() void
        -_on_shortcut_zoom_in() void
        -_on_shortcut_zoom_out() void
        -_on_shortcut_zoom_reset() void
        -_on_shortcut_rescan() void
        -_on_shortcut_start_redact() void
        -_on_shortcut_skip_space() void
        -_on_shortcut_skip_s() void
        -_on_shortcut_previous() void
        -_on_shortcut_escape() void
        -_on_shortcut_hit_next() void
        -_on_shortcut_hit_prev() void
        -_on_shortcut_hit_toggle() void
        -_on_shortcut_add_file() void
        -_on_shortcut_add_folder() void
        -_on_shortcut_remove_file() void
        -_on_shortcut_settings() void
        -_on_shortcut_clear_queue() void
        -_on_shortcut_paste() void
        -_on_shortcut_reset_layout() void
        -_show_engine_status_popup() void
        +splitter
        +is_batch_mode
        +active_pdf_ocr_worker
        +text_patterns_layout
        +focus_filter
        +current_file_path
        +settings
        +batch_success_count
        +batch_index
        +current_hits
        +ClickableStatusLabel status_label
    }

    class PreviewWidget {
        +Signal identityRequested
        +QGraphicsScene scene
        +QGraphicsPixmapItem current_pixmap_item
        +List hit_items
        +List active_hits
        +bool drawing_mode
        +QPointF draw_start_point
        +QGraphicsRectItem current_drawing_rect
        +callable on_manual_hit_added
        +float zoom_factor
        +LoadingOverlay overlay
        +bool persistent_mode
        +str persistent_scope
        +str persistent_pdf_source
        +List persistent_manual_hits
        +display_hits(hits: List~SensitiveHit~, is_pdf: bool, pdf_source: str, cached_active_hits: list, reviewed: bool) void
        +get_selected_hits() List~SensitiveHit~
        +set_drawing_mode(enabled: bool) void
        +set_persistent_mode(enabled: bool, scope: str, pdf_source: str) void
        +clear_preview() void
        +load_image(file_path: str) void
        +zoom_in() void
        +zoom_out() void
        +reset_zoom() void
        +on_add_identity_requested(hit: SensitiveHit) void
        +has_focused_hit() bool
        +focus_next_hit() void
        +focus_previous_hit() void
        +toggle_focused_hit() void
        +clear_hit_focus() void
        +show_loading(text: str) void
        +hide_loading() void
        +on_hit_toggled() void
        +resizeEvent() void
        +wheelEvent() void
        +mousePressEvent() void
        +mouseMoveEvent() void
        +mouseReleaseEvent() void
    }

    class SelectableHitItem {
        +SensitiveHit hit
        +bool is_selected
        +bool is_focused
        +QGraphicsTextItem text_item
        +callable on_toggle
        +update_style() void
        +mousePressEvent(event) void
        +contextMenuEvent(event) void
    }

    class SettingsDialog {
        +SafeScanner scanner
        +IdentityManager identity_manager
        +Dict local_shortcuts
        -_init_shortcuts_tab() void
        -_check_for_conflicts() void
        -_on_shortcut_changed(key: str, seq: str) void
        -_on_shortcut_reset(key: str, default_seq: str) void
        -_reset_all_shortcuts() void
        -_import_identities() void
        -_export_identities() void
        -_add_person() void
        -_del_person() void
        -_rename_person(item: QListWidgetItem) void
        -_add_image() void
        -_trigger_identity_shortcut(callback) void
        -_refresh_people_list() void
        -_filter_people_list(text: str) void
        -_on_selection_changed() void
        -_clear_grid() void
        -_load_person_images(name: str, is_session: bool) void
        -_on_global_output_toggled(checked: bool) void
        -_browse_global_dir() void
        -_update_logging_preferences() void
        -_delete_individual_image(img_path: str, person_name: str, is_session: bool) void
        +settings
        +tabs
    }

    class ShortcutRebindButton {
        +Signal keySequenceChanged
        +str current_sequence
        +bool is_listening
        +update_style() void
        +keyPressEvent(event) void
        +focusOutEvent(event) void
        -_on_clicked() void
    }

    class PersistentRangeDialog {
        +get_selected_scope() str
    }

    class FocusEventFilter {
        +eventFilter(obj: QObject, event: QEvent) bool
        +main_window
    }

    class ClickableStatusLabel {
        +Signal clicked
        +mousePressEvent(event) void
    }

    class EngineStatusDialog {

    }

    class QuickAddIdentityDialog {
        +QComboBox combo_name
        +get_name() str
        -_on_save() void
    }

    class LoadingOverlay {
        +QWidget spinner_spacer
        +QTimer timer
        +QTimer pulse_timer
        +int angle
        +int dots
        +update_dots() void
        +animate() void
        +paintEvent(event) void
    }

    class InteractiveCropLabel {
        +QRect crop_rect
        +bool is_dragging
        +bool is_resizing
        +QPoint drag_start
        +int resize_handle
        +set_crop_rect(rect: QRect) void
        +get_crop_rect() QRect
        +paintEvent(event) void
        +mousePressEvent(event) void
        +mouseMoveEvent(event) void
        +mouseReleaseEvent(event) void
        -_get_handle_at() void
    }

    class FaceCropDialog {
        +InteractiveCropLabel crop_label
        -_load_and_detect() void
        -_on_confirm() void
        +workspace_card
        +raw_image_path
        +cropped_image
        +raw_img
        +scale_factor
    }

    class NewIdentityDialog {
        +get_name() str
        -_on_save() void
    }

    class PatternLineEdit {
        +bool is_regex
        +SafeMARCMainWindow parent_window
        +keyPressEvent(event) void
    }

    class ScanWorker {
        +Signal finished
        +Signal error
        +SafeScanner scanner
        +str file_path
        +List pdf_words
        +str cache_key
        +List hits
        +run() void
    }

    SafeMARCMainWindow *-- PreviewWidget
    SafeMARCMainWindow *-- ClickableStatusLabel
    SafeMARCMainWindow *-- PatternLineEdit
    SafeMARCMainWindow *-- PDFExtractWorker : manages
    SafeMARCMainWindow *-- PDFFinalizeWorker : manages
    SafeMARCMainWindow *-- PDFOCRWorker : manages
    SafeMARCMainWindow *-- ScanWorker : manages
    SafeMARCMainWindow ..> SettingsDialog : opens
    SafeMARCMainWindow ..> PersistentRangeDialog : opens
    SafeMARCMainWindow ..> EngineStatusDialog : opens
    SafeMARCMainWindow ..> QuickAddIdentityDialog : opens
    SafeMARCMainWindow ..> LoadingDialog : opens
    PreviewWidget *-- SelectableHitItem
    PreviewWidget *-- LoadingOverlay
    PreviewWidget ..> SafeMARCMainWindow : identityRequested signal
    SettingsDialog ..> FaceCropDialog : opens
    SettingsDialog ..> NewIdentityDialog : opens
    FaceCropDialog *-- InteractiveCropLabel
    FocusEventFilter ..> SafeMARCMainWindow : filters focus events for
```
