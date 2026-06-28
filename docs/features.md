# SafeMARC Features

## Performance & Architecture
- [x] **Zero-Lag Session Caching**: An advanced memory dictionary cache that saves full biometric and text hits per file/page, ensuring backwards and forwards queue navigation is instantaneous (<10ms latency). Text/OCR hits are cached separately from vision/face hits so that adding or modifying face identities only invalidates the vision cache, keeping the slow OCR/Tesseract results cached for all session documents.
- [x] **Stable PDF Cache Keys**: Maps randomized temporary PDF extraction paths to stable document/page keys to perfectly track PDF hits inside the zero-lag session cache.
- [x] **Unified Resource Pooling**: All temporary files (PDF pages, cropped identities, clipboard images, and redacted assets) are securely managed inside a single system-level `safemarc_temp` directory to prevent workspace clutter and bypass Windows permission issues.
- [x] **Graceful RAII Loop Guard**: PySide6 event loops are protected with a custom `SIGINT` signal handler and a `try-finally` Python RAII guard. This guarantees that `safemarc_temp` is securely and completely purged even if the application is killed forcefully with `Ctrl+C`.
- [x] **Persistent Diagnostics & Logging**: Automatically initializes Python `faulthandler` to log native C/C++ segmentation faults, paired with a custom `TeeStream` redirection that writes diagnostic outputs to both standard streams and a persistent `safemarc.log` file in the XDG app data directory. The logging and `TeeStream` redirection are fully resilient to headless and packaged `noconsole` environments (such as PyInstaller builds), safely checking stream existence, catching write/flush errors, and implementing a fallback `fileno()` method.
- [x] **Safety-Focused Keyboard Focus Filter**: Replaces crash-prone PySide6 `focusChanged` signals with a custom `FocusEventFilter` to safely manage keyboard focus shifting, prevent infinite loops, and handle ESC keybindings.
- [x] **Non-Blocking Background Threads & Real-Time Progress Feedback**: Migrates heavy, long-running operations (like PDF page extraction and final PDF compilation) into dedicated background `QThread` workers (`PDFExtractWorker` and `PDFFinalizeWorker`). Displays a premium, custom-styled dark-themed modal `LoadingDialog` containing an animated spinner, custom typography, and a native `QProgressBar` reporting granular, step-by-step page-by-page progress in real-time, eliminating GUI freezes and ensuring seamless multitasking.
- [x] **Dynamic RAM Governance**: Configurable **Soft RAM Limit** and **Hard RAM Limit** sliders in the Performance settings tab (range 512 MB to total system RAM; defaults: `1024/2048 MB` for < 8 GB RAM, `1536/3072 MB` for 8–16 GB, `2048/4096 MB` for > 16 GB, all auto-derived at startup via `psutil`). A background watch loop enforces tiered reclamation: breaching the soft limit prunes the in-memory OCR cache (retaining only the 2 most recent pages); breaching the hard limit fully flushes all caches and destroys active vision detectors (releasing MediaPipe/TFLite heap). Cross-platform heap release is triggered after every reclamation cycle — `malloc_trim(0)` on Linux, `SetProcessWorkingSetSize` on Windows — ensuring OS-level memory monitors (htop, Task Manager) reflect the reclaim immediately.
- [x] **Session-Only OCR Cache**: OCR results are stored exclusively in-memory (never persisted to disk) in a dict keyed by `(image_path, pdf_words)`. Maximum pages cached defaults to `50` (< 8 GB RAM), `100` (8–16 GB), or `200` (> 16 GB), and is configurable via the **Max OCR Cache Pages** slider in Performance settings. The cache is fully cleared at the end of each batch review session (unless **Preserve OCR cache across batch reviews** is enabled).
- [x] **Proactive Mid-Scan Memory Reclamation**: `VisionDetector` calls `_reclaim_if_needed()` after every inference pass (face detection Pass 1, and each tile in the adaptive body detection tiling loop) to immediately `del` transient image buffers and trigger heap release before they accumulate across a large batch.
- [x] **Configurable PDF Extraction Zoom**: PDF pages are rasterized at a user-configurable zoom level (default 2×, settable in Performance tab). This replaces the previous hard-coded 4× extraction, reducing the peak memory footprint of large PDFs by up to 75% with no perceptible quality loss for typical A4 documents.
- [x] **Global Output Folder Enabled by Default**: Settings now default to saving all outputs in a global folder, persisting user preference across sessions.
- [x] **Manual Hit Color Updated**: Updated UI highlight color for manual hits to improve visual contrast.
- [x] **Skip Remaining Pages Option**: Added UI control to fast‑forward through remaining pages during batch review.
- [x] **Static Title During PDF Review**: Toolbar title remains "SafeMARC" throughout PDF navigation for a cleaner UI.

 
## Core Vision Features
- [x] **Face Detection**: Fast & high-accuracy face scanning via **YuNet DNN** (`assets/face_detection_yunet_2023mar.onnx`).
  - *Multi-Scale Strategy*: Employs a dual-scale pipeline (native resolution for small/medium faces, and downscaled 640px pass to capture large portrait-sized faces) to overcome DNN training scale limits.
  - *Containment-Aware NMS*: Replaces standard IoU NMS with a custom containment-ratio NMS (40% threshold) to prevent sub-face false positives (eyes, lips) inside larger face boxes.
  - *Dynamic Settings Integration*: Leverages user-customizable face detection threshold settings (`model_face_detect_yunet`) dynamically read from QSettings, defaulting to `0.70`.
