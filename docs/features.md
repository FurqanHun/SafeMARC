# SafeMARC Features

## Core Vision Features
- [x] **Face Detection**: Fast & accurate face scanning via Haar Cascade (OpenCV).
  - *Pose & Occlusion Robustness*: Employs a multi-cascade ensemble (frontal, alt-frontal, and side-profile) with horizontal profile-flipping, and Union-Based Bounding Box Merging (Union-NMS) to seamlessly capture tilted, rotated, posed, and partially covered faces.
- [x] **Face Recognition**: Deep learning identity matching via SFace (OpenCV DNN) with LBPH fallback.
  - *Ensemble Auto-Cropping*: Reference images are auto-cropped using the high-recall ensemble face detector to guarantee high-precision biometric registration even for tilted or posed reference photos.
- [x] **Body Detection**: Robust human body and silhouette detection.
  - *EfficientDet-Lite2 (TFLite)*: Leverages MediaPipe Object Detector with a lightweight, high-performance `efficientdet_lite2.tflite` model to detect full bodies and silhouettes with low latency.
- [x] **Text Only Mode**: Ability to disable image/face scanning to focus strictly on text redactions.
- [x] **Redact All**: Auto-redact all detected faces in a document.
- [x] **Whitelist Mode**: Redact all faces except those matching specific approved identities.
- [x] **Blacklist Mode**: Specifically redact only matched sensitive identities.

## Text Redaction
- [x] **Smart PDF Text Extraction & OCR Fallback**: Leverages native PDF digital text via PyMuPDF for perfect accuracy, with a highly optimized Tesseract OCR fallback (OpenCV binarization and 2x upscaling) for scanned documents.
- [ ] **Predefined Patterns**: Pre-configured rules for Common entities (Phone Numbers, CNICs/IDs, Credit Cards). (Planned/Partial)
- [x] **Custom Text & Regex Redaction**: User can add multiple custom strings or complex Regular Expressions to redact sensitive text lines.

## Document Support & Handling
- [x] **Images**: Comprehensive support for modern image formats (JPG, JPEG, PNG, WEBP).
- [x] **PDFs**: Seamless PDF page extraction, individual page review, and rasterized rebuilding to completely eliminate any hidden layers and metadata.
- [ ] **Word Documents (`.docx`)**: Planned for future releases.

## Non-Destructive Review Workflow
- [x] **Manual Toggle**: Intersected regions/boxes can be untoggled before saving.
- [x] **Manual Draw Tool**: Ability to toggle "Draw Box" mode (with a button or the `D` keyboard shortcut) to draw custom redaction rectangles.
- [ ] **Persistent Draw Tool**: Persistent manual redaction boxes across the entire queue or specific PDF pages for repeating layouts. (Planned)
- [x] **Auto-Skip Clean Images**: Configurable feature to bypass images with no detected sensitive hits for a faster review.
- [x] **Skip Review Mode**: Configurable checkbox toggle to run fully automated review and redaction across all items.
- [x] **Stop Review**: Option to exit the active batch review process without clearing the queue.
- [x] **Queue Management**: Direct queue manipulation allowing users to remove any individual file before/during review.
- [x] **Drag and Drop**: Support dragging and dropping files or folders directly into the queue list widget.
- [x] **Clipboard Integration**: Support pasting images (`Ctrl+V`) directly from the clipboard to auto-generate a temporary review item.
- [x] **Global Output Folder & Clipboard Safety**: Configuration to specify a custom global folder for all redactions. Clipboard-pasted files automatically redirect here to prevent loss in system temporary directories.
- [x] **Backwards Navigation**: Full navigation history to step backward to a previous file or PDF page.

## Biometric Identity Editor
- [x] **Interactive 1:1 Aspect-Ratio Crop Editor**: Crop uploaded reference faces with a locked 1:1 aspect ratio, interactive resize handles, transparent helper labels, and automatic face detection fallback.
- [x] **Individual Reference Image Removal**: Delete specific reference images via interactive red corner corner close markers on thumbnails, triggering immediate `.npy` cache cleanups.
- [x] **Extended Multi-Selection**: Select and batch-delete multiple identities at once using standard keyboard hotkeys (Ctrl+Click, Shift+Click, or Drag).

## System & Interface
- [x] **Interactive GUI**: Sleek modern interface built using PySide6.
- [ ] **Premium UI/UX Polish**: Premium unified deep-dark `#0B0F19` canvas, custom `NewIdentityDialog` with matching aesthetics, global transparent labels, and tactile `PointingHandCursor` feedback on all interactive components (buttons, checkboxes, comboboxes, menus, and list items). This is an ongoing process.
- [ ] **Keyboard-Driven Workflow**: Expanded keyboard shortcuts for quick queue actions (`Ctrl+O`, `Ctrl+Shift+O`, `Delete`), navigating review loops (`Return`, `Backspace`), and toggling Draw Mode (`D`). (Ongoing)
- [ ] **Rebindable Shortcuts Settings**: Settings panel to allow users to fully customize and rebind keys (Planned).
- [ ] **CLI Interface**: Command-line batch processing with ArgumentParser. (Planned/Partial), It's half baked rn.
- [x] **Cross-Platform Compatibility**: Fully safe and optimized file path handling across Linux and Windows.
- [x] **Graceful Shutdown**: Instant and clean `Ctrl+C` signal handling in the GUI.

For more information, please check `requirements.txt`.