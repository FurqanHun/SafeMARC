import os
import cv2
import numpy as np
import threading
from typing import List, Dict, Optional
from src.utils.paths import resource_path, get_app_data_dir


class IdentityManager:
    def __init__(self, identities_dir: str = None):
        self.identities_dir = os.path.abspath(identities_dir) if identities_dir else os.path.join(get_app_data_dir(), "identities")
        os.makedirs(self.identities_dir, exist_ok=True)
        
        import tempfile
        self.session_temp = os.path.join(tempfile.gettempdir(), "safemarc_temp", "session_temp")
        os.makedirs(self.session_temp, exist_ok=True)
        
        self.identity_map = {}  # int id -> str Name
        self.is_trained = False
        self._local = threading.local()
        
        self.use_sface = False
        self.sface_recognizer = None
        self.sface_embeddings = {}  # name -> list of embeddings
        
        sface_model = resource_path("assets/face_recognition_sface_2021dec.onnx")
        if os.path.exists(sface_model):
            try:
                self.sface_recognizer = cv2.FaceRecognizerSF.create(sface_model, "")
                self.use_sface = True
                print("[IdentityManager] Using SFace deep learning model for recognition.")
            except Exception as e:
                print(f"[IdentityManager] SFace init failed ({e}), falling back to LBPH.")
        if not self.use_sface:
            print("[IdentityManager] Using LBPH fallback (less accurate).")
            self.recognizer = cv2.face.LBPHFaceRecognizer_create(
                radius=2, neighbors=8, grid_x=8, grid_y=8
            )
        
        self.reload_identities()

    def _extract_face_crop(self, img):
        """Extract the largest face crop from an image using a robust high-recall multi-cascade ensemble. Returns BGR crop."""
        if not hasattr(self._local, "face_cascade"):
            self._local.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            self._local.face_cascade_alt = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml'
            )
            self._local.profile_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_profileface.xml'
            )
            
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h_img, w_img = gray.shape[:2]
        
        faces_default = self._local.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4)
        faces_alt = self._local.face_cascade_alt.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4)
        faces_profile = self._local.profile_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4)
        
        flipped_gray = cv2.flip(gray, 1)
        faces_profile_flipped = self._local.profile_cascade.detectMultiScale(flipped_gray, scaleFactor=1.1, minNeighbors=4)
        
        all_faces = []
        for (x, y, w, h) in faces_default:
            all_faces.append((int(x), int(y), int(w), int(h)))
        for (x, y, w, h) in faces_alt:
            all_faces.append((int(x), int(y), int(w), int(h)))
        for (x, y, w, h) in faces_profile:
            all_faces.append((int(x), int(y), int(w), int(h)))
        for (x, y, w, h) in faces_profile_flipped:
            orig_x = w_img - x - w
            all_faces.append((int(orig_x), int(y), int(w), int(h)))
            
        if len(all_faces) > 0:
            x, y, w, h = max(all_faces, key=lambda f: f[2] * f[3])
            clip_y = max(0, y)
            clip_h = min(h_img - clip_y, h)
            clip_x = max(0, x)
            clip_w = min(w_img - clip_x, w)
            return img[clip_y:clip_y+clip_h, clip_x:clip_x+clip_w]
            
        return img

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
                        aligned = cv2.resize(face_crop, (112, 112))
                        embedding = self.sface_recognizer.feature(aligned)
                        
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

    def match_face(self, face_image: np.ndarray) -> Optional[str]:
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

    def _match_sface(self, face_image: np.ndarray) -> Optional[str]:
        """Match using SFace deep learning embeddings."""
        try:
            aligned = cv2.resize(face_image, (112, 112))
            embedding = self.sface_recognizer.feature(aligned)
            
            best_name = None
            best_score = -1.0
            
            for name, ref_embeddings in self.sface_embeddings.items():
                for ref_emb in ref_embeddings:
                    score = self.sface_recognizer.match(
                        embedding, ref_emb, cv2.FaceRecognizerSF_FR_COSINE
                    )
                    if score > best_score:
                        best_score = score
                        best_name = name
            
            from PySide6.QtCore import QSettings
            settings = QSettings("SafeMARC", "SafeMARC")
            fm_val = float(settings.value("model_face_match", 0.36))
            matched = best_score > fm_val
            print(f"[DEBUG] SFace match: {best_name}, Score: {best_score:.4f} (Threshold: {fm_val:.2f}) → {'MATCH' if matched else 'REJECT'}")
            
            if matched:
                return best_name
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