- [x] **Face Recognition**: Deep learning identity matching via SFace (OpenCV DNN) with LBPH fallback.
  - *Landmark-Based Geometric alignCrop*: Reference and live images are normalized using YuNet's 5 facial landmark coordinates and `alignCrop()` to correct for rotation, scale, and tilt before embedding extraction.
  - *Context-Aware Tiered Margin*: Matches are gated by a tiered margin check where borderline scores in group photos require stricter separation (0.20) than portrait shots (0.10) to prevent false matches in crowded frames.
- [x] **Body Detection**: Robust human body and silhouette detection.
  - *EfficientDet-Lite2 (TFLite)*: Leverages MediaPipe Object Detector with a lightweight, high-performance `efficientdet_lite2.tflite` model to detect full bodies and silhouettes with low latency.
  - *Adaptive Tiling & Upscaling*: Employs an adaptive multi-scale tiling grid (up to 4x3) for larger images to capture small-scale bodies, and 2x upscaling for small images (<640px) to boost detection recall.
  - *Standard IoU NMS & Sliver Filtering*: Switched body detection NMS from containment-ratio to standard IoU NMS (0.55 threshold) to prevent merging overlapping adjacent people, paired with a height/width ratio filter (h >= w * 0.5) to discard sliver false positives (hands, arms, necks).
  - *Depth-Ordered Clipping*: Trims back-row body boxes so they don't cover front-row faces (heuristic: lower bottom edge = in front).
  - *Face-Body Hybrid Identity Mapping*: Bodies are spatially mapped to identified faces; if a body contains a matched face, it is tagged with that identity, enabling identity-based filtering for body redactions.
  - *Face-Guided Recovery*: Automatically estimates and generates a synthetic body box centering any identified face that was missed by the body detector to ensure complete body redaction for sensitive targets.
