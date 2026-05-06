# SafeMARC System Workflows

This document explains exactly how SafeMARC processes files and manages review loops through detailed Mermaid diagrams.

## Document Redaction Workflow

```mermaid
graph TD
    A[Add files to queue] --> B[Click Start Review]
    B --> C{Check File Type}
    
    C -- Image --> D[Scan with face/text detectors]
    C -- PDF --> E[Extract PDF pages into high-fidelity temp images]

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
    A[Face detected by Haar Cascade] --> B{SFace model available?}
    
    B -- Yes --> C[Resize crop to 112×112]
    C --> D[Compute 128-dim SFace embedding]
    D --> E[Compare against all reference embeddings]
    E --> F{Cosine similarity > 0.363?}
    
    F -- Yes --> G["Label: FACE: {name}"]
    F -- No --> H["Label: FACE (unknown)"]
    
    B -- No --> I[LBPH fallback]
    I --> J{Distance < 115?}
    J -- Yes --> G
    J -- No --> H
    
    G --> K{Redaction Mode}
    H --> K
    
    K -- All --> L[Always redacted]
    K -- Blacklist --> M{Identity in target list?}
    K -- Whitelist --> N{Identity in target list?}
    
    M -- Yes --> O[Redacted ✓]
    M -- No --> P[Skipped ✗]
    
    N -- Yes --> Q[Protected ✗]
    N -- No --> R[Redacted ✓]
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
