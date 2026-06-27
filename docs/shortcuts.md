# SafeMARC Keyboard Shortcuts

SafeMARC's keyboard-driven workflow enables highly efficient document review. All **30 keyboard shortcuts** listed below are fully customizable and rebindable to your preferred key combinations in **Settings** (`Ctrl` + `,`) under the **Shortcuts** tab. Custom combinations persist across application restarts.

---

## 1. General Shortcuts
| Action / Config Key | Default Key Sequence | Description |
| :--- | :--- | :--- |
| **Add Files** (`add_file`) | `Ctrl` + `O` | Add files to the review queue. |
| **Add Folder** (`add_folder`) | `Ctrl` + `Shift` + `O` | Add a whole folder of files to the review queue. |
| **Remove Selected File** (`remove_file`) | `Delete` | Remove the currently selected file from the queue. |
| **Clear Queue** (`clear_queue`) | `Ctrl` + `Shift` + `C` | Clears all files in the queue. |
| **Open Settings** (`settings`) | `Ctrl` + `,` | Opens the settings panel. |
| **Paste from Clipboard** (`paste`) | `Ctrl` + `V` | Pastes an image from the system clipboard as a temporary review item. |
| **Reset Splitter Layout** (`reset_layout`) | `Ctrl` + `Alt` + `R` | Resets the three-pane window divider splitters back to their default balanced sizes. |

---

## 2. Zoom & Navigation Shortcuts
| Action / Config Key | Default Key Sequence | Description |
| :--- | :--- | :--- |
| **Zoom In (Primary)** (`zoom_in`) | `Ctrl` + `=` | Enlarges the preview image centered on the mouse cursor. |
| **Zoom In (Alternative)** (`zoom_in_alt`) | `Ctrl` + `+` | Alternative key sequence to enlarge the preview image. |
| **Zoom Out** (`zoom_out`) | `Ctrl` + `-` | Shrinks the preview image centered on the mouse cursor. |
| **Reset Zoom** (`zoom_reset`) | `Ctrl` + `0` | Immediately resets the view to default aspect ratio and fits it in the window. |
| **Scroll Zoom** (Mouse) | `Ctrl` + Mouse Wheel | Quick zooming in and out (non-customizable). |
| **Pan Image** (Mouse) | Mouse Click & Drag | Drag in the preview area to pan when zoomed in (non-customizable). |

---

## 3. Review Actions
| Action / Config Key | Default Key Sequence | Description |
| :--- | :--- | :--- |
| **Toggle Draw Mode** (`toggle_draw`) | `D` | Switches the pointer to Draw mode to manually draw a custom redaction box. |
| **Toggle Persistent Draw Mode** (`toggle_persistent`) | `Shift` + `D` | Switches pointer to Draw mode and prompts for persistent propagation scope (propagates manual boxes across pages/files). |
| **Rescan Current File** (`rescan`) | `F5` | Re-scans the currently active file with current settings and filters. |

---

## 4. Batch Workflow Shortcuts
| Action / Config Key | Default Key Sequence | Description |
| :--- | :--- | :--- |
| **Redact & Next (Primary)** (`redact_next`) | `Shift` + `Return` | Processes redaction on the current file and loads the next item. |
| **Redact & Next (Alternative)** (`redact_next_alt`) | `Shift` + `Enter` | Alternative key sequence to redact and move to the next item. |
| **Skip Item (Primary Key)** (`skip_s`) | `S` | Skips the current file and loads the next item. |
| **Skip / Toggle Box (Space)** (`skip_space`) | `Space` | Skips the current file (or toggles a selected box if one is currently focused). |
| **Previous Item (Primary Key)** (`previous_p`) | `P` | Returns to the previous file/page in the queue. |
| **Previous Item (Alternative Key)** (`previous_bs`) | `Backspace` | Alternative key sequence to return to the previous file/page. |
| **Stop Review / Cancel** (`escape`) | `Escape` | Cancels the active batch review. Note: If keyboard focus is active, pressing `Escape` clears the highlight first; pressing it a second time stops the review. |

---

## 5. Sensitive Box Keyboard Selection
| Action / Config Key | Default Key Sequence | Description |
| :--- | :--- | :--- |
| **Focus Next Box** (`hit_next`) | `Right` | Cycles keyboard focus forward to the next detected sensitive box on the page. |
| **Focus Previous Box** (`hit_prev`) | `Left` | Cycles keyboard focus backward to the previous sensitive box on the page. |
| **Toggle Selected State** (`hit_toggle`) | `C` | Toggles the checked/unchecked state of the currently focused sensitive box. |

---

## 6. Identities Management Shortcuts
| Action / Config Key | Default Key Sequence | Description |
| :--- | :--- | :--- |
| **Add New Person** (`id_add_person`) | `Ctrl` + `Shift` + `N` | Prompts to add a new biometric identity. |
| **Rename Selected Person** (`id_rename_person`) | `F2` | Prompts to rename the currently selected identity. |
| **Delete Selected Person** (`id_del_person`) | `Ctrl` + `D` | Deletes the currently selected identity/identities and rebuilds the model. |
| **Import Identities Package** (`id_import_identities`) | `Ctrl` + `I` | Imports a zip/package of encrypted identities. |
| **Export Selected Identities** (`id_export_identities`) | `Ctrl` + `E` | Exports the selected identities as an encrypted zip archive. |
| **Add Image to Person** (`id_add_image`) | `Ctrl` + `Shift` + `A` | Prompts to add reference photos to the selected identity. |