- [x] **Text Only Mode**: Ability to disable image/face scanning to focus strictly on text redactions.
- [x] **Redact All**: Auto-redact all detected faces/bodies in a document.
- [x] **Whitelist Mode**: Redact all faces/bodies except those matching specific approved identities.
- [x] **Blacklist Mode**: Specifically redact only matched sensitive identities (faces and their corresponding bodies).

 
## Text Redaction
- [x] **Smart PDF Text Extraction & OCR Fallback**: Leverages native PDF digital text via PyMuPDF for perfect accuracy, with a highly optimized Tesseract OCR fallback (OpenCV binarization and 2x upscaling) for scanned documents. Automatically auto-locates Tesseract installation paths across multiple operating systems on startup and execution (Windows standard Program Files paths, macOS Homebrew/MacPorts, and Linux system binary paths) even if not present in the user's PATH environment variable.
- [x] **Predefined & Dynamic Regional Patterns**: Pre-configured rules for common entities grouped by country regions. The user can toggle these regions via the UI, instantly re-evaluating matches:
  - **Global**: Credit Card numbers (Visa, Mastercard, Amex, etc.), Email Addresses, IPv4 Addresses, Names (with title prefixes e.g. Mr, Dr, Mrs), and Street Locations/Addresses.
  - **Pakistan**: National Identity Card (CNIC), Phone Numbers, Passports, Driving Licenses, and Vehicle Registration Plates.
  - **United States**: Social Security Numbers (SSN), Phone Numbers, Zip Codes, and Driver's Licenses.
  - **European Union**: IBAN Bank Account numbers, VAT Registration Numbers.
  - **India**: Aadhaar Card numbers, Phone Numbers, PAN Card numbers, and Driving Licenses.
  - **United Kingdom**: National Insurance Numbers (NINO), Phone Numbers.
- [x] **Algorithmic Verification & Mod-97 Checksum**: Employs mathematical structural validation (e.g. ISO 7064 mod-97 checksum checks for IBAN accounts) to immediately discard invalid OCR text matches.
- [x] **Context Proximity & Review Suggested State**: Matches found near context keywords are boosted to 90% or 95% confidence. Isolated ambiguous matches (like Zip Codes, IPs) default to 30% confidence, while high-value targets (SSN, Aadhaar) lacking surrounding context keywords drop to 25% confidence, keeping them review-suggested and hidden from automatic selection by default.
- [x] **Custom Pattern Import/Export**: Export custom strings or complex Regular Expressions as password-protected, encrypted `.smpat` (SafeMARC Patterns) packages. Uses standard cryptographic primitives (PBKDF2-HMAC-SHA256 with 100,000 iterations for key derivation and SHA-256 CTR mode for data encryption) with a random salt to lock the package. Users can also choose to export in unencrypted JSON (`.json`) format. Importing accepts both formats, asking for a password when loading `.smpat` packages to decrypt and restore pattern configurations.
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
- [x] **Interactive PDF Page Navigation & Direct Jumping**: An elegant, custom-styled toolbar panel containing a page spinbox (`Page X / Y`) next to the SafeMARC title. Changing the spinbox value triggers immediate, direct navigation to any page in the active PDF. The toolbar title dynamically adjusts to eliminate redundant labels, and page changes automatically commit current redaction states to the zero-lag session cache.
- [x] **PyMuPDF Rebuilding Engine**: Uses the lightweight PyMuPDF (`fitz`) library to rebuild final sanitized PDFs from redacted page images, resolving Pillow rendering/color-space issues. Rebuilt pages preserve original page dimensions and utilize 2× downscaling combined with highly optimized JPEG compression (quality 85) to reduce compiled PDF file size by up to 98% compared to uncompressed source PDFs. PDF pages are extracted at a configurable zoom level (default 2×) which propagates consistently through extraction, OCR coordinate scaling, and PDF rebuilding.
- [ ] **Word Documents (`.docx`)**: Planned for future releases.

## Non-Destructive Review Workflow
- [x] **Manual Toggle**: Intersected regions/boxes can be untoggled before saving.
- [x] **Manual Draw Tool**: Ability to toggle "Draw Box" mode (with a button or the `D` keyboard shortcut) to draw custom redaction rectangles, rendered in a distinct bright purple (`#A855F7`) to separate them from automated detections.
- [x] **Persistent Draw Tool**: Persistent manual redaction boxes across the entire queue or specific PDF pages for repeating layouts (toggled via the premium "Persistent Boxes" pin button).
- [x] **Auto-Skip Clean Images**: Configurable feature to bypass images with no detected sensitive hits for a faster review.
- [x] **Granular PDF Skipping & Skip Remaining Pages**:
  - *Current Page*: Skips only the current page, moving to the next.
  - *Remaining Pages*: Bypasses all upcoming pages in the document. Automatically copies unreviewed pages to the compilation stack as clean/original, commits any edits already made, and triggers background compilation to build the finalized PDF immediately.
  - *Entire PDF*: Aborts review of the current document entirely, discarding changes, and advances the batch queue.
