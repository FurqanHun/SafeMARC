import os
import cv2
import numpy as np
import threading
from typing import List, Dict, Optional
from src.utils.paths import resource_path, get_app_data_dir


# Score and NMS thresholds used by YuNet when cropping reference faces.
_YUNET_SCORE_THRESH = 0.50
_YUNET_NMS_THRESH   = 0.30
_YUNET_TOP_K        = 100


class IdentityManager:
    def __init__(self, identities_dir: str = None):
        self.identities_dir = os.path.abspath(identities_dir) if identities_dir else os.path.join(get_app_data_dir(), "identities")
        os.makedirs(self.identities_dir, exist_ok=True)
        
        import tempfile
        self.session_temp = os.path.join(tempfile.gettempdir(), "safemarc_temp", "session_temp")
        os.makedirs(self.session_temp, exist_ok=True)
        
        # Mapping from integer face class ID to the registered person name.
        self.identity_map: Dict[int, str] = {}
        self.is_trained = False
        self._local = threading.local()
        
        self.use_sface = False
        self.sface_recognizer = None
        # Cache of biometric SFace face embeddings, keyed by person name.
        self.sface_embeddings: Dict[str, List[np.ndarray]] = {}
        
        self.sface_model = resource_path("assets/face_recognition_sface_2021dec.onnx")
        if os.path.exists(self.sface_model):
            self.use_sface = True
            print("[IdentityManager] SFace model file found. Biometric recognition is available.")
        
        if not self.use_sface:
            print("[IdentityManager] Using LBPH fallback (less accurate).")
            self.recognizer = cv2.face.LBPHFaceRecognizer_create(
                radius=2, neighbors=8, grid_x=8, grid_y=8
            )
        
        self.reload_identities()

    def _get_sface_recognizer(self):
        if self.sface_recognizer is None:
            if self.use_sface and os.path.exists(self.sface_model):
                try:
                    print("[IdentityManager] Lazy-loading SFace model...")
                    self.sface_recognizer = cv2.FaceRecognizerSF.create(self.sface_model, "")
                except Exception as e:
                    print(f"[IdentityManager] Failed to load SFace model lazily: {e}")
                    self.use_sface = False
        return self.sface_recognizer

    def _extract_face_crop(self, img: np.ndarray) -> np.ndarray:
        """
        Extract the largest face crop from an image using YuNet DNN detector.
        Falls back to the full image if no face is found.
        Returns a BGR crop.
        """
        yunet_path = resource_path("assets/face_detection_yunet_2023mar.onnx")
        if not os.path.exists(yunet_path):
            # YuNet model not present — return the full image as-is.
            return img

        h_img, w_img = img.shape[:2]
        detector = cv2.FaceDetectorYN.create(
            model=yunet_path,
            config="",
            input_size=(w_img, h_img),
            score_threshold=_YUNET_SCORE_THRESH,
            nms_threshold=_YUNET_NMS_THRESH,
            top_k=_YUNET_TOP_K,
        )

        _, detections = detector.detect(img)

        if detections is None or len(detections) == 0:
            return img

        # Select the largest face detection based on bounding box area.
        best = max(detections, key=lambda d: d[2] * d[3])
        x, y, w, h = int(best[0]), int(best[1]), int(best[2]), int(best[3])

        # Prevent coordinates from extending beyond the image boundaries.
        x = max(0, x)
        y = max(0, y)
        w = min(w_img - x, w)
        h = min(h_img - y, h)

        if w <= 0 or h <= 0:
            return img

        return img[y:y + h, x:x + w]

    def reload_identities(self):
        """Loads images from disk and builds recognition data."""
        self.identity_map = {}
        self.sface_embeddings = {}
        
        faces_lbph = []
        labels_lbph = []
        
        dirs_to_scan = [self.identities_dir, self.session_temp]
        
        current_id = 0
        for base_dir in dirs_to_scan:
            if not os.path.exists(base_dir): continue
            
            for person_name in sorted(os.listdir(base_dir)):
                if person_name == "session_temp": continue
                
                person_path = os.path.join(base_dir, person_name)
                if not os.path.isdir(person_path):
                    continue
                
                person_has_images = False
                    
                for img_name in os.listdir(person_path):
                    if img_name.endswith(".npy") or ".lbph.png" in img_name:
                        continue
                    
                    img_path = os.path.join(person_path, img_name)
                    
                    if self.use_sface:
                        npy_path = img_path + ".sface.npy"
                        if os.path.exists(npy_path):
                            try:
                                embedding = np.load(npy_path)
                                if person_name not in self.sface_embeddings:
                                    self.sface_embeddings[person_name] = []
                                self.sface_embeddings[person_name].append(embedding)
                                person_has_images = True
                                continue
                            except Exception as e:
                                print(f"[IdentityManager] Failed to load cached SFace embedding: {e}")
                    else:
                        crop_path = img_path + ".lbph.png"
                        if os.path.exists(crop_path):
                            try:
                                gray_crop = cv2.imread(crop_path, cv2.IMREAD_GRAYSCALE)
                                if gray_crop is not None:
                                    faces_lbph.append(gray_crop)
                                    labels_lbph.append(current_id)
                                    person_has_images = True
                                    continue
                            except Exception as e:
                                print(f"[IdentityManager] Failed to load cached LBPH crop: {e}")

                    img = cv2.imread(img_path)
                    if img is None:
                        continue
                    
                    face_crop = self._extract_face_crop(img)
                    
                    if self.use_sface:
                        embedding = self._build_aligned_embedding(img)
                        if embedding is None:
                            # Fallback: Resize the unaligned crop to 112x112 if YuNet fails to locate landmarks.
                            aligned = cv2.resize(face_crop, (112, 112))
                            embedding = self._get_sface_recognizer().feature(aligned)
                        
                        try:
                            npy_path = img_path + ".sface.npy"
                            np.save(npy_path, embedding)
                        except Exception as e:
                            print(f"[IdentityManager] Failed to save cached embedding: {e}")
                        
                        if person_name not in self.sface_embeddings:
                            self.sface_embeddings[person_name] = []
                        self.sface_embeddings[person_name].append(embedding)
                    else:
                        gray_crop = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
                        gray_crop = cv2.resize(gray_crop, (150, 150))
                        gray_crop = cv2.equalizeHist(gray_crop)
                        
                        try:
                            crop_path = img_path + ".lbph.png"
                            cv2.imwrite(crop_path, gray_crop)
                        except Exception as e:
                            print(f"[IdentityManager] Failed to save cached LBPH crop: {e}")
                        
                        faces_lbph.append(gray_crop)
                        labels_lbph.append(current_id)
                    
                    person_has_images = True
                
                if person_has_images:
                    self.identity_map[current_id] = person_name
                    current_id += 1

        if self.use_sface:
            total = sum(len(v) for v in self.sface_embeddings.values())
            self.is_trained = total > 0
            if self.is_trained:
                print(f"[IdentityManager] Loaded {total} SFace embeddings for {len(self.sface_embeddings)} people.")
            else:
                print("[IdentityManager] No identities found to train.")
        else:
            if faces_lbph and labels_lbph:
                self.recognizer = cv2.face.LBPHFaceRecognizer_create(
                    radius=2, neighbors=8, grid_x=8, grid_y=8
                )
                self.recognizer.train(faces_lbph, np.array(labels_lbph))
                self.is_trained = True
                print(f"[IdentityManager] Trained LBPH on {len(faces_lbph)} images for {len(self.identity_map)} people.")
            else:
                self.is_trained = False
                print("[IdentityManager] No identities found to train.")

    def _build_aligned_embedding(self, img: np.ndarray):
        """
        Run YuNet on a reference image and use alignCrop to produce a
        geometrically aligned 112x112 face before computing the SFace
        embedding.  Returns None if no face is found.
        """
        yunet_path = resource_path("assets/face_detection_yunet_2023mar.onnx")
        if not os.path.exists(yunet_path):
            return None

        h_img, w_img = img.shape[:2]
        detector = cv2.FaceDetectorYN.create(
            model=yunet_path, config="",
            input_size=(w_img, h_img),
            score_threshold=0.50, nms_threshold=0.30, top_k=100,
        )
        _, dets = detector.detect(img)
        if dets is None or len(dets) == 0:
            return None

        best = max(dets, key=lambda d: d[2] * d[3])
        try:
            aligned = self._get_sface_recognizer().alignCrop(img, best)
            return self._get_sface_recognizer().feature(aligned)
        except Exception as e:
            print(f"[IdentityManager] alignCrop failed during embedding: {e}")
            return None

    def match_face_aligned(self, full_img: np.ndarray, det_row: np.ndarray,
                           num_faces: int = 1):
        """
        Match a detected face using the full YuNet detection row (bbox +
        landmarks + score) so that SFace can use alignCrop for proper
        geometric alignment before embedding.  Falls back to crop-based
        matching when SFace is unavailable.

        num_faces: total detections in the same image, used to select
        the appropriate margin strictness in _rank_sface_embedding.
        """
        if not self.is_trained or full_img is None:
            return None

        if self.use_sface:
            try:
                aligned = self._get_sface_recognizer().alignCrop(full_img, det_row)
                return self._match_sface_from_aligned(aligned, num_faces)
            except Exception as e:
                print(f"[IdentityManager] alignCrop match failed ({e}), falling back to crop.")
                x, y, w, h = int(det_row[0]), int(det_row[1]), int(det_row[2]), int(det_row[3])
                h_img, w_img = full_img.shape[:2]
                face_crop = full_img[max(0, y):min(h_img, y + h), max(0, x):min(w_img, x + w)]
                return self.match_face(face_crop)
        else:
            x, y, w, h = int(det_row[0]), int(det_row[1]), int(det_row[2]), int(det_row[3])
            h_img, w_img = full_img.shape[:2]
            face_crop = full_img[max(0, y):min(h_img, y + h), max(0, x):min(w_img, x + w)]
            return self._match_lbph(face_crop)

    def _match_sface_from_aligned(self, aligned_face: np.ndarray, num_faces: int = 1):
        """
        Compute SFace embedding from an already-aligned 112x112 BGR crop and
        match against all registered identities.
        """
        try:
            embedding = self._get_sface_recognizer().feature(aligned_face)
            return self._rank_sface_embedding(embedding, num_faces)
        except Exception as e:
            print(f"SFace aligned match failed: {e}")
            return None

    def match_face(self, face_image: np.ndarray):
        """
        Takes a BGR face crop, predicts identity.
        Returns the Name if confidence is high enough, else None.
        """
        if not self.is_trained or face_image is None:
            return None
        
        if self.use_sface:
            return self._match_sface(face_image)
        else:
            return self._match_lbph(face_image)

    def _rank_sface_embedding(self, embedding: np.ndarray,
                              num_faces: int = 1) -> Optional[str]:
        """
        Shared scoring logic for both aligned and crop-based SFace paths.

        Scoring strategy:
          - Per-identity score = MAX cosine similarity across all reference
            embeddings for that identity (preserves recall: one strong ref
            is enough to match a genuine face in challenging conditions).
          - Context-aware tiered margin against the second-best identity:
              * Strong score (> threshold+0.20): margin >= 0.08 (easy accept)
              * Borderline score, single-face image (num_faces == 1):
                margin >= 0.10 — portrait / solo shot, inherently lower false-
                positive risk, so a moderate gap suffices.
              * Borderline score, multi-face image (num_faces > 1):
                margin >= 0.20 — group photo, many competing faces, a large
                gap is required to avoid ambiguous matches.
          - Only one identity registered: margin check is skipped.
        """
        _STRONG_SCORE_OFFSET  = 0.20
        _MARGIN_STRONG        = 0.08
        _MARGIN_BORDERLINE_1  = 0.10   # Single-face image.
        _MARGIN_BORDERLINE_N  = 0.20   # Multi-face image.

        from PySide6.QtCore import QSettings
        settings = QSettings("SafeMARC", "SafeMARC")
        fm_val = float(settings.value("model_face_match", 0.40))

        # Find the highest matching cosine similarity score across reference embeddings.
        identity_scores = {}
        for name, ref_embeddings in self.sface_embeddings.items():
            scores = [
                float(self._get_sface_recognizer().match(
                    embedding, ref_emb, cv2.FaceRecognizerSF_FR_COSINE
                ))
                for ref_emb in ref_embeddings
            ]
            identity_scores[name] = max(scores)

        if not identity_scores:
            return None

        ranked      = sorted(identity_scores.items(), key=lambda x: x[1], reverse=True)
        best_name   = ranked[0][0]
        best_score  = ranked[0][1]
        second_score = ranked[1][1] if len(ranked) > 1 else -1.0
        margin = best_score - second_score

        # Check matched identity against context-aware tiered margin requirements.
        if len(ranked) == 1:
            margin_ok = True
        elif best_score > fm_val + _STRONG_SCORE_OFFSET:
            margin_ok = margin >= _MARGIN_STRONG
        else:
            # Group photos (multiple faces) enforce a stricter margin than solo portraits.
            min_margin = _MARGIN_BORDERLINE_1 if num_faces == 1 else _MARGIN_BORDERLINE_N
            margin_ok = margin >= min_margin

        matched = best_score > fm_val and margin_ok

        print(
            f"[DEBUG] SFace match: {best_name}, Score: {best_score:.4f} "
            f"(Threshold: {fm_val:.2f}, Margin: {margin:.4f}) "
            f"→ {'MATCH' if matched else 'REJECT'}"
        )
        return best_name if matched else None


    def _match_sface(self, face_image: np.ndarray) -> Optional[str]:
        """Crop-based SFace match used as fallback when alignCrop is unavailable."""
        try:
            aligned   = cv2.resize(face_image, (112, 112))
            embedding = self._get_sface_recognizer().feature(aligned)
            return self._rank_sface_embedding(embedding, num_faces=1)
        except Exception as e:
            print(f"SFace match failed: {e}")
            return None

    def _match_lbph(self, face_image: np.ndarray) -> Optional[str]:
        """Fallback LBPH matching."""
        try:
            gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, (150, 150))
            gray = cv2.equalizeHist(gray)
            
            label_id, confidence = self.recognizer.predict(gray)
            name = self.identity_map.get(label_id, "?")
            
            matched = confidence < 115.0
            print(f"[DEBUG] LBPH match: {name}, Distance: {confidence:.2f} → {'MATCH' if matched else 'REJECT'}")
            
            if matched:
                return name
        except Exception as e:
            print(f"LBPH match failed: {e}")
            
        return None

    def add_identity(self, name: str, image_paths: List[str]):
        """Adds a new identity folder and copies images into it."""
        person_dir = os.path.join(self.identities_dir, name)
        os.makedirs(person_dir, exist_ok=True)
        
        import shutil
        import glob
        
        existing_files = glob.glob(os.path.join(person_dir, "ref_*"))
        start_idx = len(existing_files)
        
        for i, path in enumerate(image_paths):
            ext = os.path.splitext(path)[1]
            target = os.path.join(person_dir, f"ref_{start_idx + i}{ext}")
            shutil.copy2(path, target)
            
        self.reload_identities()

    def add_session_identity(self, name: str, image_path: str):
        """Adds an identity that will be deleted when the app restarts."""
        session_dir = os.path.join(self.session_temp, name)
        os.makedirs(session_dir, exist_ok=True)
        
        import shutil
        import glob
        
        existing_files = glob.glob(os.path.join(session_dir, "temp_ref*"))
        start_idx = len(existing_files)
        
        ext = os.path.splitext(image_path)[1]
        target = os.path.join(session_dir, f"temp_ref_{start_idx}{ext}")
        shutil.copy2(image_path, target)
        
        self.reload_identities()
