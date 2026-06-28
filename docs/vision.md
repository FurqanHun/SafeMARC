# SafeMARC — Vision & Identity Matching System

This document provides a detailed technical reference for SafeMARC's computer vision pipeline: face **detection** (locating faces in an image) and face **recognition** (determining whose face it is). Both subsystems live in `src/core/detectors/vision.py` and `src/core/identity_manager.py` respectively.

---

## 1. Face Detection — YuNet DNN

### 1.1 Detection Evolution — From Haar Cascades to YuNet

SafeMARC's face detector went through three distinct generations, each motivated by real problems observed in testing.

#### Generation 1 — Single Haar Cascade (`92c3dfd`)

The initial implementation used a single `haarcascade_frontalface_default.xml` pass on a grayscale image. It was fast and required no model file download, but had serious limitations:

- **Upright frontals only** — tilted heads, side profiles, and partially occluded faces were missed entirely.
- **High false-positive rate** on scanned documents — high-contrast texture patterns (letterheads, table borders, watermarks) frequently triggered the cascade.
- **No sub-detector coordination** — single pass meant no way to recover from misses.

#### Generation 2 — Ensemble Haar Cascade with Union-NMS (`784c810`, `0cc2dbb`, `214d3d1`)

To fix the recall problems, the detector was rebuilt as a **multi-cascade ensemble**:

| Pass | Cascade | Purpose |
|---|---|---|
| 1 | `haarcascade_frontalface_alt2.xml` | Tilted heads, slight occlusion |
| 2 | `haarcascade_frontalface_default.xml` | Classic upright frontals |
| 3 | `haarcascade_profileface.xml` | Left-facing side profiles |
| 4 | Profile cascade on horizontally flipped image | Right-facing side profiles |
| 5 | Alt frontal on CLAHE-enhanced image | Low-contrast / underexposed faces |
| 6–7 | Alt frontal on ±30° rotated images | Strongly tilted heads |

All raw detections from all passes were pooled and merged with a custom **Union-NMS** — rather than picking one winner, overlapping boxes from different cascades were merged by taking their coordinate union. This ensured partially covered faces (hands in front, hair, glasses) were fully enclosed in the final redaction box.

Thread safety was also addressed (`214d3d1`): cascade classifiers are not thread-safe in OpenCV. Each worker thread that calls `detect()` was given its own thread-local `_local.face_cascade` instances via `threading.local()` to prevent concurrent access assertion crashes.

**Result:** significantly improved recall across poses and angles, and the Union-NMS approach effectively collapsed multi-cascade duplicate hits into clean single boxes. False positives dropped substantially compared to generation 1.

**Remaining limitations:**
- Still no landmark data — SFace matching used a plain bbox crop + resize, discarding all geometric alignment information.
- The 7-pass pipeline was expensive and did a lot of redundant work on images with many faces.
- Very large portrait-sized faces (> 300 px) still required multiple passes to be caught at rotated scales.
- Texture false positives on scanned documents persisted at lower rates.

#### Generation 3 — YuNet DNN + Multi-Scale + Context-Aware Matching (current, `a11d1d5`, `f551c7c`, `d8faf5c`)

YuNet was introduced to replace the entire cascade ensemble. Out of the box it matched the ensemble's core accuracy on standard portraits while being faster and simpler — one model, one pass. However, two issues required additional engineering:

1. **Large portrait miss** — YuNet's training range is 10–300 px. A close-up portrait where the face fills 800 × 700 px is outside this range. Solution: **multi-scale detection** (§1.2) — a second pass on a downscaled image catches these large faces.

2. **Sub-face false positives on large faces** — before the multi-scale pass was in place, YuNet at native resolution would detect lips or eyes (which happen to be in the 10–300 px range) instead of the full face. Solution: **containment-ratio NMS** (§1.3) — suppresses any box that is ≥ 40% enclosed by a larger sibling detection.

3. **SFace accuracy regression** — the initial YuNet integration passed only a bbox crop to SFace, the same as the Haar ensemble did. This turned out to lose all landmark geometry and produce *worse* SFace scores than the ensemble (even though the crop was better). Solution: pass the full 15-element detection row to `alignCrop` (§2.3), which restored and exceeded the previous matching accuracy.