- [x] **Skip Review Mode**: Configurable checkbox toggle to run fully automated review and redaction across all items.
- [x] **Stop Review**: Option to exit the active batch review process without clearing the queue.
- [x] **Queue Management**: Direct queue manipulation allowing users to remove any individual file before/during review.
- [x] **Drag and Drop**: Support dragging and dropping files or folders directly into the queue list widget.
- [x] **Clipboard Integration**: Support pasting images (`Ctrl+V`) directly from the clipboard to auto-generate a temporary review item.
- [x] **Global Output Folder & Clipboard Safety**: Configuration to specify a custom global folder for all redactions. Clipboard-pasted files automatically redirect here to prevent loss in system temporary directories.
- [x] **Backwards Navigation & PDF Re-entry**: Full navigation history to step backward to a previous file or PDF page. Re-entering a completed PDF prompts the user to restart from Page 1, ensuring a clean sequential compilation stack.
- [x] **Strict Start-from-First-Item Queue**: Enforces that starting batch reviews always initiates from the first item in the queue (index 0) to guarantee a consistent and predictable review workflow.
- [x] **State Selections & Checkbox Persistence**: Keeps the exact checked/unchecked state of all AI detections and manually added bounding boxes perfectly synchronized and persistent across queue navigation (back, next, skip) and settings/pattern rescans.

## Biometric Identity Editor
- [x] **Interactive 1:1 Aspect-Ratio Crop Editor**: Crop uploaded reference faces with a locked 1:1 aspect ratio, interactive resize handles, transparent helper labels, and automatic face detection fallback.
- [x] **Real-Time Training Feedback**: Fully tactile status updates (e.g. `"Loading & detecting face..."`, `"Retraining face recognition model..."`) paired with busy override cursors and temporary interface lockouts to provide perfect, seamless transition feedback during batch cropping, automatically clearing status feedback when addition or cropping is cancelled.
- [x] **Individual Reference Image Removal**: Delete specific reference images via interactive red corner corner close markers on thumbnails, triggering immediate `.npy` cache cleanups.
- [x] **Extended Multi-Selection**: Select and batch-delete multiple identities at once using standard keyboard hotkeys (Ctrl+Click, Shift+Click, or Drag).
- [x] **Identity Renaming**: Dynamic and validated renaming of identities (via the rename button `✎` or double-clicking the item in the list) with path traversal guards and directory conflict resolution.
- [x] **Customizable Keyboard Shortcuts**: Full hotkey integration inside the identities tab (e.g., adding, renaming, deleting, importing, exporting, and uploading images) with configurable mappings in the Shortcuts Settings tab.
- [x] **Live Biometric & Target Synchronization**: Adjusting the Face Matching Threshold, Face Detection Threshold (YuNet), Body Detection Threshold (EfficientDet), the Text Auto-Redact cutoff in the Settings dialog, or checking/unchecking target identities instantly re-evaluates and updates matches in the preview canvas in real-time.
- [x] **Smart Quick-Add Combobox Dropdown**: Right-click to assign a face directly from the preview canvas using a styled autocompleting dropdown combobox. Re-using an existing name directly appends the reference photo to the correct permanent or session folder, while new names prompt the user for save-type preferences.
- [x] **Secure & Locked Import/Export**: Export selected or all permanent biometric reference photos into a password-protected, encrypted archive in the proprietary `.smid` (SafeMARC Identity) format. Uses standard cryptographic primitives (PBKDF2-HMAC-SHA256 with 100,000 iterations for key derivation and SHA-256 CTR mode for data encryption) with a random salt to lock the package. Importing requires the password, extracts the archive securely with path traversal guards (Zip Slip protection), and automatically runs face detection to rebuild the SFace/LBPH recognition embeddings.

