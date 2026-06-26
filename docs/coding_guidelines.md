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

---

## 2. Commenting Guidelines

SafeMARC adopts a **minimalist, formal, and non-redundant** commenting philosophy. The code itself should be readable, self-documenting, and descriptive.

### 2.1 General Principles
* **No Conversational Comments**: Avoid chatty or informal notes, personal remarks, or instructions (e.g., `# Let's do this now`, `# Loop through everything`).
* **No Redundant Comments**: Do not write comments that restate what the code clearly does. If a variable, method, or class name is self-explanatory, do not comment on it.
* **Documential Focus**: Comments should explain *why* something is done or specify the structure of non-obvious data types, rather than describing *how* basic code works.

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
