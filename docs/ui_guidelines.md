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