So while YuNet alone was "quite similar" to the refined ensemble on straight portraits, it needed the same class of supplementary techniques (multi-scale, NMS refinement, geometric alignment) to match the ensemble's overall performance — just expressed differently and more efficiently.

---

### 1.2 Why YuNet was Still Worth the Switch

Even after adding multi-scale and containment NMS, the YuNet stack is meaningfully better than the ensemble in several ways:

| | Ensemble Haar | YuNet (current) |
|---|---|---|
| **Passes per image** | 7 (cascade × 5 + CLAHE + rotations) | 2 (native + downscaled) |
| **Landmark output** | ❌ bbox only | ✅ 5 keypoints per face |
| **SFace alignment** | plain resize, no geometry | `alignCrop` with landmark transform |
| **Sub-face FP handling** | Union-NMS (merge, not suppress) | Containment-ratio NMS (suppress) |
| **Thread safety** | manual `threading.local` cascade copies | thread-local `cv2.FaceDetectorYN` instances |
| **Model download** | none (built-in cascades) | 228 KB ONNX |

The 5 landmark points are the decisive advantage: they enable `cv2.FaceRecognizerSF.alignCrop()` which geometrically normalises each face to a canonical pose before computing the SFace embedding. The ensemble had no way to do this, which is why SFace scores were lower even when the bbox itself was correctly placed.

---

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

### 2.1 Recognition Evolution — Models Explored and Rejected

Like detection, face recognition in SafeMARC went through several iterations and evaluated multiple candidate models before settling on the current architecture.

#### Models Evaluated

**MediaPipe face detection models (explored, not adopted for recognition)**

During early planning the project explored MediaPipe's `BlazeFace` models for face detection as an alternative to Haar cascades. Download commands for two variants were recorded in `todo.log`:

```bash
# BlazeFace short-range (selfie/close-up oriented)
wget -O face_detector.tflite \
  https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite

# BlazeFace full-range
curl -L -o face_detector_full.tflite \
  https://github.com/google-ai-edge/mediapipe/raw/master/mediapipe/modules/face_detection/face_detection_full_range.tflite
```

These were evaluated and not adopted for face detection. BlazeFace is optimised for real-time selfie streams with a very short depth-of-field assumption; it performs poorly on the high-resolution scanned document images and multi-face group photos that SafeMARC typically processes. The Haar ensemble already handled these cases better, and YuNet was a superior eventual solution.

**MediaPipe EfficientDet models (adopted for body detection only)**

MediaPipe's `EfficientDet Lite` family was evaluated for body/person detection. Two sizes were tested:

```bash
# Lite 0 — lighter, faster
curl -L -o object_detector.task \
  "https://storage.googleapis.com/mediapipe-models/object_detector/efficientdet_lite0/float16/latest/efficientdet_lite0.tflite"

# Lite 2 — heavier, more accurate  
curl -L -o object_detector_heavy.task \
  "https://storage.googleapis.com/mediapipe-models/object_detector/efficientdet_lite2/float32/latest/efficientdet_lite2.tflite"
```

`EfficientDet Lite 2` was chosen for the **body/person detection mode** (`VisionDetector(mode="bodies")`). It is not involved in face detection or identity matching — it exists as a separate redaction mode for non-face-based privacy (e.g. blurring all people in a document without facial recognition).

---

#### Generation 1 — LBPH Face Recognizer (`92c3dfd` – `1f6b64f`)

Before any identity system existed, face detection returned only anonymous hits (label: `"FACE"`). When identity-based redaction was added (`1f6b64f`), the initial recogniser was OpenCV's **LBPH (Local Binary Pattern Histogram)** — chosen because it requires no model download and is built into OpenCV.

LBPH works by encoding local texture patterns in a grayscale image into histograms and comparing them. Reference images were cropped with a single Haar cascade, resized to 150 × 150, histogram-equalised, and used to train an `LBPHFaceRecognizer`. At match time, `predict()` returns a distance value; a distance below 115.0 was treated as a match.

