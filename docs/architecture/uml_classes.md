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
        +detect(image_path: str, match_identities: bool) List~SensitiveHit~
        +cleanup() void
    }
    
    class RegexDetector {
        +List custom_patterns
        +clear_custom_patterns() void
        +add_custom_pattern(label: str, pattern: str, is_regex: bool, is_whole_word: bool) void
        +detect(file_path: str, pdf_words: list) List~SensitiveHit~
    }
    
    class SafeScanner {
        +IdentityManager identity_manager
        +VisionDetector vision_detector
        +RegexDetector text_detector
        +Redactor redactor
        +str face_redaction_mode
        +List target_identities
        +set_vision_mode(mode: str) void
        +set_face_redaction_mode(mode: str) void
        +set_text_patterns(patterns_list: List) void
        +scan(file_path: str, pdf_words: list) List~SensitiveHit~
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
        +FaceRecognizerSF sface_recognizer
        +bool use_sface
        +Dict identity_map
        +Dict sface_embeddings
        +bool is_trained
        +reload_identities() void
        +match_face(face_image: ndarray) Optional~str~
        +add_identity(name: str, image_paths: List~str~) void
        +add_session_identity(name: str, image_path: str) void
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
        +start_batch() void
        +redact_current() void
        +skip_current() void
        +go_previous() void
        +load_next_batch_item() void
        +add_files() void
        +add_folder() void
        +add_dropped_paths(paths: List) void
        -_update_face_mode(text: str) void
        -_show_people_selector() void
        -_toggle_target_identity(name: str, checked: bool) void
        -_rescan_current() void
        +on_quick_add_identity(hit: SensitiveHit) void
        +toggle_persistent_mode(checked: bool) void
    }

    class PreviewWidget {
        +Signal identityRequested
        +display_hits(hits: List~SensitiveHit~, is_pdf: bool, pdf_source: str) void
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
        +accept() void
    }

    class PersistentRangeDialog {
        +bool is_pdf
        +get_selected_scope() str
    }

    SafeMARCMainWindow *-- PreviewWidget
    SafeMARCMainWindow ..> SettingsDialog : opens
    SafeMARCMainWindow ..> PersistentRangeDialog : opens
    PreviewWidget *-- SelectableHitItem
    PreviewWidget ..> SafeMARCMainWindow : identityRequested signal
```
