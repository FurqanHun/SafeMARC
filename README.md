# SafeMARC - Sensitive Media Automatic Redaction and Concealment

> [!WARNING]
> **Pre-Alpha Stage Notice:** This project is currently in a pre-alpha stage. No official release build is shipped yet. This project should only be used for development or testing purposes.

SafeMARC is a privacy-focused desktop application designed to automatically detect and redact Sensitive Personal Identifiable Information (SPII) and faces from images, PDFs, and digital documents.

The system will focus on reliably detecting structured sensitive data such as phone numbers, ID numbers, card numbers, and other pattern-based information, along with face detection in visual media.

For categories that require heavier linguistic or AI-based processing (e.g., name detection), the system will provide a customizable rule-based module. Users can define their own redaction rules using keywords, strings, or patterns (e.g., regex), allowing flexible and user-controlled detection without requiring complex model training.

The goal of SafeMARC is to provide a practical, efficient, and user-configurable privacy tool for securely sharing digital content, which runs directly on their system locally.

## Setup for Windows

1. **Install Python 3.12**: Make sure "Add to PATH" is checked.
2. **Create Virtual Environment (CRITICAL)**:
   Open your terminal in the project folder and run:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the app**:
   ```bash
   python main.py
   ```

## Required System Dependencies

### Tesseract OCR (Required for all modes)
Tesseract OCR is required for the text extraction and OCR features of the application on all platforms, whether you run the app from Python source code, build it yourself, or run the pre-compiled standalone executable.
- **Windows**: Download and run the installer from the [UB-Mannheim Wiki](https://github.com/UB-Mannheim/tesseract/wiki). Copy the installation path (usually `C:\Program Files\Tesseract-OCR`) and add it to your system Environment Variables (PATH).
- **Linux**:
  - **Fedora**: `sudo dnf install tesseract`
  - **Ubuntu / Debian**: `sudo apt install tesseract-ocr`

## Linux Standalone Binary Dependencies

If you are running the pre-compiled standalone Linux executable, please note that core desktop system libraries are **not bundled** inside the package. Bundling them causes dynamic library ABI and symbol mismatches across different Linux distributions, resulting in segmentation faults on startup or during keyboard shortcut interactions.

Instead, the executable dynamically loads the system-native versions. While most desktop environments have these pre-installed, ensure the following libraries are installed on your host system if they are missing:
- `libxkbcommon` & `libxkbcommon-x11` (keyboard and shortcut event mapping)
- `glib2` / `glib-2.0` (specifically `libglib-2.0`, `libgobject-2.0`, `libgio-2.0`, `libgthread-2.0`, and `libgmodule-2.0` for core desktop service bindings)
- `dbus` / `libdbus` (specifically `libdbus-1` for system D-Bus communication and native portal integration)
- `libz` (standard compression library)

## Required Models

> [!NOTE]
> These models are **only required if you clone the repository and run the app from Python source code**. The pre-compiled standalone binaries (executable packages) already bundle these models.

### Body Detection (Full Body mode)
Download into `assets/` directory as `efficientdet_lite2.tflite`:
```bash
curl -L -o assets/efficientdet_lite2.tflite "https://storage.googleapis.com/mediapipe-models/object_detector/efficientdet_lite2/float32/latest/efficientdet_lite2.tflite"
```

### Face Recognition (Blacklist/Whitelist identity matching)
Download OpenCV's SFace deep learning model (~37MB) into `assets/`:
```bash
curl -L -o assets/face_recognition_sface_2021dec.onnx "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx"
```
> [!NOTE]
> Without the SFace model, face identity matching falls back to LBPH (less accurate). The model is gitignored and must be downloaded separately.

## Structure

```
SafeMARC/
├── .gitignore      
├── requirements.txt
├── README.md
├── setup.py
├── main.py                <-- Entry point of the application
│
├── src/
│   ├── cli/               <-- Command Line Interface logic
|   |   ├── cli.py
│   ├── core/              <-- OCR, Redaction, and Scanning logic
│   │   ├── detectors/     <-- Face & text detection algorithms
│   │   ├── batch_processor.py
│   │   ├── identity_manager.py <-- Face identity recognition (SFace/LBPH)
│   │   ├── redactor.py
│   │   ├── scanner.py
│   │   └── types.py
│   ├── gui/               <-- PySide6-based Graphical User Interface
│   │   ├── main_window.py <-- Main application window layout & workflows
│   │   ├── preview_widget.py <-- Interactive image preview, zoom & draw area
│   │   └── settings_dialog.py <-- Settings & Identity Manager UI
│   └── utils/             <-- Helpers (file path normalizers, conversions)
│       └── pdf_handler.py <-- PDF page extraction and rasterized rebuilding
│
├── assets/                <-- Icons, logos, UI themes, AI models
│   └── identities/        <-- Reference face images per person
├── test_data/             <-- Sample images and PDFs for testing
├── tests/                 <-- Unit and integration tests
└── docs/                  <-- Project and developer documentation
    ├── features.md        <-- Project feature roadmap & status
    ├── shortcuts.md       <-- Keyboard and mouse shortcut guide
    ├── ui_guidelines.md   <-- Theme, colors, and layout guidelines
    └── architecture/      <-- UML, use cases, and workflow diagrams
        ├── uml_classes.md
        ├── use_cases.md
        └── workflows.md
```