## System & Interface
- [x] **Interactive GUI**: Sleek modern interface built using PySide6.
- [x] **Premium UI/UX Polish**: Premium unified deep-dark `#0B0F19` canvas, custom `NewIdentityDialog` with matching aesthetics (including Enter-key Save/Default support), global transparent labels, and tactile `PointingHandCursor` feedback on all interactive components (buttons, checkboxes, comboboxes, menus, and list items).
- [x] **Keyboard-Driven Workflow**: Fully complete and safety-guarded keyboard navigation. Navigate queue, toggle Draw/Persist modes, and use `Left`/`Right` arrow keys to cycle focus on detected bounding boxes, toggling them with `Space`/`C`. All shortcuts are automatically bypassed when input fields are active or modal dialogs are open to prevent conflicts. Keyboard focus/tabbing is cleared by default when starting or navigating in batch reviews, keeping the focus strictly on the window unless explicitly activated by pressing the `Tab` key, and pressing `Escape` on any focused widget exits tabbing mode.
- [x] **Queue Protection in Batch Mode**: Queue-modifying controls (Add File, Add Folder, Clear Queue, Paste, Remove) and the Settings dialog are automatically disabled while batch review is active to prevent modification during processing, while vision checklists and pattern configuration controls remain fully enabled.
- [x] **Rebindable Shortcuts Settings**: Dedicated settings panel tab to interactively rebind, conflict-check, and persist all 30 keyboard shortcuts using QSettings.
- [x] **AI Engine & Environment Diagnostics**: A dynamic `ClickableStatusLabel` in the main toolbar providing one-click access to the `EngineStatusDialog`, which validates installation state and path locations of AI engines (YuNet face detection model, SFace face recognition model, MediaPipe body silhouette detector, and Tesseract OCR).
- [x] **CLI Interface**: Robust command-line batch processing via `src/cli/cli.py` supporting `-i/--input`, `-o/--output-dir`, `--use-suffix`, `--faces`, `--redact-body`, and `--text` flags.
- [x] **Cross-Platform Memory Trimming**: After each memory reclamation cycle, heap pages are released back to the OS using `malloc_trim(0)` on Linux and `SetProcessWorkingSetSize` on Windows, ensuring that freed Python/C++ allocations are immediately visible to system monitoring tools.
- [x] **Cross-Platform Compatibility**: Fully safe and optimized file path handling across Linux and Windows.
- [x] **Graceful Shutdown**: Instant and clean `Ctrl+C` signal handling in the GUI.

## Visual Confidence & Color Legend

To make reviewing sensitive matches completely intuitive and tactile, SafeMARC uses distinct visual states and colors based on match type and calculated confidence:

| State / Match Type | Status | Outline Style | Fill Style | Identity Label | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Low-Confidence Text** | Checked (Selected) | **Solid Amber** (`#F59E0B`, thickness: 3) | **Amber Fill** (opacity: 80) | Visible (if set) | Calculated confidence falls below the user's customized text cutoff threshold, but explicitly selected for redaction. |
| **Low-Confidence Text** | Unchecked (Unselected) | **Dashed Amber** (`#F59E0B`, thickness: 2) | **Light Amber Fill** (opacity: 30) | Hidden | "Review Suggested" state; isolated pattern match lacking context keywords. Unselected by default. |
| **Known Face Hit** | Checked (Selected) | **Solid Green** (`#10B981`, thickness: 3) | **Green Fill** (opacity: 80) | Visible | Matched biometric face with similarity score above the face matching threshold. |
| **High-Confidence Hit** | Checked (Selected) | **Solid Red** (`#EF4444`, thickness: 3) | **Red Fill** (opacity: 80) | Visible (if set) | High-confidence text (confidence $\ge$ threshold), generic face, or body silhouette. |
| **Custom Manual Box** | Checked (Selected) | **Solid Purple** (`#A855F7`, thickness: 3) | **Purple Fill** (opacity: 80) | Hidden | Custom manual draw box defined directly by the user. |
| **De-selected Hit** | Unchecked (Unselected) | **Dashed Grey** (`#646464`, thickness: 2) | **Transparent** (no fill) | Hidden | Standard high-confidence or generic hit that the user has unchecked to skip redacting. |

For more information, please check `requirements.txt`.