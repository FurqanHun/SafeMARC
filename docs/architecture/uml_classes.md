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
        +detect(image_path: str) List~SensitiveHit~
    }
    
    class RegexDetector {
        +List custom_patterns
        +clear_custom_patterns() void
        +add_custom_pattern(label: str, pattern: str, is_regex: bool, is_whole_word: bool) void
        +detect(file_path: str, pdf_words: list) List~SensitiveHit~
    }
    
    class SafeScanner {
        +VisionDetector vision_detector
        +RegexDetector text_detector
        +Redactor redactor
        +set_vision_mode(mode: str) void
        +set_text_patterns(patterns_list: List) void
        +scan(file_path: str, pdf_words: list) List~SensitiveHit~
        +redact(file_path: str, output_path: str, hits: List~SensitiveHit~) bool
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
    }

    BaseDetector <|-- VisionDetector
    BaseDetector <|-- RegexDetector
    SafeScanner *-- VisionDetector
    SafeScanner *-- RegexDetector
    SafeScanner *-- Redactor
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
        +QCheckBox chk_always_rasterize
        +QCheckBox chk_skip_review
        +start_batch() void
        +redact_current() void
        +skip_current() void
        +go_previous() void
        +load_next_batch_item() void
    }

    class PreviewWidget {
        +display_hits(hits: List~SensitiveHit~) void
        +get_selected_hits() List~SensitiveHit~
        +toggle_draw_mode() void
        +zoom_in() void
        +zoom_out() void
        +reset_zoom() void
    }

    class SettingsDialog {
        +accept() void
    }

    SafeMARCMainWindow *-- PreviewWidget
    SafeMARCMainWindow ..> SettingsDialog : opens
```
