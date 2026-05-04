# SafeMARC System Workflows

This document explains exactly how SafeMARC processes files and manages review loops through detailed Mermaid diagrams.

## Document Redaction Workflow

```mermaid
graph TD
    A[Add files to queue] --> B[Click Start Review]
    B --> C{Check File Type}
    
    C -- Image --> D[Extract image and perform text/face scan]
    C -- PDF --> E[Extract PDF pages into high-fidelity temp images]

    D --> F[Show interactive preview with toggleable boxes]
    E --> F

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

## Processing & Redaction Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor User as Reviewer
    participant UI as Desktop MainWindow
    participant Sc as SafeScanner
    participant Ph as PDFHandler
    participant Rd as Redactor

    User->>UI: Click "Start Review"
    alt Is PDF File
        UI->>Ph: extract_pages(file_path)
        Ph-->>UI: List of temp page paths
        loop For each page in PDF
            UI->>Sc: scan(page_path)
            Sc-->>UI: List of sensitive hits
            User->>UI: Confirm / draw boxes
            User->>UI: Click "Redact Next"
            UI->>Rd: apply(page_path, temp_output, selected_hits)
            Rd-->>UI: Done
        end
        UI->>Ph: build_pdf(temp_outputs, out_path)
        Ph-->>UI: Final sanitized PDF
    else Is Image File
        UI->>Sc: scan(file_path)
        Sc-->>UI: List of sensitive hits
        User->>UI: Confirm / draw boxes
        User->>UI: Click "Redact Next"
        UI->>Rd: apply(file_path, out_path, selected_hits)
        Rd-->>UI: Final sanitized image
    end
    UI->>User: Update queue status (green/grey)
```
