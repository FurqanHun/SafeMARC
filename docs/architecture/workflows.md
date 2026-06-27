# SafeMARC System Workflows

This document explains exactly how SafeMARC processes files and manages review loops through detailed Mermaid diagrams.

## Document Redaction Workflow

```mermaid
graph TD
    A[Add files to queue] --> B[Click Start Review]
    B --> C{Check File Type}
    
    C -- Image --> D1{Hit in Session Cache?}
    C -- PDF --> E[Extract PDF pages into high-fidelity temp images]
    
    E --> D1
    D1 -- Yes --> F2[Load Cached Hits Instantly]
    D1 -- No --> D[Scan with face/text detectors & Update Cache]

    D --> F1{Face Mode?}
    E --> F1

    F1 -- All --> F2[Show all detected hits]
    F1 -- Blacklist --> F3[Match faces via SFace → show only targeted identities]
    F1 -- Whitelist --> F4[Match faces via SFace → hide targeted, show rest]

    F2 --> F[Show interactive preview with toggleable boxes]
    F3 --> F
    F4 --> F

    F --> G{User Action}
    G -- Redact Next --> H{Is it a PDF?}
    G -- Skip --> I{Is it a PDF?}
    G -- Go Previous --> P{Re-entering completed PDF?}
    G -- Change Spinbox / Jump Page --> S[Save selections to Cache & Load target page]
    
    S --> D1
    
    P -- Yes --> Q[Prompt User: Restart PDF from Page 1?]
    Q -- Yes --> E
    P -- No --> R[Load previous item or page]
    R --> D1
    
    H -- No --> H_IMG[Burn redactions & save to output file]
    H -- Yes --> H_PDF{Is it the last page?}
    H_PDF -- No --> H_NEXT[Save selections to Cache & Load next page] --> D1
    H_PDF -- Yes --> FIN[Trigger background PDF compilation finalization]
    
    I -- No --> J[Mark as skipped / grey out in queue]
    I -- Yes --> K{Prompt User: Skip Page, Skip Remaining, or Entire PDF?}
    K -- Skip Page --> L{Is it the last page?}
    L -- No --> L_NEXT[Save selections to Cache & Load next page] --> D1
    L -- Yes --> FIN
    K -- Skip Remaining --> M[Fast-forward index, skip unvisited, & trigger compile] --> FIN
    K -- Entire PDF --> J

    H_IMG --> NEXT_QUEUE{More items in queue?}
    FIN --> NEXT_QUEUE
    J --> NEXT_QUEUE

    NEXT_QUEUE -- Yes --> N[Move to next queue item]
    N --> C
    NEXT_QUEUE -- No --> O[Processing complete]
```

---

## Face Identity Recognition Workflow

```mermaid
graph TD
    A[Run Multi-Scale YuNet DNN Detection] --> B[Containment-Ratio NMS]
    B --> C{SFace model available?}
    
    C -- Yes --> D[alignCrop using YuNet 5 facial landmarks]
    D --> E[Compute 128-dim SFace embedding]
    E --> F[Compare against all reference embeddings]
    F --> G{Cosine similarity >= 0.40 & tiered margin check?}
    
    G -- Yes --> H["Label: FACE: {name}"]
    G -- No --> I["Label: FACE (unknown)"]
    
    C -- No --> J[Crop Face via bounding box]
    J --> K[LBPH fallback on 150×150 crop]
    K --> L{Distance < 115?}
    L -- Yes --> H
    L -- No --> I
    
    H --> RM{Redaction Mode}
    I --> RM
    
    RM -- All --> RED[Always redacted]
    RM -- Blacklist --> BL{Identity in target list?}
    RM -- Whitelist --> WL{Identity in target list?}
    
    BL -- Yes --> RED1[Redacted ✓]
    BL -- No --> SKP1[Skipped ✗]
    
    WL -- Yes --> PRT[Protected ✗]
    WL -- No --> RED2[Redacted ✓]
```

---

## Body Detection & Face-Body Hybrid Mapping Workflow

