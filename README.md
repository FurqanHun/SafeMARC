# SafeMARC - Sensitive Media Automatic Redaction and Concealment

SafeMARC is a privacy-focused desktop application designed to automatically detect and redact Sensitive Personal Identifiable Information (SPII) and faces from images, PDFs, and digital documents.

The system will focus on reliably detecting structured sensitive data such as phone numbers, ID numbers, card numbers, and other pattern-based information, along with face detection in visual media.

For categories that require heavier linguistic or AI-based processing (e.g., name detection), the system will provide a customizable rule-based module. Users can define their own redaction rules using keywords, strings, or patterns (e.g., regex), allowing flexible and user-controlled detection without requiring complex model training.

The goal of SafeMARC is to provide a practical, efficient, and user-configurable privacy tool for securely sharing digital content, which runs directly on their system locally.

## Setup for Windows

1. **Install Python 3.10+**: Make sure "Add to PATH" is checked.
2. **Install Tesseract OCR**:
   - Download the installer here: https://github.com/UB-Mannheim/tesseract/wiki
   - **IMPORTANT:** During install, copy the path (usually `C:\Program Files\Tesseract-OCR`).
   - You might need to add this path to your System Environment Variables.
3. **Create Virtual Environment (CRITICAL)**:
   Open your terminal in the project folder and run:
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
  ```

4. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
    ```
  
5. **Run the app**:
  ```bash
  python src/main.py
```


## Structure

```
SafeMARC/
├── .gitignore      
├── requirements.txt
├── README.md
├── setup.py
│
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── gui/
│   ├── core/              <-- OCR, Redaction logic
│   └── utils/             <-- Helpers (PDF parsers, Config loaders)
│
├── assets/                <-- Icons, logos, UI themes (non-code)
├── tests/                 <-- Unit tests (eventually)
└── docs/                  <-- FYP documentation
```
