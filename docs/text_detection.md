# SafeMARC — Text Detection & PII Matching System

This document covers SafeMARC's text extraction pipeline (how raw text and its exact page coordinates are obtained) and its PII matching system (how patterns, heuristics, and confidence scoring identify sensitive content in that text).

---

## 1. OCR & Text Extraction — Tools Evaluated

### 1.1 Tools Evaluated and Rejected

#### Microsoft Presidio

Microsoft **Presidio** (`presidio-analyzer`) was evaluated during planning as a high-level PII detection framework. It combines NLP (spaCy models) with regex and ML classifiers to detect named entities (names, locations, organisations) alongside structured PII (credit card numbers, SSNs, etc.).

**Why it was not adopted:**

- **Heavy system requirements** — Presidio requires spaCy language models (100 MB+) and has a significant startup cost. For an offline desktop tool this is a poor trade-off vs. a curated regex library.
- **Black-box confidence** — Presidio's ML-driven entity recognition produces confidence scores that are difficult to explain to users or tune for a specific document domain. The project's approach of explicit regex + keyword proximity scoring is more transparent and auditable.
- **No coordinate output** — Presidio works on raw text strings and does not produce bounding-box coordinates. SafeMARC needs exact page coordinates to draw redaction boxes; this would have required a separate mapping step and re-introduces the coordinate synchronisation problem.
- **Scope mismatch** — Presidio is designed for NLP pipelines on unstructured text (call transcripts, emails). SafeMARC's primary domain is structured PDFs and scanned documents where regex is highly accurate and far lighter.

Presidio remains a valid future option for unstructured text use cases and may be exposed as an optional backend in a later settings panel (see §4).

#### EasyOCR

**EasyOCR** was evaluated as an alternative OCR engine. It uses deep learning (CRAFT text detection + CRNN recognition) and supports 80+ languages and non-Latin scripts with good accuracy on handwritten and stylised fonts.

**Why it was deferred (not rejected):**

- **Scope vs. effort** — SafeMARC's current focus is formal documents (PDFs, typed scans) where Tesseract with Otsu binarisation already performs well. EasyOCR's main advantages (handwriting, decorative fonts, curved text) are not relevant to this phase.
- **GPU dependency for speed** — EasyOCR on CPU is significantly slower than Tesseract for multi-page documents; GPU acceleration requires CUDA setup which cannot be assumed in the target environment.
- **Diminishing returns in phase 1** — adding EasyOCR would cost integration time with marginal accuracy benefit for the current document corpus.

EasyOCR is explicitly deferred to a future settings option (see §4), not ruled out. For handwritten records, non-Latin documents, or forms with decorative fonts, it is the more capable choice.

#### LLM-Based OCR

Multimodal LLMs and document-understanding models were discussed at various points in development. Several specific candidates were evaluated:

**DeepSeek OCR (DeepSeek document understanding)**

DeepSeek's document-understanding research demonstrated strong OCR accuracy on degraded scans, mixed-language documents, and dense layouts. The self-hosting option was briefly considered (the user runs their own model server locally), but this was rejected:

- **General audience assumption** — SafeMARC is designed for non-technical users. Requiring someone to set up and run a local model inference server (Ollama, vLLM, etc.) is not a reasonable installation requirement for a desktop privacy tool.
- **Even self-hosted = GPU hardware** — a capable DeepSeek document model requires several gigabytes of VRAM to run at interactive speed. The vast majority of the target user base (office workers, NGOs, legal professionals) will not have a GPU-capable machine.
- **Offline guarantee complexity** — a "self-hosted" model still requires the user to download a multi-GB model file and manage a running service, which violates the spirit of SafeMARC's one-click local-only design.

**Baidu Unlimited-OCR**

Unlimited-OCR was released by Baidu approximately one week before this writing (late June 2026) and showed impressive benchmark results on multi-language and handwritten document recognition. It was noted as interesting but ultimately faces the same barriers:

- Same hardware and hosting requirements as above.
- It arrived too late in the development cycle to be meaningfully evaluated or integrated for phase 1 — the architecture and document pipeline were already finalised.
- Still cloud-dependent in its standard form; self-hosted deployment carries the same general-audience friction as DeepSeek.