```mermaid
graph TD
    A[Image Input] --> CL{Mean Gray Brightness < 90?}
    CL -- Yes --> CL_APPLY[Apply CLAHE to L channel of LAB image] --> B
    CL -- No --> B{Max Dim < 640px?}
    
    B -- Yes --> C[2x linear upscaling] --> D
    B -- No --> D{Image Size / Max Dim?}
    
    D -- "> 5000 px" --> E1[4 × 3 Tiling Grid]
    D -- "3001 – 5000 px" --> E2[3 × 3 Tiling Grid]
    D -- "1201 – 3000 px" --> E3[2 × 2 Tiling Grid]
    D -- "≤ 1200 px" --> E4[1 × 1 Global Pass]
    
    E1 --> F[Run EfficientDet-Lite2 on tiles]
    E2 --> F
    E3 --> F
    E4 --> F
    
    F --> G[Category Filter: Keep 'person' only, drop 'face']
    G --> H[Translate tile coords to absolute coordinates]
    H --> I[Standard IoU NMS: threshold 0.55]
    
    I --> J{Sliver Filter: height >= width * 0.5?}
    J -- No --> K[Discard hit]
    J -- Yes --> L[Map face box containment inside body box]
    
    L --> M{Face has recognized identity?}
    M -- Yes --> N[Assign identity to body box SensitiveHit]
    M -- No --> O[Keep body box identity empty]
    
    N --> P[Face-Guided Recovery: Generate synthetic body box for uncovered targeted faces]
    O --> P
    
    P --> Q[Depth-Ordered Clipping: Trim back-row boxes overlapping front faces]
    Q --> R[Final Sliver Filter: height >= width * 0.5 check]
    R --> S[Apply Redaction Mode: Blacklist/Whitelist/All]
```

---

## Hybrid Digital & OCR Text Detection Workflow

```mermaid
graph TD
    A[Image/PDF Input] --> B{Cache check: Has this file/page been scanned?}
    B -- Yes --> C[Load cached text hits instantly]
    B -- No --> D{Are digital PDF words available?}
    
    D -- Yes --> E[Map digital PDF words coordinates to scale 1.0]
    E --> F[Run regex & text pattern matching on digital line texts]
    F --> G[Extract word boundaries & calculate initial hits]
    
    D -- No --> H[Image File Path]
    G --> H
    
    H --> I[Read image in Grayscale]
    I --> J[2x upscale using linear interpolation]
    J --> K[Apply Otsu's thresholding to binarize image]
    K --> L[Restore LD_LIBRARY_PATH environment context]
    L --> M[Run Tesseract OCR image_to_data --psm 3]
    M --> N[Map OCR word bounds & scale coordinates down by 2.0]
    N --> O[Run regex & text pattern matching on OCR line texts]
    
    O --> P[Pool digital hits + OCR hits]
    P --> Q{Validation & Confidence Boosting Heuristics}
    
    Q -- "Credit Card" --> R1{Validate Luhn Algorithm Checksum}
    R1 -- Pass --> S1[Assign confidence 95%]
    R1 -- Fail --> S2[Discard hit]
    
    Q -- "EU IBAN" --> R2{Validate ISO 7064 Mod-97 Checksum}
    R2 -- Pass --> T1[Assign confidence 95%]
    R2 -- Fail --> T2[Discard hit]
    
    Q -- "US SSN / IN Aadhaar" --> R3{Context Keywords Proximity check within ±35 chars}
    R3 -- Yes --> U1[Assign confidence 90%]
    R3 -- No --> U2[Assign confidence 25% review-suggested]
    
    Q -- "Other Pattern (with Keywords)" --> R4{Context Keywords Proximity check within ±35 chars}
    R4 -- Yes --> V1[Assign confidence 90%]
    R4 -- No --> V2[Assign confidence 30% review-suggested]
    
    S1 --> W[Area-Overlap IoU Deduplication]
    T1 --> W
    U1 --> W
    U2 --> W
    V1 --> W
    V2 --> W
    
    W --> X{Overlap ratio with other hit > 0.40?}
    X -- Yes --> Y[Keep the hit with higher confidence, discard other]
    X -- No --> Z[Keep both hits]
    
    Y --> AA[Final SensitiveHit List]
    Z --> AA
    AA --> AB[Cache final text hits]
```

---

