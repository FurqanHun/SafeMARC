# SafeMARC Keyboard Shortcuts

SafeMARC's keyboard-driven workflow enables highly efficient document review. All keyboard shortcuts listed below are fully customizable and rebindable to your preferred key combinations in **Settings** (`Ctrl` + `,`) under the **Shortcuts** tab. Custom combinations persist across application restarts.

## General Shortcuts
| Action | Shortcut | Description |
|---|---|---|
| **Toggle Draw Mode** | `D` | Switches the pointer to Draw mode to manually draw a custom redaction box. |
| **Toggle Persistent Mode** | `Shift` + `D` | Switches pointer to Draw mode and prompts for persistent propagation scope (propagates manual boxes across pages/files). |
| **Add Files** | `Ctrl` + `O` | Add files to the review queue. |
| **Add Folder** | `Ctrl` + `Shift` + `O` | Add a whole folder of files to the review queue. |
| **Remove Selected File** | `Delete` | Remove the currently selected file from the queue. |
| **Clear Queue** | `Ctrl` + `Shift` + `C` | Clears all files in the queue. |
| **Settings** | `Ctrl` + `,` | Opens the settings panel. |
| **Paste from Clipboard** | `Ctrl` + `V` | Pastes an image from the system clipboard as a temporary review item. |
| **Rescan current file** | `F5` | Re-scans the currently active file with current settings and filters. |
| **Reset Layout** | `Ctrl` + `Alt` + `R` | Resets the three-pane window divider splitters back to their default balanced sizes. |

## Zoom & Pan Shortcuts
| Action | Shortcut | Description |
|---|---|---|
| **Zoom In** | `Ctrl` + `=` or `Ctrl` + `+` | Enlarges the preview image centered on the mouse cursor. |
| **Zoom Out** | `Ctrl` + `-` | Shrinks the preview image centered on the mouse cursor. |
| **Reset Zoom** | `Ctrl` + `0` | Immediately resets the view to default aspect ratio and fits it in the window. |
| **Scroll Zoom** | `Ctrl` + Mouse Wheel Up/Down | Quick zooming in and out. |
| **Pan Image** | Mouse Click & Drag | Drag in the preview area to pan when zoomed in. |

## Sensitive Box Navigation
| Action | Shortcut | Description |
|---|---|---|
| **Focus Next Box** | `Right Arrow` | Cycles keyboard focus forward to the next detected sensitive box on the page. |
| **Focus Previous Box** | `Left Arrow` | Cycles keyboard focus backward to the previous sensitive box on the page. |
| **Toggle Selected State** | `C` or `Space` (if box is focused) | Toggles the checked/unchecked state of the currently focused sensitive box. |

## Batch Review Workflow
| Action | Shortcut | Description |
|---|---|---|
| **Start Review** | `Shift+Return` or `Shift+Enter` | Starts the batch review process. |
| **Redact & Next** | `Shift+Return` or `Shift+Enter` | Processes redaction on the current file and loads the next item. |
| **Skip Item** | `Space` or `S` | Skips the current file and loads the next item. |
| **Previous Item** | `Backspace` or `P` | Returns to the previous file/page in the queue. |
| **Stop Review** | `Escape` | Cancels the active batch review. Note: If keyboard focus is active, pressing `Escape` clears the highlight first; pressing it a second time stops the review. |

## Pattern Input Fields (Text & Regex)
| Action | Shortcut | Description |
|---|---|---|
| **Save & Exit Input** | `Enter` or `Return` | Saves the typed pattern and unfocuses (exits) the text box, preventing accidental advancement of the batch review. |
| **Add New Input Row** | `Shift` + `Enter` | Creates a new text or regex pattern input field of the same type and automatically focuses it. |

## Biometric Identity Editor
| Action | Shortcut | Description |
|---|---|---|
| **Multi-Select** | `Ctrl` + Mouse Click / `Shift` + Mouse Click | Selects multiple identities inside the left pane. |
| **Select All** | `Ctrl` + `A` | Selects all identities inside the left pane. |
