# SafeMARC — Vision & Identity Matching System

This document provides a detailed technical reference for SafeMARC's computer vision pipeline: face **detection** (locating faces in an image) and face **recognition** (determining whose face it is). Both subsystems live in `src/core/detectors/vision.py` and `src/core/identity_manager.py` respectively.

---

## 1. Face Detection — YuNet DNN

### 1.1 Why YuNet instead of Haar Cascades

Previous versions used an OpenCV Haar Cascade ensemble (frontal default, frontal alt2, profile, flipped profile, CLAHE pass, ±30° rotation passes). While high-recall, this approach had several hard limits:

| Problem | Detail |
|---|---|
| **False positives** | Texture regions (lips, eyes, wrinkled fabric) frequently trigger cascades |
| **Speed** | 5+ independent cascade passes + rotation warps per image |
| **No landmarks** | Cascades return only a bounding box; no eye/nose positions for geometric alignment |
| **Grayscale only** | Colour information is discarded before detection |

**YuNet** (`cv2.FaceDetectorYN`) is a lightweight DNN face detector from the OpenCV Zoo. It runs directly on BGR images, returns a **15-element detection vector per face** (bounding box + 5 facial landmarks + confidence score), and achieves state-of-the-art accuracy on the WIDER Face benchmark at millisecond latency.

```
Detection row layout (15 values):
  [0]  x       — left edge of bounding box
  [1]  y       — top edge of bounding box
  [2]  w       — width of bounding box
  [3]  h       — height of bounding box
  [4]  re_x    — right eye centre x
  [5]  re_y    — right eye centre y
  [6]  le_x    — left eye centre x
  [7]  le_y    — left eye centre y
  [8]  nose_x  — nose tip x
  [9]  nose_y  — nose tip y
  [10] rm_x    — right mouth corner x
  [11] rm_y    — right mouth corner y
  [12] lm_x    — left mouth corner x
  [13] lm_y    — left mouth corner y
  [14] score   — detection confidence (0.0 – 1.0)
```

The 5 landmarks are the critical ingredient that enables **geometric face alignment** before recognition (see §2.3).

**Model file:** `assets/face_detection_yunet_2023mar.onnx` (~228 KB, gitignored)

```bash
curl -L -o assets/face_detection_yunet_2023mar.onnx \
  https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx
```

> **Note on model versions:** `face_detection_yunet_2026may.onnx` is a re-export of the same weights with symbolic (dynamic) input dimensions for OpenCV 5.x compatibility. Since SafeMARC runs on OpenCV 4.x, `2023mar` is the correct choice — it uses fixed input dimensions matched per-call to the actual image size.

---

### 1.2 Multi-Scale Detection Strategy

YuNet is trained to detect faces in the **10 × 10 to 300 × 300 pixel** range. A close-up portrait where the face fills most of the frame (e.g. 800 × 700 px) falls outside this range and would be missed — or worse, sub-face regions like lips or eyes (which are within range) get detected instead.

`VisionDetector._multi_scale_detect()` addresses this with two complementary passes:

```
Pass 1 — Native resolution
  Input:  original BGR image at full size
  Catches: small and medium faces (10 – ~300 px)

Pass 2 — Downscaled (only if max(w, h) > 640)
  Input:  image resized so its longest dimension = 640 px
  Catches: large faces (portrait, close-up) that are out of range at native scale
  Post:   bounding box + landmark coordinates scaled back to original resolution
```

After both passes, all detections are merged through NMS (§1.3) to eliminate cross-scale duplicates.

**Thread-local detector instances:**  YuNet requires the input resolution to be declared at creation time. Rather than re-creating the detector on every frame, `VisionDetector` caches a thread-local instance keyed by `(width, height)` and only recreates it when the image size changes:

```python
def _get_yunet(self, w, h) -> cv2.FaceDetectorYN:
    if self._local.yunet_size != (w, h):
        self._local.yunet = _load_yunet(self._yunet_model_path, (w, h))
        self._local.yunet_size = (w, h)
    return self._local.yunet
```

Separate instances are kept for the native (`_local.yunet`) and downscaled (`_local.yunet_small`) passes.

---

### 1.3 Non-Maximum Suppression (NMS)

After collecting detections from both passes, `VisionDetector._nms()` de-duplicates overlapping boxes using a **containment-ratio** check rather than standard IoU.

**Why not standard IoU?**

Standard IoU only suppresses boxes with significant mutual overlap. A lips detection (say 80 × 30 px) positioned inside a face box (200 × 220 px) has a very low IoU with that face box, so it would survive a standard IoU NMS. The lips box is fully contained within the face box, which is the actual signal we want to suppress.

**Containment ratio formula:**