## Processing & Redaction Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor User as Reviewer
    participant UI as Desktop MainWindow
    participant LD as LoadingDialog
    participant EW as PDFExtractWorker
    participant FW as PDFFinalizeWorker
    participant Sc as SafeScanner
    participant IM as IdentityManager
    participant VD as VisionDetector
    participant Ph as PDFHandler
    participant Rd as Redactor

    User->>UI: Click "Start Review"
    alt Is PDF File
        UI->>EW: QTimer.singleShot(50ms) → PDFExtractWorker.start()
        note over UI,EW: 50ms deferral gives the window manager time to fully map LoadingDialog before heavy I/O begins, eliminating visual ghosting artifacts
        loop For each page extracted
            EW-->>UI: progress(current, total)
            note over EW: time.sleep(0.01) per iteration yields GIL to GUI thread, keeping QProgressBar and spinner responsive
            UI->>LD: update_progress()
        end
        EW-->>UI: finished(pages)
        UI->>LD: close()
        loop For each page in PDF
            UI->>Sc: scan(page_path)
            Sc->>VD: detect(page_path, match_identities)
            alt If match_identities is True
                loop For each detected face
                    VD->>IM: match_face_aligned(full_img, det_row, num_faces)
                    IM-->>VD: identity or None
                end
            end
            VD-->>Sc: List of hits with identities
            Sc->>Sc: Filter by face_redaction_mode
            Sc-->>UI: Filtered hits
            User->>UI: Confirm / draw boxes / navigate
            UI->>UI: Cache manual & selected hits for page
        end
        User->>UI: Click "Redact Next" on final page / "Skip Remaining Pages"
        UI->>FW: QTimer.singleShot(50ms) → PDFFinalizeWorker.start()
        note over UI,FW: Same 50ms deferral ensures LoadingDialog is fully painted before compilation begins
        loop For each visited/reviewed page in PDF
            FW->>Rd: apply(page_path, temp_output, selected_hits)
            Rd-->>FW: Done
            FW-->>UI: progress(current, total)
            note over FW: time.sleep(0.01) per page yields GIL, keeping progress dialog responsive
            UI->>LD: update_progress()
        end
        FW->>Ph: build_pdf(temp_outputs, out_path)
        Ph-->>FW: Final sanitized PDF
        FW-->>UI: finished(success, outputs)
        UI->>LD: close()
    else Is Image File
        UI->>Sc: scan(file_path)
        Sc->>VD: detect(file_path, match_identities)
        alt If match_identities is True
            loop For each detected face
                VD->>IM: match_face_aligned(full_img, det_row, num_faces)
                IM-->>VD: identity or None
            end
        end
        VD-->>Sc: List of hits with identities
        Sc->>Sc: Filter by face_redaction_mode
        Sc-->>UI: Filtered hits
        User->>UI: Confirm / draw boxes
        User->>UI: Click "Redact Next"
        UI->>Rd: apply(file_path, out_path, selected_hits)
        Rd-->>UI: Final sanitized image
    end
    UI->>User: Update queue status (green/grey)
```

---

## Identity Quick-Add Workflow

```mermaid
sequenceDiagram
    autonumber
    actor User as Reviewer
    participant UI as PreviewWidget
    participant MW as MainWindow
    participant IM as IdentityManager

    User->>UI: Right-click detected face box
    UI->>UI: Show context menu "Add as Known Identity..."
    User->>UI: Click action
    UI->>MW: identityRequested signal (SensitiveHit)
    MW->>User: Prompt for name
    User->>MW: Enter name
    MW->>User: Prompt save type (Permanent / Session)
    User->>MW: Choose type
    MW->>MW: Crop face from original image
    alt Permanent
        MW->>IM: add_identity(name, [crop_path])
    else Session Only
        MW->>IM: add_session_identity(name, crop_path)
    end
    IM->>IM: reload_identities() → retrain SFace embeddings
    MW->>MW: Rescan current image with updated identities
```

---

## Reference Photo Cropping & Biometric Training Workflow

```mermaid
sequenceDiagram
    autonumber
    actor User as Reviewer
    participant SD as SettingsDialog
    participant CD as FaceCropDialog
    participant IM as IdentityManager

    User->>SD: Click "Add Image"
    SD->>User: Select raw reference photos
    loop For each selected file
        SD->>SD: Show "Loading & detecting face..." status
        SD->>CD: Open FaceCropDialog
        CD->>CD: Run YuNet DNN to pre-focus crop box
        User->>CD: Adjust crop selection and click Save
        CD-->>SD: cropped_image
    end
    SD->>SD: Enable Wait Cursor & Disable Window
    SD->>SD: Show "Retraining face recognition model..." status
    alt Permanent Identity
        SD->>IM: add_identity(name, crops)
    else Session-Only Identity
        SD->>IM: add_session_identity(name, crops)
    end
    IM->>IM: reload_identities() → generate SFace .npy files
    SD->>SD: Restore normal cursor & Enable Window
    SD->>SD: Clear status label and refresh thumbnails