**Limitations:**
- No geometric normalisation — angle and lighting changes between registration and scan time caused high miss rates.
- Inherently holistic — cannot separate a face from background if the crop is slightly misaligned.
- Works adequately on controlled portraits with consistent angle/lighting; breaks down on group photos.

#### Generation 2 — SFace DNN with LBPH fallback (`1f6b64f`, `0446cfb`, `5bd90f5`)

SFace (`cv2.FaceRecognizerSF`, OpenCV Zoo) was introduced as the primary recogniser in the same commit that added the full identity-management system (`1f6b64f`). It produces a **128-dimensional embedding vector** per face; two faces are compared by cosine similarity. This is the same class of approach used by commercial FR systems (ArcFace, FaceNet etc.).

The initial SFace integration used the same crop-and-resize approach as LBPH — the Haar cascade bounding box was extracted, resized to 112 × 112, and passed to `sface_recognizer.feature()`. No landmark alignment was applied.

Two optimisations were added in `0446cfb`:
- **Embedding cache** — each reference image's SFace embedding is saved as `<image>.sface.npy` so subsequent launches skip the YuNet + SFace recompute.
- **LBPH crop cache** — similarly, the pre-processed LBPH grayscale crop is saved as `<image>.lbph.png`.

An ensemble auto-crop for reference images was also added in `5bd90f5`: when registering a new identity, the same multi-cascade ensemble was run on the reference photo to find and crop the face region before computing the embedding. This improved registration quality for photos where the subject was not already tightly cropped.

