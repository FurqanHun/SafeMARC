# SafeMARC Coding Guidelines and Commenting Standards

This document establishes the coding patterns, commenting guidelines, and commit standards for the SafeMARC project. Developers must adhere to these practices to ensure codebase maintainability and clean design.

---

## 1. Coding Patterns & Architecture

### 1.1 Asynchronous Operations & Threading
* **Rule**: All heavy operations—such as PDF page extraction, deep learning/computer vision scanning, and PDF compilation—must run asynchronously in background threads.
* **Mechanism**: Use `QThread` workers (e.g., `PDFExtractWorker`, `PDFFinalizeWorker`) to offload I/O and CPU-bound tasks.
* **Thread Safety**: 
  * Do not interact with or mutate GUI widgets directly from background threads.
  * Use PySide6 `Signal` and `Slot` mechanisms exclusively to pass data and progress updates back to the UI main thread.

### 1.2 State Management and Caching
* **Caching**: Use memory caches (e.g., `user_selections_cache`, `_scan_cache`) to store intermediate results, manual redaction hits, and reviewed page states.
* **Consistency**: Ensure manual modifications made by the user are synchronized with state caches during page transitions, direct navigation jumping, or background compilation.

### 1.3 Modular Design
* **Separation of Concerns**: Keep UI layouts and styling separated from detection logic, file I/O operations, and cryptographic functions.
  * `src/gui/`: Application windows, layouts, dialogs, and custom widgets.
  * `src/core/`: Detection algorithms, scanners, redactors, and identity management.
  * `src/utils/`: Cryptography, file utilities, paths, and platform-specific helpers.

### 1.4 Logging over Print (`src/core/*`, `src/gui/*`, `src/utils/*`)
* Every file in the codebase imports the standard Python `logging` module and initializes a logger at the top using `logger = logging.getLogger(__name__)`. Print statements are avoided.

### 1.5 Conditional Type Hinting (`src/core/scanner.py`, `src/utils/crypto.py` vs `src/gui/main_window.py`)
* Core logic and utilities strictly define return types and argument types (e.g., `def encrypt_data(data: bytes) -> bytes:`). However, standard PyQt/PySide UI callbacks (`paintEvent`, `mousePressEvent`) or internal UI slots rarely use type hints, showing a relaxed enforcement for boilerplate GUI methods.

### 1.6 Fail-Safe Exception Handling in GUI (`src/gui/settings_dialog.py`, `src/gui/main_window.py`)
* GUI components wrap non-critical operations in broad `except Exception:` or `except Exception as e:` blocks. This fail-safe pattern ensures that minor UI errors or specific file I/O failures do not crash the entire application.

### 1.7 UI Slot Naming Conventions (`src/gui/settings_dialog.py`)
* Internal Qt slots and callbacks are consistently prefixed with a leading underscore (e.g., `_on_clicked`, `_refresh_people_list`, `_add_person`) to distinguish them from public methods and API calls.

### 1.8 Lazy Imports for Performance (`src/gui/preview_widget.py`, `src/gui/settings_dialog.py`)
* Heavy UI components or specific dialog modules (like `QMenu` in `preview_widget.py` or `QSvgRenderer` in `settings_dialog.py`) are imported locally inside the function that needs them, rather than at the top of the file, presumably to reduce application startup time.

### 1.9 PEP 8 / Google Python Style Adherence (`src/utils/pdf_handler.py`, `src/core/identity_manager.py`)
* **Naming**: Classes use `CamelCase` (`IdentityManager`, `SafeScanner`), while functions and variables strictly use `snake_case` (`extract_pages`, `image_paths`).
* **Constants**: Module-level constants are in `UPPER_SNAKE_CASE` (e.g., `SVG_CLOSE`, `DEFAULT_SHORTCUTS`). Private constants prefix with an underscore (e.g., `_YUNET_SCORE_THRESH`).
* **String Formatting**: `f-strings` are used universally over `.format()` or `%` formatting.

### 1.10 OOP Abstractions & Static Methods (`src/core/detectors/base.py`, `src/utils/pdf_handler.py`)
* **Interfaces**: Core system plugins (detectors) inherit from an Abstract Base Class (`class BaseDetector(ABC):`) defining `@abstractmethod` functions, mandating strict interfaces for subclasses.
* **Static Utility Classes**: Utility files group pure functions inside static classes (e.g., `@staticmethod def extract_pages()` inside `PDFHandler`), which prevents global namespace pollution.

---

## 2. Commenting Guidelines

SafeMARC adopts a **minimalist, formal, and non-redundant** commenting philosophy. The code itself should be readable, self-documenting, and descriptive.

### 2.1 General Principles
* **No Conversational Comments**: Avoid chatty or informal notes, personal remarks, or instructions (e.g., `# Let's do this now`, `# Loop through everything`).
* **No Redundant Comments**: Do not write comments that restate what the code clearly does. If a variable, method, or class name is self-explanatory, do not comment on it.
* **Documentational Focus**: Comments should explain *why* something is done or specify the structure of non-obvious data types, rather than describing *how* basic code works. If the code is inherently complex and hard for another person to understand, phrasing the explanation in a formal, documentational way is permitted. However, this exception is strictly reserved for difficult-to-understand code.

### 2.2 Formatting and Placement
* **Docstrings**: Use Python triple-quoted docstrings (`"""`) for modules, classes, and public methods to document their high-level intent, inputs, and outputs.
* **Inline Comments**: Keep inline comments to an absolute minimum. Use them only for complex formulas, algorithm overrides, or coordinate transformations.
* **Block Comments**: Use block comments (`#`) only when explaining a multi-step, non-obvious block of logic.

### 2.3 Good vs. Bad Examples

#### Bad (Conversational & Redundant)
```python
# Create a new list for hits
hits = []

# Loop through all the detections
for d in detections:
    # Check if the confidence is greater than 50%
    if d.confidence > 0.5:
        # Add it to the list
        hits.append(d)
```

#### Good (Self-Documenting Code)
```python
hits = [d for d in detections if d.confidence > 0.5]
```

#### Bad (Instructional inline notes)
```python
# Fallback to LBPH if SFace is not installed
self.recognizer = cv2.face.LBPHFaceRecognizer_create()
```

#### Good (Documential docstring and clean naming)
```python
class IdentityManager:
    """Manages permanent and session identities using SFace or LBPH."""
```

---

## 3. Commit Guidelines

We enforce the **Conventional Commits** specification for clear, readable git histories.

### 3.1 Format
Commits must follow the format:
```
<type>(<scope>): <description>
```
* **Types**:
  * `feat`: A new feature (e.g., background threading, granular skips).
  * `fix`: A bug fix (e.g., Tesseract path location on Windows).
  * `docs`: Documentation updates (e.g., class diagrams, workflows, guidelines).
  * `refactor`: Code restructuring without functional changes.
  * `test`: Adding or updating unit tests.
* **Scope**: Optional, indicating the specific subsystem (e.g., `gui`, `pdf`, `core`).