```

---

## Persistent Custom Bounding Box Smart Range Scope Workflow

```mermaid
sequenceDiagram
    autonumber
    actor User as Reviewer
    participant UI as PreviewWidget
    participant MW as MainWindow
    participant PD as PersistentRangeDialog

    User->>MW: Click "Persistent Boxes" (pin tool)
    MW->>PD: Open dialog (is_pdf context)
    User->>PD: Select Scope (e.g., current_pdf_only, all_upcoming) and click Apply
    PD-->>MW: selected_scope
    MW->>UI: set_persistent_mode(True, scope, pdf_source)
    UI->>UI: Capture currently visible manual boxes into persistent cache

    loop For each subsequent page / file loaded
        MW->>UI: load_image(file_path)
        MW->>UI: display_hits(hits, is_pdf, pdf_source)
        alt Selected Scope Matches Context
            UI->>UI: Inject cached persistent coordinates onto active hits
        end
        UI-->>User: Render merged auto-detected + persistent manual redactions
    end
```

---

## Unified Temp Resource Lifecycle & Exit Routines

```mermaid
graph TD
    A[Launch Application] --> B[Startup Cleanup: Purge Leftover safemarc_temp]
    B --> C[Application Active]
    
    C --> D[Clipboard Paste] --> E[Save to safemarc_temp/clipboard]
    C --> F[PDF Scan] --> G[Extract to safemarc_temp/pdf]
    C --> H[Add Session Identity] --> I[Save to safemarc_temp/session_temp]
    
    C --> J[Click Start Review]
    J --> K[Keep session scan cache intact for instant loading]
    
    C --> L[Cancel Batch Review]
    L --> M[cleanup_temp_resources full=False]
    M --> N[Purge PDF and Redacted temps, Keep Clipboard & Session temps]
    
    C --> O[App Close / Ctrl+C]
    O --> P[PySide6 handle_sigint / Exit]
    P --> Q[RAII try-finally Guard]
    Q --> R[cleanup_temp_resources full=True]
    R --> S[Completely destroy safemarc_temp]
```


---

## Checkbox Selections Persistence & Manual Box Restoration Workflow

```mermaid
sequenceDiagram
    autonumber
    actor User as Reviewer
    participant MW as MainWindow
    participant PW as PreviewWidget
    participant SC as User Selections Cache

    User->>MW: Click "Redact Next", "Skip", "Previous", or "F5"
    MW->>PW: Query currently displayed active hits
    PW-->>MW: active_hits (includes manual & AI selections)
    MW->>SC: Save active_hits to user_selections_cache[current_file_path]
    
    note over MW,SC: Cache holds exact checkbox selections & manually drawn shapes
    
    MW->>MW: Load next/target document / trigger scan
    MW->>SC: Get cached selections for target path
    SC-->>MW: cached_active_hits (or None)
    
    MW->>PW: display_hits(new_scan_hits, cached_active_hits)
    
    alt cached_active_hits is not None
        loop For each new scan hit
            PW->>PW: Match coordinates and label against cached_active_hits
            alt Match Found
                PW->>PW: Keep Checked state / Add to active_hits
            else Match Not Found
                PW->>PW: Leave Unchecked / Exclude from active_hits
            end
        end
        loop For each cached hit
            alt Hit is "MANUAL" and not in new scan
                PW->>PW: Inject and check manual box on preview canvas
            end
        end
    else Default / Pre-Review State
        PW->>PW: Apply model confidence thresholds to auto-check scan hits
        loop For each cached hit
            alt Hit is "MANUAL"
                PW->>PW: Inject and check manual box
            end
        end
    end
    PW-->>User: Display fully restored selections & manual shapes
```

---

## Keyboard Focus & Tabbing Mode Lifecycle Workflow

```mermaid
graph TD
    A[Enter Batch Review / Load Next Item] --> B[Clear any auto-relocated focus & setFocus to MainWindow]
    B --> C{User presses Tab?}
    C -- No --> D[No widget focused / Pressing Enter does not trigger buttons]
    C -- Yes --> E[Focus first/next interactive widget & set focused_via_keyboard = true]
    E --> F[Show green focus indicator border]
    F --> G{User presses Enter/Return?}
    G -- Yes --> H[Trigger focused widget action]
    G -- No --> I{User presses Escape?}
    I -- Yes --> J[Clear focus & call setFocus to MainWindow / Exit Tabbing Mode]
    J --> B