```
containment = intersection_area / min(box_area, candidate_area)
```

If `containment > 0.40` the smaller detection is suppressed. This correctly removes any sub-face hit that is ≥ 40% enclosed by a larger face detection.

The NMS runs on detections sorted by confidence (highest first) so the strongest detection wins in every overlap group.

**Confidence threshold:** `0.70` (raised from the YuNet default of 0.60 to further reduce marginal false positives like lip/texture detections in high-resolution document scans).

---

## 2. Face Recognition — SFace + LBPH

### 2.1 Architecture Overview

SafeMARC uses a two-model recognition stack:

| Model | Role | File |
|---|---|---|
| **SFace** (primary) | Deep learning cosine-similarity embedding | `assets/face_recognition_sface_2021dec.onnx` |
| **LBPH** (fallback) | Classical Local Binary Pattern Histogram | Built into OpenCV, no file needed |

SFace is loaded automatically if the `.onnx` model file is present. If not, LBPH is used. All logic is in `IdentityManager`.

---

### 2.2 Reference Embedding Building (`reload_identities`)

When the app starts (or after any identity change), `IdentityManager.reload_identities()` scans `~/.local/share/SafeMARC/identities/<person_name>/` for reference images and builds the in-memory embedding store.

**SFace path (preferred):**

1. Load the reference image with `cv2.imread`.
2. Run YuNet on the reference image to detect the face and obtain its 15-element detection row (including 5 landmarks).
3. Call `cv2.FaceRecognizerSF.alignCrop(img, detection_row)` — this uses the 5 landmark positions to **geometrically normalise** the face (correct for rotation, scale, inter-eye distance) and returns a 112 × 112 BGR crop.
4. Call `sface_recognizer.feature(aligned_crop)` to produce a 128-dimensional embedding vector.
5. Save the embedding to `<image_path>.sface.npy` as a cache so subsequent launches don't re-run YuNet + SFace on unchanged reference images.

If YuNet finds no face in a reference image (e.g. the image is a tight crop without enough context), the code falls back to a plain `cv2.resize(crop, (112, 112))` before computing the embedding.

**LBPH path (fallback):**

The reference image is converted to grayscale, resized to 150 × 150, and histogram-equalised. The processed crop is used directly to train an `LBPHFaceRecognizer`.

---

### 2.3 Live Matching — `match_face_aligned`

`VisionDetector._detect_faces()` calls `IdentityManager.match_face_aligned(full_img, det_row, num_faces)` for each detected face, passing:

- `full_img` — the original full BGR image (not a pre-cropped face patch)
- `det_row` — the raw 15-element YuNet detection row for this face
- `num_faces` — total number of faces detected in this image (used for context-aware margin, §2.5)

**Why pass the full image instead of a crop?**

`cv2.FaceRecognizerSF.alignCrop(src, face_box)` requires the full source image alongside the detection row. It internally uses the 5 landmark positions to compute a similarity transform (rotation + scale) that maps the face to a canonical 112 × 112 pose. Cropping first and then resizing discards the landmark geometry and produces lower-quality alignment.

```
Full image
    │
    ├── YuNet detection row [x, y, w, h, re, le, nose, rm, lm, score]
    │                                          ↑ 5 landmarks
    └── alignCrop(full_img, det_row)
            │
            └── 112 × 112 BGR, geometrically normalised
                    │
                    └── sface_recognizer.feature(aligned)
                            │
                            └── 128-dim embedding vector
```

---

### 2.4 Cosine Similarity Scoring

SFace embeddings are compared with `cv2.FaceRecognizerSF.match(..., cv2.FaceRecognizerSF_FR_COSINE)`, which returns a cosine similarity score in **[−1, 1]** where 1 means identical.

Typical score distributions observed in testing:

| Scenario | Score range |
|---|---|
| Same person, clear frontal portrait | 0.75 – 0.95 |
| Same person, group photo / challenging angle | 0.40 – 0.60 |
| Different person, similar appearance | 0.30 – 0.45 |
| Different person, dissimilar appearance | −0.10 – 0.25 |

The overlap between "same person, challenging" and "different person, similar" is the core difficulty. The scoring strategy in §2.5 addresses this.

**Per-identity score = MAX across all reference embeddings.**  If a person has multiple reference photos, the score is the maximum cosine similarity against any single reference. This preserves recall: one reference photo that closely matches the current angle/lighting is sufficient to produce a strong score, rather than being dragged down by refs shot in different conditions.

---

### 2.5 Context-Aware Tiered Margin Scoring

A raw threshold check (score > 0.40) alone produces false positives in group photos where a stranger's face scores 0.41–0.47 against one reference image. The solution is a **second-place margin** requirement — the winning identity's score must exceed the second-best identity's score by a minimum gap, preventing ambiguous matches where multiple identities score similarly.

