# SafeMARC Features

## Core Vision Features
- [x] **Face Detection**: Fast & accurate face scanning via Mediapipe/TensorFlow Lite.
- [x] **Redact All**: Auto-redact all detected faces in a document.
- [ ] **Whitelist Mode**: Redact all faces except those matching specific approved identities. (Planned)
- [ ] **Blacklist Mode**: Specifically redact only matched sensitive identities. (Planned)

## Text Redaction
- [ ] **Predefined Patterns**: Pre-configured rules for Common entities (Phone Numbers, CNICs/IDs, Credit Cards). (Planned/Partial)
- [x] **Custom Text & Regex Redaction**: User can add multiple custom strings or complex Regular Expressions to redact sensitive text lines.

## Document Support & Handling
- [x] **Images**: Comprehensive support for modern image formats (JPG, JPEG, PNG, WEBP).
- [x] **PDFs**: Seamless PDF page extraction, individual page review, and rasterized rebuilding to completely eliminate any hidden layers and metadata.
- [ ] **Word Documents (`.docx`)**: Planned for future releases.

## Non-Destructive Review Workflow
- [x] **Manual Toggle**: Intersected regions/boxes can be untoggled before saving.
- [x] **Manual Draw Tool**: Ability to toggle "Draw Box" mode (with a button or the `D` keyboard shortcut) to draw custom redaction rectangles.
- [x] **Auto-Skip Clean Images**: Configurable feature to bypass images with no detected sensitive hits for a faster review.
- [x] **Queue Management**: Direct queue manipulation allowing users to remove any individual file before/during review.
- [x] **Backwards Navigation**: Full navigation history to step backward to a previous file or PDF page.

## System & Interface
- [x] **Interactive GUI**: Sleek modern interface built using PySide6.
- [ ] **UI/UX Polish**: High-fidelity UI styling and enhanced layouts (Planned).
- [x] **CLI Interface**: Command-line batch processing with ArgumentParser.
- [x] **Cross-Platform Compatibility**: Fully safe and optimized file path handling across Linux and Windows.
- [x] **Graceful Shutdown**: Instant and clean `Ctrl+C` signal handling in the GUI.

For more information, please check `requirements.txt`.