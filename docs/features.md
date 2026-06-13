# SafeMARC Features

## Performance & Architecture
- [x] **Zero-Lag Session Caching**: An advanced memory dictionary cache that saves full biometric and text hits per file/page, ensuring backwards and forwards queue navigation is instantaneous (<10ms latency).
- [x] **Stable PDF Cache Keys**: Maps randomized temporary PDF extraction paths to stable document/page keys to perfectly track PDF hits inside the zero-lag session cache.
- [x] **Unified Resource Pooling**: All temporary files (PDF pages, cropped identities, clipboard images, and redacted assets) are securely managed inside a single system-level `safemarc_temp` directory to prevent workspace clutter and bypass Windows permission issues.
- [x] **Graceful RAII Loop Guard**: PySide6 event loops are protected with a custom `SIGINT` signal handler and a `try-finally` Python RAII guard. This guarantees that `safemarc_temp` is securely and completely purged even if the application is killed forcefully with `Ctrl+C`.

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
- [x] **Predefined & Dynamic Regional Patterns**: Pre-configured rules for common entities grouped by country regions. The user can toggle these regions via the UI, instantly re-evaluating matches:
  - **Global**: Credit Card numbers (Visa, Mastercard, Amex, etc.), Email Addresses, IPv4 Addresses, Names (with title prefixes e.g. Mr, Dr, Mrs), and Street Locations/Addresses.
  - **Pakistan**: National Identity Card (CNIC), Phone Numbers, Passports, Driving Licenses, and Vehicle Registration Plates.
  - **United States**: Social Security Numbers (SSN), Phone Numbers, Zip Codes, and Driver's Licenses.
  - **European Union**: IBAN Bank Account numbers, VAT Registration Numbers.
  - **India**: Aadhaar Card numbers, Phone Numbers, PAN Card numbers, and Driving Licenses.
  - **United Kingdom**: National Insurance Numbers (NINO), Phone Numbers.
- [x] **Algorithmic Verification & Mod-97 Checksum**: Employs mathematical structural validation (e.g. ISO 7064 mod-97 checksum checks for IBAN accounts) to immediately discard invalid OCR text matches.
- [x] **Context Proximity & Review Suggested State**: Matches found near context keywords are boosted to 90% or 95% confidence. Isolated ambiguous matches (like Zip Codes, IPs) default to 30% confidence, while high-value targets (SSN, Aadhaar) lacking surrounding context keywords drop to 25% confidence, keeping them review-suggested and hidden from automatic selection by default.
- [x] **Custom Pattern Import/Export**: User can add multiple custom strings or complex Regular Expressions to redact sensitive text lines, with seamless serialization/deserialization to `.json` files.
  * **Example Custom Pattern JSON Format**:
    ```json
    [
        {
            "label": "REGEX",
            "pattern": "\\b\\d{3}-\\d{2}-\\d{4}\\b",
            "is_regex": true,
            "whole_word": false
        },
        {
            "label": "TEXT",
            "pattern": "Confidential",
            "is_regex": false,
            "whole_word": true
        }
    ]
    ```
- [x] **Area-Overlap (IoU) Deduplication**: Mathematically robust Intersection-over-Union bounding box merging that consolidates redundant/overlapping native PDF text and Tesseract OCR hits, keeping the highest confidence match.

## Document Support & Handling
- [x] **Images**: Comprehensive support for modern image formats (JPG, JPEG, PNG, WEBP).
- [x] **PDFs**: Seamless PDF page extraction, individual page review, and rasterized rebuilding to completely eliminate any hidden layers and metadata.
- [ ] **Word Documents (`.docx`)**: Planned for future releases.

## Non-Destructive Review Workflow
- [x] **Manual Toggle**: Intersected regions/boxes can be untoggled before saving.
- [x] **Manual Draw Tool**: Ability to toggle "Draw Box" mode (with a button or the `D` keyboard shortcut) to draw custom redaction rectangles.
- [x] **Persistent Draw Tool**: Persistent manual redaction boxes across the entire queue or specific PDF pages for repeating layouts (toggled via the premium "Persistent Boxes" pin button).
- [x] **Auto-Skip Clean Images**: Configurable feature to bypass images with no detected sensitive hits for a faster review.
- [x] **Skip Review Mode**: Configurable checkbox toggle to run fully automated review and redaction across all items.
- [x] **Stop Review**: Option to exit the active batch review process without clearing the queue.
- [x] **Queue Management**: Direct queue manipulation allowing users to remove any individual file before/during review.
- [x] **Drag and Drop**: Support dragging and dropping files or folders directly into the queue list widget.
- [x] **Clipboard Integration**: Support pasting images (`Ctrl+V`) directly from the clipboard to auto-generate a temporary review item.
- [x] **Global Output Folder & Clipboard Safety**: Configuration to specify a custom global folder for all redactions. Clipboard-pasted files automatically redirect here to prevent loss in system temporary directories.
- [x] **Backwards Navigation**: Full navigation history to step backward to a previous file or PDF page.
- [x] **State Selections & Checkbox Persistence**: Keeps the exact checked/unchecked state of all AI detections and manually added bounding boxes perfectly synchronized and persistent across queue navigation (back, next, skip) and settings/pattern rescans.