**Default threshold:** `0.363` (OpenCV's published default for SFace cosine similarity).

#### Generation 3 — SFace + YuNet alignCrop + Context-Aware Margin (current, `a11d1d5`–`d8faf5c`)

With YuNet replacing the cascade ensemble for detection, SFace matching was also updated to take advantage of YuNet's landmark output:

1. **`alignCrop` for reference embedding building** — instead of the multi-cascade crop + resize, `_build_aligned_embedding()` runs YuNet on the reference image, takes the largest detection's 15-element row, and calls `sface_recognizer.alignCrop()`. This geometrically normalises the face (rotation, scale, inter-eye distance) before computing the embedding. Stale `.sface.npy` caches from the previous approach were invalidated on migration.

2. **`alignCrop` for live matching** — `match_face_aligned()` receives the full image and the raw YuNet detection row, so `alignCrop()` can apply the same geometric transform to the live face before comparison. Passing the full image (not a pre-crop) is required by the OpenCV API to use the landmark positions.

3. **Context-aware tiered margin** — plain threshold matching produced false positives in group photos (stranger scoring 0.47 against one reference frame). The `_rank_sface_embedding()` logic was refined through several test runs with real photos before reaching the current tier constants (see §2.5).

4. **Default threshold raised to 0.40** from 0.363 after empirical testing showed the higher threshold reduced marginal false positives with minimal true-positive recall loss on the test set.

---

### 2.2 Architecture Overview

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

## 3. Body Detection Pipeline

SafeMARC's body detection mode (`VisionDetector(mode="bodies")`) is built to locate full-body silhouettes and coordinate with face detections for identity-based body redaction. Because group photos have unique challenges like high density, small silhouettes, and row-based overlaps, the body detection pipeline uses several advanced stages:

### 3.1 Model & Class Filtering
The pipeline uses MediaPipe's **EfficientDet-Lite2** (`efficientdet_lite2.tflite`) running on CPU/XNNPACK. 
- SafeMARC strictly filters out all categories except `"person"`.
- The `"face"` category of EfficientDet is disabled because face detection is handled with much higher precision by YuNet. This prevents overlapping duplicate boxes from two different models.

### 3.2 Adaptive CLAHE Contrast Enhancement
Low-light or poorly exposed document scans degrade the body detector's performance. SafeMARC automatically checks the average brightness before scanning:
- The image is converted to grayscale, and the mean brightness is computed.
- If the mean brightness is `< 90`, the system applies **Contrast Limited Adaptive Histogram Equalization (CLAHE)** with a `clipLimit=2.0` and `tileGridSize=(8, 8)` to the L channel of the image in LAB color space, then converts it back to BGR.
- This highlights structural details in dark regions without blowing out highlights, significantly improving body recall in dark environments.

### 3.3 Adaptive Tiling Grid
Large group photos (e.g. 6000 × 4000 pixels) contain small individuals that the detector's native receptive field cannot resolve. To solve this, SafeMARC implements an **adaptive tiling grid**:
- Grid density scales dynamically based on the image's maximum dimension:
  - **Max Dim ≥ 5000 px**: 4 × 3 grid (12 tiles)
  - **Max Dim ≥ 3500 px**: 3 × 3 grid (9 tiles)
  - **Max Dim ≥ 2000 px**: 2 × 2 grid (4 tiles)
  - **Max Dim < 2000 px**: 1 × 1 pass (global only)
- Tiles are scanned with a 100-pixel overlap to prevent individuals standing on boundary lines from being missed.
- Detections from all tiles are pooled together and converted back to absolute image coordinates.

### 3.4 Small Object Upscaling
For small images where the maximum dimension is `< 640 px`, SafeMARC pre-processes the image by upscaling it 2× using linear interpolation. Bounding boxes returned by the detector are subsequently scaled back down. This allows EfficientDet to resolve small silhouettes that would otherwise be missed.

### 3.5 Non-Maximum Suppression (NMS)
Unlike face detection (which uses containment-ratio NMS to suppress sub-features like eyes or lips), body detection uses standard **Intersection-over-Union (IoU) NMS** with a threshold of `0.55`:
- Using containment NMS on bodies would mistakenly suppress a front-row person who is highly overlapped by a taller back-row person.
- The `0.55` IoU threshold allows closely packed, overlapping individuals in group pictures to retain their distinct bounding boxes while removing tile-boundary duplicates.

### 3.6 Sliver and Shape Filtering
Object detectors often flag arms, hands, neck fragments, or high-contrast background banners as "person" detections, leading to false-positive redaction blocks. To prevent this, SafeMARC applies a shape filter after NMS:
- Any bounding box where the height is less than half its width (`height < width * 0.5`) is discarded as a horizontal sliver.
- This preserves seated, crouching, or standing people while reliably filtering out arm and neck fragments.

### 3.7 Depth-Ordered Clipping
In multi-row group photos, a person in a back row will have a bounding box that extends downwards, often overlapping with the face of the person sitting or standing directly in front of them. Burning a redaction block on the back-row body would cover the front-row face. 

SafeMARC solves this with a **spatial depth heuristic**:
1. The bottom edge (`y + h`) of a box acts as a proxy for depth (lower bottom edge = closer to the camera/in front).
2. For every pair of overlapping body boxes, we identify the one "in front" (lower bottom edge) and the one "behind" (higher bottom edge).
3. If the "behind" box overlaps horizontally with the face of the "in-front" person, we clip the bottom of the "behind" box so it stops exactly at the top of the front person's face (`new_height = front_face.y - behind.y`).
4. To avoid leaving tiny fragments, we only clip if the resulting box retains at least 30% of its original height.

### 3.8 Hybrid Face-Body Identity Mapping
To allow Blacklist/Whitelist identity modes to apply to full-body redaction, the vision pipeline maps bodies to facial identities:
1. Face detection (YuNet) and identity matching (SFace) are run first.
2. The body detector is then executed, producing candidate body boxes.
3. For each body box, we check if any detected face box is contained within it (using a containment threshold of `0.50`).
4. If a matching face is found, the body box is tagged with that face's identity (`SensitiveHit.identity`).
5. **Face-Guided Recovery**: If a recognized face is not covered by any body box (due to a body detection miss), a synthetic body box is generated centering the face (`width = face.w * 2.5`, `height = face.h * 4.5`, starting vertically at `y = face.y` and extending downwards) to guarantee the body of the target identity is still redacted.

---

## 4. Configuration & Tuning

All tuneable parameters for the vision and identity systems are stored in `QSettings("SafeMARC", "SafeMARC")` and exposed in Settings › Model Configuration:

| Setting key | Default | Description |
|---|---|---|
| `model_face_match` | `0.40` | SFace cosine similarity threshold for identity acceptance |
| `model_face_detect_yunet` | `0.70` | YuNet face detection confidence threshold |
| `model_body_detect` | `0.25` | MediaPipe body detection score threshold |
| `pdf_extract_zoom` | `2.0` | PDF rasterization zoom multiplier (range 1.0–4.0×); stored in QSettings |
| `soft_ram_limit` | `1024 MB` (< 8 GB RAM) · `1536 MB` (8–16 GB) · `2048 MB` (> 16 GB) | RSS threshold above which OCR cache is pruned to the last 2 pages |
| `hard_ram_limit` | `2048 MB` (< 8 GB RAM) · `3072 MB` (8–16 GB) · `4096 MB` (> 16 GB) | RSS threshold above which all caches are flushed and vision detectors are destroyed |
| `max_ocr_cache_pages` | `50` (< 8 GB RAM) · `100` (8–16 GB) · `200` (> 16 GB) | Maximum pages retained in the in-memory OCR result cache (oldest-first eviction) |
| `preserve_session_cache` | `false` | When `true`, OCR cache is preserved across batch review sessions |

The YuNet detection threshold is dynamically loaded from QSettings (`model_face_detect_yunet`), while NMS containment ratio (`0.40`), and SFace tiered margin values (`0.08 / 0.10 / 0.20`) are hard-coded constants in `vision.py` and `identity_manager.py`.

---

## 5. Memory Management in VisionDetector

Large batch runs — especially seminar-scale group photos or high-resolution PDFs — can produce transient RSS spikes during detection. `VisionDetector` includes a proactive memory reclamation helper to limit these spikes mid-scan.

### 5.1 `_reclaim_if_needed()`

A lightweight check called at strategic points inside `_detect_bodies()` and `detect()`:

1. Read current process RSS via `psutil.Process.memory_info().rss`.
2. Read `soft_ram_limit` from `QSettings` (defaults: `1024 MB` for < 8 GB RAM, `1536 MB` for 8–16 GB, `2048 MB` for > 16 GB).
3. If RSS exceeds the soft limit:
   - Run `gc.collect()` to release Python-managed objects.
   - On **Linux**: call `ctypes.CDLL("libc.so.6").malloc_trim(0)` to release free glibc heap arenas back to the kernel immediately.
   - On **Windows**: call `kernel32.SetProcessWorkingSetSize(handle, -1, -1)` to trim the process working set, producing the equivalent effect.

### 5.2 Invocation Points

| Location | Purpose |
|---|---|
| After Pass 1 (full-image detect) in `_detect_bodies` | Release the full-resolution `mp.Image` buffer and inference result before tiling begins |
| After each tile in the adaptive tiling loop | Release per-tile `tile_img`, `tile_rgb`, `tile_mp`, and `tile_result` before the next tile allocates |
| After `_detect_faces` and `_detect_bodies` return in `detect()` | Final per-image sweep after all inference is complete |

### 5.3 Transient Spike Tolerance

A temporary RSS spike above the soft limit during a single complex image (e.g. a 38-face seminar photo) is an **expected and acceptable tradeoff**. Constraining the scan resolution to prevent such spikes would degrade detection accuracy for small or distant faces. The key guarantee is that the spike is released immediately after the scan completes, not accumulated across the batch.

---

## 5. Model Assets Summary

| File | Size | Purpose | Download |
|---|---|---|---|
| `assets/face_detection_yunet_2023mar.onnx` | ~228 KB | YuNet face detector | See `README.md` |
| `assets/face_recognition_sface_2021dec.onnx` | ~37 MB | SFace identity embeddings | See `README.md` |
| `assets/efficientdet_lite2.tflite` | ~23 MB | MediaPipe body/person detector | See `README.md` |

All three files are gitignored (`*.onnx`, `*.tflite`). Run the `curl` commands in `README.md` to download them into the `assets/` directory before first use.