**General rejection rationale for all LLM/VLM OCR approaches**

The shared rejection reason across all these models is a design constraint, not a quality judgement:

> *SafeMARC is a general-audience application. Users should not need to operate a model server, provision GPU hardware, or manage multi-GB downloads beyond the existing asset files. Any OCR backend that requires infrastructure the user cannot install with a single `pip install` or system package command is out of scope for phase 1.*

These models remain viable candidates for a future "power user" or enterprise mode where self-hosted inference is an acceptable expectation (see §4).

---

### 1.2 Tesseract — Chosen and Retained

**Tesseract** (via `pytesseract`) is the OCR engine used for all image-based text extraction. It is:

- Fully local and offline.
- Mature and battle-tested on printed documents.
- Available on all target platforms via system package managers.
- Compatible with `pytesseract_env()`, SafeMARC's cross-platform Tesseract binary location helper (`src/utils/paths.py`), which also supports PyInstaller frozen-binary environments.

Tesseract is only invoked for rasterised content (scanned pages, image-only PDFs). For native PDFs, PyMuPDF's direct word extraction is used instead (§2.2).

---

## 2. Current Text Extraction Pipeline

### 2.1 Evolution of the Pipeline

#### Generation 1 — Tesseract-only (`92c3dfd`, `5ee2279`)

The initial implementation rasterised every page to an image and ran Tesseract on it regardless of whether the PDF had embedded text. This was simple but wasteful for native PDFs where coordinate-accurate text was already available without OCR.

Tesseract configuration at this stage used default settings with no resolution scaling.

#### Generation 2 — OCR Optimisation (`bfb9e80`)

Two targeted improvements were made after observing missed detections in low-contrast scans:

1. **2× upscale before OCR** — the page image is scaled to 2× resolution using `cv2.INTER_CUBIC` before being passed to Tesseract. This dramatically improves Tesseract's character segmentation on small-font text (sub-12pt) and faint prints.
2. **Otsu binarisation** — after upscaling, an Otsu threshold converts the grayscale image to clean black-and-white. This removes background gradients, watermarks, and scanning noise that Tesseract reads as garbled characters.
3. **PSM 3 (fully automatic page segmentation)** — `--psm 3` was set explicitly to let Tesseract determine page layout automatically rather than assuming a single column, improving detection on multi-column layouts.

#### Generation 3 — Hybrid PyMuPDF + Tesseract with Caching (`1f543ef`, `dbe17a4`)

The critical architectural change: **use PyMuPDF native word extraction as the primary path**, with Tesseract as a fallback for image content.

```
For each page:
  ├── PyMuPDF page.get_text("words")
  │     Returns: [(x0, y0, x1, y1, word, block_no, line_no, word_no), ...]
  │     Available: only for PDFs with embedded text layer
  │     Accuracy: perfect coordinate alignment, 100% confidence
  │
  └── Tesseract OCR on rasterised page image (always runs as supplemental pass)
        Returns: pytesseract image_to_data dict (word, x, y, w, h, conf)
        Available: always
        Purpose: catches text in image regions, stamps, signatures, scanned overlays
```

Both passes are run and their hits are merged. A hit from the PyMuPDF pass for the same word always wins (100% conf) over the equivalent OCR hit, with IoU-based deduplication removing duplicates from the merged pool.

**Per-image caching (session-only, in-memory):** Both the PyMuPDF word dict and the Tesseract `image_to_data` dict are cached in-memory against `(image_path, pdf_words identity)`. Subsequent pattern changes (the user adds/removes a regex) skip re-running OCR and only re-run `_scan_data_dict()` against the cached output. This makes pattern iteration nearly instantaneous.