The margin requirement is **tiered by both score band and image context** (`_rank_sface_embedding`):

```
┌─────────────────────────────────────────────────────────────────┐
│  score > threshold + 0.20  (strong zone, e.g. > 0.60)          │
│  → margin >= 0.08   (relaxed, high confidence speaks for itself) │
├─────────────────────────────────────────────────────────────────┤
│  threshold <= score <= threshold + 0.20  (borderline zone)      │
│                                                                  │
│  num_faces == 1  (portrait / single-face image)                  │
│  → margin >= 0.10   (moderate — solo shots have low FP risk)     │
│                                                                  │
│  num_faces > 1   (group photo / document with multiple faces)    │
│  → margin >= 0.20   (strict — many competing faces, higher risk) │
├─────────────────────────────────────────────────────────────────┤
│  score < threshold                                               │
│  → REJECT unconditionally                                        │
└─────────────────────────────────────────────────────────────────┘
```

**Default threshold:** `0.40` (configurable via Settings › Face Match Threshold slider, persisted in `QSettings`).

**Why context-aware margin?**

| Situation | Score | Margin | num_faces | Required margin | Decision |
|---|---|---|---|---|---|
| Person A portrait (genuine) | 0.44 | 0.14 | 1 | ≥ 0.10 | **MATCH** ✅ |
| Person B in group photo (false positive) | 0.47 | 0.17 | 38 | ≥ 0.20 | **REJECT** ✅ |
| Person A in group photo (genuine) | 0.49 | 0.27 | 38 | ≥ 0.20 | **MATCH** ✅ |
| Any portrait > 0.75 | 0.90 | 0.63 | any | ≥ 0.08 | **MATCH** ✅ |

A portrait with one face is inherently lower risk — if that face scores 0.44 against Person A's refs and only 0.30 against Person B's refs, that 0.14 margin is meaningful. In a 38-face seminar photo the same scores could be coincidental texture matches, so a 0.20 gap is required.

**Only one identity registered:** the margin check is skipped entirely (no second-best to compare against).

---

### 2.6 Face Redaction Modes

Identity matching feeds directly into `SafeScanner.scan()`, which applies one of three modes:

| Mode | Behaviour |
|---|---|
| **ALL** | Every detected face is redacted regardless of identity |
| **BLACKLIST** | Only faces identified as a target identity are redacted |
| **WHITELIST** | All faces are redacted *except* those identified as a protected identity |

In ALL mode, identity matching still runs in the background (to populate `SensitiveHit.identity`) but the result does not affect whether a hit is included.

---

### 2.7 LBPH Fallback

When the SFace ONNX model is absent, `IdentityManager` trains an `LBPHFaceRecognizer` (radius=2, neighbors=8, grid=8×8) on 150 × 150 grayscale histogram-equalised crops from reference images. Matching uses LBPH's `predict()` distance metric — a lower distance means a better match. The acceptance threshold is distance < 115.0.

LBPH does not use landmarks or geometric alignment, so it is significantly less robust to pose and lighting variation than SFace. It exists purely as a no-model-download fallback for offline or restricted environments.

---

## 3. Configuration & Tuning

All tuneable parameters for the vision and identity systems are stored in `QSettings("SafeMARC", "SafeMARC")` and exposed in Settings › Model Configuration:

| Setting key | Default | Description |
|---|---|---|
| `model_face_match` | `0.40` | SFace cosine similarity threshold for identity acceptance |
| `model_face_detect` | `0.20` | MediaPipe ObjectDetector score threshold (body detection mode only) |

The YuNet detection threshold (`0.70`), NMS containment ratio (`0.40`), and tiered margin values (`0.08 / 0.10 / 0.20`) are currently hard-coded constants in `vision.py` and `identity_manager.py` (`_STRONG_SCORE_OFFSET`, `_MARGIN_STRONG`, `_MARGIN_BORDERLINE_1`, `_MARGIN_BORDERLINE_N`).

---

## 4. Model Assets Summary

| File | Size | Purpose | Download |
|---|---|---|---|
| `assets/face_detection_yunet_2023mar.onnx` | ~228 KB | YuNet face detector | See `README.md` |
| `assets/face_recognition_sface_2021dec.onnx` | ~37 MB | SFace identity embeddings | See `README.md` |
| `assets/efficientdet_lite2.tflite` | ~23 MB | MediaPipe body/person detector | See `README.md` |

All three files are gitignored (`*.onnx`, `*.tflite`). Run the `curl` commands in `README.md` to download them into the `assets/` directory before first use.
