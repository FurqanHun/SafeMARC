# SafeMARC Automated Testing Suite

SafeMARC features a comprehensive, isolated test suite built using **pytest** to verify scanner heuristics, cryptographic/algorithmic validations, PDF page rendering, face biometrics training, and settings synchronization.

---

## Test Suite Structure

The test modules are located in the `tests/` directory:

| Test File | Target Module | Scope of Coverage |
| :--- | :--- | :--- |
| **`test_validators.py`** | `src/core/detectors/text.py` | Validates Luhn checksum algorithm (Credit Cards), ISO 7064 Mod-97 checksum (EU IBAN), and the Proximity Keyword Confidence Boosting heuristics (boosting ambiguous regex matches from 25% to 90% or 95% if matching keywords appear nearby). |
| **`test_regex_patterns.py`** | `src/core/patterns.py` | Validates all 22 predefined country-specific regex patterns (Global, US, EU, UK, PK, IN) against positive matching samples and negative false-positive cases. |
| **`test_pdf_handler.py`** | `src/utils/pdf_handler.py` | Tests PDF extraction pipelines (splitting pages to high-quality PNGs, retrieving digital character bounding coordinates directly via PyMuPDF) and building output documents from list of page images. |
| **`test_pdf_navigation.py`** | `src/gui/main_window.py` | Tests PDF page navigation lifecycles, spinbox synchronization, direct page jumping, selection caching, and the deferred finalization compilation pipeline. |
| **`test_identity_manager.py`** | `src/core/identity_manager.py` | Tests biometric face reference setup. Isolates session-specific temporary identities vs. permanent reference photos, handles thumbnail registration, and validates YuNet cropping/embedding pipelines in a mock environment. |
| **`test_scanner.py`** | `src/core/scanner.py` | Verifies the zero-lag session cache (ensuring subsequent scans retrieve cached hits instead of executing heavy vision/OCR modules twice), face redaction modes (All, Whitelist, Blacklist), and scanner-redactor pipelines. |
| **`test_shortcut_settings.py`** | `src/gui/settings_dialog.py` | Verifies default keybindings registration and dynamic shortcut updates to `QShortcut` objects inside `SafeMARCMainWindow` on rebinding. |
| **`test_settings_dialog.py`** | `src/gui/settings_dialog.py` | Verifies settings dialog configurations, including localized identities tab keyboard shortcuts (`Ctrl+Shift+N`, `F2`, `Ctrl+D`, `Ctrl+I`, `Ctrl+E`, `Ctrl+Shift+A`), tab-scoped triggers, and real-time re-binding propagation. |
| **`test_ui_caching.py`** | `src/gui/main_window.py` | Verifies correct cache handling and selection restoration behavior for manually selected files in the queue without triggering redundant background scans. |
| **`test_quick_add_dialog.py`** | `src/gui/main_window.py` | Verifies instantiation, autocomplete population, save/cancel actions, and empty name handling of the QuickAddIdentityDialog. |
| **`test_import_export.py`** | `src/utils/crypto.py` / `src/gui/settings_dialog.py` / `src/gui/main_window.py` | Verifies standard PBKDF2 + SHA-256 CTR encryption/decryption roundtrips, secure Zip Slip path traversal defenses, package zip/unzip restore routines, and custom text/regex patterns encrypted export and backward-compatible JSON import. |

---

## Running the Tests

To run the complete test suite, execute pytest inside the project's virtual environment:

```bash
# Run the entire test suite
pytest tests/

# Run tests with verbose outputs
pytest -v tests/
```

During test collection, the system path is automatically resolved to include the `src/` directory via `tests/conftest.py`

---

## Automated Post-Test Session Cleanup

To prevent host machine pollution, SafeMARC implements an automated garbage collection routine. 

Once pytest finishes collecting and running all 53 tests, the session hook `pytest_sessionfinish` inside `tests/conftest.py` executes:
1. It locates the system-level temporary directory `/tmp/safemarc_temp` used for sandbox PDF and face crop outputs.
2. It deletes `/tmp/safemarc_temp` recursively.
3. It bypasses standard stdout capture to print a clean confirmation directly in your terminal:
   ```text
   [Cleanup] Cleared temporary test files at /tmp/safemarc_temp
   ```