The cache is **session-only** and never persisted to disk. It is governed by the RAM limits system in `MainWindow.reclaim_memory`:
- **Soft limit breach** (`soft_ram_limit` exceeded) — the OCR cache is pruned to the 2 most recently accessed entries (`ocr_cache.keys()[:-2]` deleted).
- **Hard limit breach** (`hard_ram_limit` exceeded) — the entire OCR cache is cleared (`ocr_cache.clear()`).
- **Session end** — if `preserve_session_cache` is `false` (default), the cache is fully cleared at the end of each batch session.
- **Maximum page count** — configurable via `max_ocr_cache_pages` QSetting (range 10–500); defaults: `50` pages (< 8 GB RAM), `100` pages (8–16 GB), `200` pages (> 16 GB).

Legacy `.pkl` disk cache files from earlier versions are automatically deleted on first startup.

---

### 2.2 Current Pipeline Detail

`RegexDetector.detect(image_path, pdf_words)` runs the following on each page:

```
┌─────────────────────────────────────────────────────────┐
│  Cache hit?  (same image_path + pdf_words)              │
│  → skip OCR, re-run _scan_data_dict on cached data      │
└─────────────────────────────────────────────────────────┘
           ↓ cache miss
┌─────────────────────────────────────────────────────────┐
│  Pass 1: PyMuPDF native words (if pdf_words provided)   │
│    Build Tesseract-compatible dict from word tuples      │
│    conf = 100.0 for all words (exact extraction)         │
│    scale = 1.0 (coordinates are already page-space)      │
└─────────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────────┐
│  Pass 2: Tesseract OCR                                   │
│    1. cv2.imread grayscale                               │
│    2. cv2.resize ×2 (INTER_CUBIC)                        │
│    3. cv2.threshold Otsu binarise                        │
│    4. pytesseract.image_to_data(--psm 3)                │
│    scale = 2.0 (divide coords by 2 to map to page-space) │
└─────────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────────┐
│  _scan_data_dict on each source dict                     │
│    → line reconstruction → regex search → heuristics    │
│    → SensitiveHit list                                   │
└─────────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────────┐
│  IoU deduplication                                       │
│    boxes_overlap_heavily() → keep higher-confidence hit  │
└─────────────────────────────────────────────────────────┘
```

---

## 3. PII Pattern Matching & Heuristics

### 3.1 Evolution of Pattern Matching

#### Generation 1 — Simple Substring/Regex (`92c3dfd`)

The first implementation allowed a user to type a text string or regex into a single input box, which was applied across the full OCR output as a flat string. Coordinates were approximated from Tesseract's word boxes.

#### Generation 2 — Line-Aware Multi-Word Matching (`5ee2279`)

The critical algorithmic improvement: rather than matching across a flat OCR string (which loses word boundaries and coordinates), the scanner **reconstructs text lines from Tesseract's word-level output** and matches patterns within those lines.

```python
# Group words by (block_num, par_num, line_num)
lines = {}
for i in range(n_boxes):
    if data['level'][i] == 5:  # word level
        key = (block_num, par_num, line_num)
        lines[key].append(i)

# Per line: build string + char→word_idx mapping
for word_idx in word_indices:
    line_text += word + " "
    for _ in word:
        char_to_word_idx.append(word_idx)
```

After a regex match in `line_text`, the character positions are mapped back to word indices, and the bounding box of the match is computed as the union of all word boxes spanning that match. This correctly handles multi-word patterns (e.g. `"John Smith"` spanning two word boxes).

#### Generation 3 — Pattern Library + Proximity Keyword Scoring + Heuristics (`029961f`, `56f23f0`)

The flat user-regex interface was supplemented with a **curated built-in pattern library** (`src/core/patterns.py`) covering:

| Region | Patterns |
|---|---|
| Global | Email, IP address, Credit Card (Luhn), Name (title-prefix), Street Address |
| Pakistan | CNIC, Phone, Passport, Driving Licence, Vehicle Plate |
| United States | SSN, Phone, ZIP Code, Driver's Licence |
| European Union | IBAN (mod-97), VAT ID |
| India | Aadhaar, Phone, PAN Card, Driving Licence |
| United Kingdom | NINO, Phone |

Users select regions from a dropdown; the corresponding patterns are loaded and active for the current scan.

---

### 3.2 Current Matching Strategy

#### Line Reconstruction

