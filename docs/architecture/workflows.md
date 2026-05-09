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
    G -- Redact Next --> H[Burn redactions & save to output file]
    G -- Skip --> I{Is it a PDF?}
    
    I -- No --> J[Mark as skipped / grey out in queue]
    I -- Yes --> K[Prompt User: Skip Page or Skip entire PDF?]
    K -- Page --> L[Keep current page unchanged & move to next page]
    K -- PDF --> J

    H --> M{More items in queue?}
    J --> M
    L --> M

    M -- Yes --> N[Move to next queue item]
    N --> C
    M -- No --> O[Processing complete]
```

---

## Face Identity Recognition Workflow

```mermaid
graph TD
    A[Run Ensemble Cascades: Frontal + Alt Frontal + Profile + Flipped Profile] --> B[Union-NMS Bounding Box Merging]
    B --> C[Crop Face with Safe Slicing]
    C --> D{SFace model available?}
    
    D -- Yes --> E[Resize crop to 112×112]
    E --> F[Compute 128-dim SFace embedding]
    F --> G[Compare against all reference embeddings]
    G --> H{Cosine similarity > 0.363?}
    
    H -- Yes --> I["Label: FACE: {name}"]
    H -- No --> J["Label: FACE (unknown)"]
    
    D -- No --> K[LBPH fallback]
    K --> L{Distance < 115?}
    L -- Yes --> I
    L -- No --> J
    
    I --> RM{Redaction Mode}
    J --> RM
    
    RM -- All --> RED[Always redacted]
    RM -- Blacklist --> BL{Identity in target list?}
    RM -- Whitelist --> WL{Identity in target list?}
    
    BL -- Yes --> RED1[Redacted ✓]
    BL -- No --> SKP1[Skipped ✗]
    
    WL -- Yes --> PRT[Protected ✗]
    WL -- No --> RED2[Redacted ✓]
```

---

## Processing & Redaction Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor User as Reviewer
    participant UI as Desktop MainWindow
    participant Sc as SafeScanner
    participant IM as IdentityManager
    participant VD as VisionDetector
    participant Ph as PDFHandler
    participant Rd as Redactor

    User->>UI: Click "Start Review"
    alt Is PDF File
        UI->>Ph: extract_pages(file_path)
        Ph-->>UI: List of temp page paths
        loop For each page in PDF
            UI->>Sc: scan(page_path)
            Sc->>VD: detect(page_path, match_identities)
            alt If match_identities is True
                loop For each detected face
                    VD->>IM: match_face(face_crop)
                    IM-->>VD: identity or None
                end
            end
            VD-->>Sc: List of hits with identities
            Sc->>Sc: Filter by face_redaction_mode
            Sc-->>UI: Filtered hits
            User->>UI: Confirm / draw boxes
            User->>UI: Click "Redact Next"
            UI->>Rd: apply(page_path, temp_output, selected_hits)
            Rd-->>UI: Done
        end
        UI->>Ph: build_pdf(temp_outputs, out_path)
        Ph-->>UI: Final sanitized PDF
    else Is Image File
        UI->>Sc: scan(file_path)
        Sc->>VD: detect(file_path, match_identities)
        alt If match_identities is True
            loop For each detected face
                VD->>IM: match_face(face_crop)
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
        CD->>CD: Run robust ensemble to pre-focus crop box
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
    J --> K[Clear scanner vision cache]
    
    C --> L[Cancel Batch Review]
    L --> M[cleanup_temp_resources full=False]
    M --> N[Purge PDF and Redacted temps, Keep Clipboard & Session temps]
    
    C --> O[App Close / Ctrl+C]
    O --> P[PySide6 handle_sigint / Exit]
    P --> Q[RAII try-finally Guard]
    Q --> R[cleanup_temp_resources full=True]
    R --> S[Completely destroy safemarc_temp]
```

