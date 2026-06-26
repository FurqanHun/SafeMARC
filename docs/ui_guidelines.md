# SafeMARC UI Design Guidelines

To maintain a premium, state-of-the-art visual standard across the SafeMARC application, all new and modified UI elements should strictly adhere to the guidelines outlined below.

## Color Palette

The design utilizes a highly curated dark theme with vibrant emerald and ruby accents to direct user attention.

| Usage | Color Hex | Sample Token |
|---|---|---|
| Window Background | `#0B0F19` | Deeper, rich dark |
| Sidebar & Cards | `#111827` | Soft charcoal/dark gray |
| Secondary Controls | `#1F2937` | Lighter gray for buttons |
| Primary Borders | `#374151` | Premium subtle separation line |
| Selected Focus | `#4B5563` | Accent outline/hover border |
| Primary Accent | `#10B981` | Vibrant emerald green for primary actions |
| Warning Accent | `#E11D48` | Ruby red for destruction or removals |
| Dark Warning | `#BE123C` | Shadow border/focus color for warnings |
| Main Text | `#F3F4F6` | Off-white text |
| Subdued Text | `#9CA3AF` | Light gray text for labels |

## Design Tokens & Typography

1. **Font Families**: Set explicitly to `'Segoe UI', Arial, sans-serif` or standard default system font with letter-spacing for headers.
2. **Font Weight**: 
   - Section Titles/Cards: `700`
   - Actions: `600`
   - Main content labels: `500`
3. **Rounded Corners (`border-radius`)**:
   - High-level containers/Cards: `10px`
   - Secondary controls/Buttons: `8px`
   - Interactive fields/Dropdowns: `6px`

## Control Styling

### Group Boxes & Section Cards

Native `QGroupBox` titles display rendering anomalies across various Linux platforms (such as a black background rectangle behind text). To prevent this, use a flat `QWidget` formatted as a card with an internal heading:

```python
settings_card = QWidget()
settings_card.setObjectName("settingsCard")
settings_card.setStyleSheet("""
    QWidget#settingsCard {
        background-color: #111827;
        border: 1px solid #374151;
        border-radius: 10px;
    }
    QWidget#settingsCard QLabel {
        background: transparent;
    }
""")
```

### SVG Vector Icons

Do not use standard emojis or built-in Qt icons. Instead, utilize raw inline string-based SVGs rendered into a `QIcon` using `QSvgRenderer`. This avoids platform-specific inconsistencies and produces high-end scalable icons:

```python
SVG_SETTINGS = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#F3F4F6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">...</svg>'''
btn_settings.setIcon(svg_to_icon(SVG_SETTINGS))
```

### Premium Visual Feedback & Cursors

1. **Custom Hand Cursors**: To maximize tactile engagement, any interactive component—including buttons, checkboxes, comboboxes, list items, and reference image thumbnail close icons—must be set with a pointing hand cursor:
   ```python
   widget.setCursor(Qt.PointingHandCursor)
   ```
2. **Dynamic Loading Overlays & Dialogs**:
   - For short, in-window processes (like image scanning or identity training), a semi-transparent, dark `LoadingOverlay` containing a custom rotating spinner and clear, user-friendly labels (e.g., *"Scanning document..."*, *"Retraining face recognition model..."*) locks the preview/dialog area.
   - For long-running asynchronous tasks (like PDF page extraction or final PDF compilation), a dedicated `LoadingDialog` modal window is used. It features a matching dark-theme layout, custom fonts, an animated spinner, and a native `QProgressBar` reporting granular page-by-page progress in real-time, preventing the GUI from freezing.
3. **Interactive 1:1 Aspect-Ratio Crop Editor**: When cropping face references inside `FaceCropDialog`, always lock the crop selection to a 1:1 square ratio with responsive, translucent drag handles. The system must also auto-detect the face region via cascades to pre-focus the crop selection for the user.

### Bounding Box Color Coding & Review Suggested States

To make manual review of automatic detections perfectly clear and visual, redactable regions are drawn with color-coded borders and translucent fills:
- **High-Confidence AI Hit / Custom Manual Box** (`confidence` $\ge$ threshold): Solid Ruby Red (`#FF0000`, opacity: 50%, thickness: 3). Automatically selected for redaction.
- **Biometric Known Identity Match**: Solid Emerald Green (`#10B981`, opacity: 50%, thickness: 3) with a floating text label showing the matched person's name.
- **Low-Confidence / Ambiguous Text Match** (falls below the auto-redact cutoff): Solid Amber (`#F59E0B`, opacity: 50%, thickness: 3) if explicitly checked by the user; otherwise, a dashed Amber border (`#F59E0B`, opacity: 15%, thickness: 2) in the "Review Suggested" unchecked state, requesting user confirmation.
- **Deselected Hit**: Dashed Grey (`#646464`, opacity: 0% / transparent fill, thickness: 2). Hit is ignored and will not be redacted when saving.

## Keyboard Focus & Accessibility Guidelines

To prevent visual clutter (such as permanent outlines or focus indicators showing up on mouse-click), focus styling must use property-based attribute selectors rather than the default `:focus` pseudo-class.

1. **Property-Based Focus Styling**:
   Use `[focused_via_keyboard="true"]` in your stylesheet to apply focus indicators (like green borders). Do **not** use the `:focus` selector, which is triggered by mouse clicks:
   ```css
   QPushButton[focused_via_keyboard="true"] {
       border: 2px solid #10B981;
       outline: none;
   }
   ```
2. **Keyboard Focus Tracking**:
   The application installs a global `KeyboardFocusFilter` (event filter) which tracks focus reasons. The property `focused_via_keyboard` is set to `"true"` if the widget was focused via keyboard (`Tab`, `Shift+Tab`, or shortcut) and `"false"` otherwise.
3. **Escaping Focus**:
   When keyboard focus is active, pressing the `Escape` key clears focus and returns focus back to the top-level main window container. This clears all focus outlines without triggering destructive shortcuts (like stopping the review process).
4. **Initial Focus Prevention**:
   To avoid initial buttons (like Settings) stealing focus on window opening, windows call `self.setFocus()` on startup. This ensures that no button is focused by default, and pressing `Enter` initially will not trigger unintended clicks.