Words from both PyMuPDF and Tesseract are grouped by line (block/paragraph/line keys) and concatenated into `line_text` strings. A parallel `char_to_word_idx` array maps every character position back to the word that produced it. When a regex matches at character positions `[start:end]`, the exact word-level bounding boxes for those positions are retrieved and unioned to produce the final hit rectangle.

This correctly handles:
- Multi-word matches spanning two or more boxes
- Patterns with separators that Tesseract may or may not preserve (e.g. `1234-5678-9012-3456` vs `1234 5678 9012 3456`)

#### Confidence Scoring

Raw OCR confidence from Tesseract (word-level) is combined with pattern-specific heuristics:

| Pattern type | Confidence logic |
|---|---|
| **Credit Card** | Run **Luhn algorithm** on matched digits. If checksum valid: `95.0`. If invalid: match rejected entirely. |
| **EU IBAN** | **Mod-97 checksum** (ISO 13616). If `int(rearranged_numeric) % 97 == 1`: `95.0`. If invalid: rejected. |
| **US SSN, IN Aadhaar** | Check ±35 character context window for proximity keywords. If keyword found: `90.0`. If not: `25.0`. |
| **All other patterns with keywords** | Same proximity window. Keyword found: `90.0`. No keyword: `30.0`. |
| **Patterns without keywords** | Average Tesseract confidence of matched words; `100.0` for PyMuPDF hits. |

The threshold below which a hit is demoted to *amber/review-suggested* state (rather than fully confirmed) is configurable in Settings. Low-confidence hits (e.g. SSN-shaped number with no nearby "social security" keyword) are shown with a different highlight colour to alert the reviewer.

#### Situational Patterns (`56f23f0`)

Beyond the structured regional library, two situational patterns were added that activate based on document context:

- **Name** — triggered by title/prefix words (`Mr.`, `Dr.`, `Officer`, `Senator`, etc.) immediately before a capitalised name. Requires specific context to avoid matching all proper nouns.
- **Location / Address** — house-number + street-name + street-type suffix pattern. Also proximity-boosted by address keywords.

These are intentionally conservative by default (low base confidence, keyword-required for high confidence) because proper noun detection produces many false positives without strong context signals.

#### IoU Deduplication

After all pattern matches from both PyMuPDF and Tesseract passes are collected, overlapping hits are deduplicated using **intersection-over-area** (not IoU):

```python
overlap_ratio_1 = intersection_area / box1_area
overlap_ratio_2 = intersection_area / box2_area
if overlap_ratio_1 > 0.40 or overlap_ratio_2 > 0.40:
    # keep the higher-confidence hit
```

This handles cases where the PyMuPDF pass and the Tesseract pass both detect the same word/phrase at slightly different coordinates due to rendering differences.

---

## 4. Future OCR Backends — Roadmap

The architecture supports swapping or adding OCR backends because all text extraction feeds into the same `Tesseract-compatible data dict` structure (`_scan_data_dict` is agnostic to where the dict came from). Adding a new backend means producing a dict with the standard keys (`text`, `left`, `top`, `width`, `height`, `conf`, `level`, `block_num`, `line_num`) and appending it to `cached_data_list`.

Planned future options (to be exposed in Settings › OCR Engine):

| Option | Best for | Trade-off |
|---|---|---|
| **Tesseract** (current default) | Typed documents, PDFs, clean scans | Struggles with handwriting, curved text |
| **EasyOCR** | Handwriting, multi-language, non-Latin scripts | Slower on CPU; requires `easyocr` package |
| **Microsoft Presidio** | Unstructured text with NLP-level entity recognition | Requires spaCy models; no coordinates natively |
| **Local VLM (future)** | Degraded scans, mixed language, semantic context | Requires 8+ GB VRAM; not currently viable |

In the current phase, the focus is on clean formal documents (typed PDFs, standard office scans) where Tesseract + curated regex significantly outperforms heavier models for the effort required. EasyOCR and Presidio would be most impactful for a future "document diversity" phase targeting handwritten records, non-Latin government IDs, or NLP-intensive narrative documents.