```


## Identity Renaming Workflow

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant SD as SettingsDialog
    participant IM as IdentityManager

    User->>SD: Double-click name OR press F2 / click ✎ button
    SD->>User: Prompt for new name (QInputDialog)
    alt User clicks Cancel or enters empty/whitespace name
        SD-->>User: Exit without changes
    else User enters valid name
        SD->>SD: Sanitize name & strip path characters
        alt New name matches old name
            SD-->>User: Exit without changes
        else New name already exists in list (collision)
            SD->>User: Show warning dialog (Name already exists)
        end
        SD->>SD: Move old identity directory to new path
        SD->>IM: reload_identities()
        IM->>IM: Retrain face recognition model
        SD->>SD: _refresh_people_list()
        SD->>SD: Select new name in list & set focus
    end
```

---

## Identity Export & Import Workflow

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant SD as SettingsDialog
    participant CRYP as crypto.py (Standard Library)
    participant IM as IdentityManager
    
    opt Export Process
        Note over User, CRYP: Export Workflow
        User->>SD: Click Export Button
        SD->>SD: Get permanent identities list (filtered/selected)
        SD->>User: Prompt for Save File Path (.smid)
        SD->>User: Prompt for password (QInputDialog)
        SD->>SD: Zip raw reference photos to in-memory bytes
        SD->>CRYP: encrypt_data(zip_bytes, password)
        CRYP->>CRYP: Derive key via PBKDF2-HMAC-SHA256 (100k iter)
        CRYP->>CRYP: XOR encrypt via SHA-256 CTR Mode
        CRYP-->>SD: return salt + ciphertext bytes
        SD->>SD: Save encrypted bytes to disk
        SD-->>User: Show Export Success dialog
    end

    opt Import Process
        Note over User, IM: Import Workflow
        User->>SD: Click Import Button
        SD->>User: Prompt to select .smid file
        SD->>User: Prompt for password
        SD->>CRYP: decrypt_data(file_bytes, password)
        CRYP->>CRYP: Extract salt & derive key
        CRYP->>CRYP: XOR decrypt ciphertext
        CRYP-->>SD: return decrypted bytes
        SD->>SD: Verify ZIP magic header PK\x03\x04
        SD->>SD: Extract ZIP to temp directory (Zip Slip path validation)
        loop For each valid identity folder
            SD->>SD: Copy reference images to identities storage
        end
        SD->>IM: reload_identities()
        IM->>IM: Reload & retrain recognition models (SFace/LBPH)
        SD->>SD: Refresh identities list view
        SD-->>User: Show Import Success dialog
    end
```

---

## Custom Patterns Export & Import Workflow

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant MW as MainWindow
    participant CRYP as crypto.py (Standard Library)
    
    opt Export Process
        Note over User, CRYP: Export Workflow
        User->>MW: Click Export Button
        MW->>MW: Gather custom patterns from text_patterns_layout
        MW->>User: Prompt for Export Format (smpat / json)
        alt Encrypted Format (.smpat)
            MW->>User: Prompt for Save File Path (.smpat)
            MW->>User: Prompt for Password (QInputDialog)
            MW->>MW: Serialize patterns to JSON & encode to UTF-8
            MW->>CRYP: encrypt_data(json_bytes, password)
            CRYP->>CRYP: Derive key via PBKDF2-HMAC-SHA256 (100k iter)
            CRYP->>CRYP: XOR encrypt via SHA-256 CTR Mode
            CRYP-->>MW: return salt + ciphertext bytes
            MW->>MW: Save encrypted bytes to disk
        else Unencrypted Format (.json)
            MW->>User: Prompt for Save File Path (.json)
            MW->>MW: Write raw serialized JSON to disk
        end
        MW-->>User: Show Export Success dialog
    end

    opt Import Process
        Note over User, CRYP: Import Workflow
        User->>MW: Click Import Button
        MW->>User: Prompt to select .smpat or .json file
        alt Selected Encrypted (.smpat)
            MW->>User: Prompt for Password
            MW->>CRYP: decrypt_data(file_bytes, password)
            CRYP->>CRYP: Extract salt & derive key
            CRYP->>CRYP: XOR decrypt ciphertext
            CRYP-->>MW: return decrypted bytes
            MW->>MW: UTF-8 decode & parse JSON (validates password correct)
        else Selected Unencrypted (.json)
            MW->>MW: Read & parse raw JSON file directly
        end
        MW->>MW: Clear existing layout & recreate pattern rows
        MW-->>User: Show Import Success dialog
    end
```