## Biometric Identity Editor
- [x] **Interactive 1:1 Aspect-Ratio Crop Editor**: Crop uploaded reference faces with a locked 1:1 aspect ratio, interactive resize handles, transparent helper labels, and automatic face detection fallback.
- [x] **Real-Time Training Feedback**: Fully tactile status updates (e.g. `"Loading & detecting face..."`, `"Retraining face recognition model..."`) paired with busy override cursors and temporary interface lockouts to provide perfect, seamless transition feedback during batch cropping.
- [x] **Individual Reference Image Removal**: Delete specific reference images via interactive red corner corner close markers on thumbnails, triggering immediate `.npy` cache cleanups.
- [x] **Extended Multi-Selection**: Select and batch-delete multiple identities at once using standard keyboard hotkeys (Ctrl+Click, Shift+Click, or Drag).
- [x] **Live Biometric Threshold Synchronization**: Adjusting the Face Matching Threshold or Text Auto-Redact cutoff in the Settings dialog instantly synchronizes with the deep-learning backend.

## System & Interface
- [x] **Interactive GUI**: Sleek modern interface built using PySide6.
- [x] **Premium UI/UX Polish**: Premium unified deep-dark `#0B0F19` canvas, custom `NewIdentityDialog` with matching aesthetics (including Enter-key Save/Default support), global transparent labels, and tactile `PointingHandCursor` feedback on all interactive components (buttons, checkboxes, comboboxes, menus, and list items).
- [x] **Keyboard-Driven Workflow**: Fully complete and safety-guarded keyboard navigation. Navigate queue, toggle Draw/Persist modes, and use `Left`/`Right` arrow keys to cycle focus on detected bounding boxes, toggling them with `Space`/`C`. All shortcuts are automatically bypassed when input fields are active or modal dialogs are open to prevent conflicts.
- [ ] **Rebindable Shortcuts Settings**: Settings panel to allow users to fully customize and rebind keys (Planned).
- [ ] **CLI Interface**: Command-line batch processing with ArgumentParser. (Planned/Partial), It's half baked rn.
- [x] **Cross-Platform Compatibility**: Fully safe and optimized file path handling across Linux and Windows.
- [x] **Graceful Shutdown**: Instant and clean `Ctrl+C` signal handling in the GUI.

## Visual Confidence & Color Legend

To make reviewing sensitive matches completely intuitive and tactile, SafeMARC uses distinct visual states and colors based on match type and calculated confidence:

| State / Match Type | Status | Outline Style | Fill Style | Identity Label | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Low-Confidence Text** | Checked (Selected) | **Solid Amber** (`#F59E0B`, thickness: 3) | **Amber Fill** (opacity: 50) | Visible (if set) | Calculated confidence falls below the user's customized text cutoff threshold, but explicitly selected for redaction. |
| **Low-Confidence Text** | Unchecked (Unselected) | **Dashed Amber** (`#F59E0B`, thickness: 2) | **Light Amber Fill** (opacity: 15) | Hidden | "Review Suggested" state; isolated pattern match lacking context keywords. Unselected by default. |
| **Known Face Hit** | Checked (Selected) | **Solid Green** (`#10B981`, thickness: 3) | **Green Fill** (opacity: 50) | Visible | Matched biometric face with similarity score above the face matching threshold. |
| **High-Confidence Hit** | Checked (Selected) | **Solid Red** (`#FF0000`, thickness: 3) | **Red Fill** (opacity: 50) | Visible (if set) | High-confidence text (confidence $\ge$ threshold), generic face, body silhouette, or custom manual draw box. |
| **De-selected Hit** | Unchecked (Unselected) | **Dashed Grey** (`#646464`, thickness: 2) | **Transparent** (no fill) | Hidden | Standard high-confidence or generic hit that the user has unchecked to skip redacting. |

For more information, please check `requirements.txt`.