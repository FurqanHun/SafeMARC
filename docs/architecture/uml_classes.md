# SafeMARC UML Class Architecture

This document contains a comprehensive UML class diagram detailing the properties, methods, and relationships between the core classes of the SafeMARC application.

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
        +CascadeClassifier face_cascade
        +CascadeClassifier face_cascade_alt
        +CascadeClassifier profile_cascade
        +ObjectDetector detector
        +detect(image_path: str, match_identities: bool) List~SensitiveHit~
        +cleanup() void
    }
    
    class RegexDetector {
        +List custom_patterns
        +str cached_image_path
        +List cached_pdf_words
        +List cached_data_list
        +clear_custom_patterns() void
        +add_custom_pattern(label: str, pattern: str, is_regex: bool, is_whole_word: bool, keywords: List) void
        +detect(file_path: str, pdf_words: list) List~SensitiveHit~
        -_scan_data_dict(data: dict, scale: float) List~SensitiveHit~
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
        +Dict _scan_cache
        +clear_cache() void
        +set_vision_mode(mode: str) void
        +set_face_redaction_mode(mode: str) void
        +set_text_patterns(patterns_list: List) void
        +scan(file_path: str, pdf_words: list, cache_key: str) List~SensitiveHit~
        +redact(file_path: str, output_path: str, hits: List~SensitiveHit~) bool
        +cleanup() void
    }

    class Redactor {
        +apply(file_path: str, output_path: str, hits: List~SensitiveHit~) bool
        -_redact_image(image_path: str, output_path: str, hits: List~SensitiveHit~) bool
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
        +CascadeClassifier face_cascade
        +CascadeClassifier face_cascade_alt
        +CascadeClassifier profile_cascade
        +FaceRecognizerSF sface_recognizer
        +LBPHFaceRecognizer recognizer
        +bool use_sface
        +Dict identity_map
        +Dict sface_embeddings
        +bool is_trained
        +reload_identities() void
        +match_face(face_image: ndarray) Optional~str~
        +add_identity(name: str, image_paths: List~str~) void
        +add_session_identity(name: str, image_path: str) void
        -_extract_face_crop(img: ndarray) ndarray
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
        +extract_pages(pdf_path: str) List~dict~
        +extract_first_page(pdf_path: str) str
        +build_pdf(page_image_paths: List~str~, out_path: str) bool
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
        +QComboBox cmb_face_mode
        +QLabel lbl_count
        +Dict active_regions
        +Dict user_selections_cache
        +Dict shortcuts_config
        +str active_pdf_source
        +int active_pdf_index
        +bool is_navigating_backward
        +QShortcut shortcut_rescan
        +start_batch() void
        +redact_current() void
        +skip_current() void
        +go_previous() void
        +load_next_batch_item() void
        +add_files() void
        +add_folder() void
        +add_dropped_paths(paths: List) void
        +update_shortcut_key(action_name: str, new_sequence: str) void
        -_update_face_mode(text: str) void
        -_show_people_selector() void
        -_show_regions_selector() void
        -_toggle_target_identity(name: str, checked: bool) void
        -_toggle_active_region(name: str, checked: bool) void
        -_rescan_current() void
        +on_quick_add_identity(hit: SensitiveHit) void
        +toggle_persistent_mode(checked: bool) void
        +cleanup_temp_resources(full: bool) void
        +handle_sigint(signum, frame) void
    }

    class PreviewWidget {
        +Signal identityRequested
        +display_hits(hits: List~SensitiveHit~, is_pdf: bool, pdf_source: str, cached_active_hits: list, reviewed: bool) void
        +get_selected_hits() List~SensitiveHit~
        +toggle_draw_mode() void
        +zoom_in() void
        +zoom_out() void
        +reset_zoom() void
        +on_add_identity_requested(hit: SensitiveHit) void
        +set_persistent_mode(enabled: bool, scope: str, pdf_source: str) void
    }

    class SelectableHitItem {
        +SensitiveHit hit
        +bool is_selected
        +QGraphicsTextItem text_item
        +update_style() void
        +contextMenuEvent(event) void
    }

    class SettingsDialog {
        +SafeScanner scanner
        +IdentityManager identity_manager
        +Dict shortcut_buttons
        +accept() void
        -_init_shortcuts_tab() void
        -_check_for_conflicts() void
        -_on_shortcut_changed(key: str, seq: str) void
        -_on_shortcut_reset(key: str, default_seq: str) void
        -_reset_all_shortcuts() void
    }

    class ShortcutRebindButton {
        +Signal keySequenceChanged
        +str current_sequence
        +bool is_listening
        +update_style() void
        +keyPressEvent(event) void
        +focusOutEvent(event) void
    }

    class PersistentRangeDialog {
        +bool is_pdf
        +get_selected_scope() str
    }

    class KeyboardFocusFilter {
        +eventFilter(obj: QObject, event: QEvent) bool
    }

    SafeMARCMainWindow *-- PreviewWidget
    SafeMARCMainWindow ..> SettingsDialog : opens
    SafeMARCMainWindow ..> PersistentRangeDialog : opens
    PreviewWidget *-- SelectableHitItem
    PreviewWidget ..> SafeMARCMainWindow : identityRequested signal
    KeyboardFocusFilter ..> SafeMARCMainWindow : filters focus events for
```
