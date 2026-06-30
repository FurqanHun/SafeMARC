import re
from typing import List, Optional

import pytesseract
from PIL import Image

from src.utils.paths import pytesseract_env
from src.core.detectors.base import BaseDetector
from src.core.types import SensitiveHit


class RegexDetector(BaseDetector):
    """Executes OCR and matches custom regular expressions or patterns against extracted text data."""

    def __init__(self) -> None:
        self.custom_patterns: List[dict] = []
        self.ocr_cache = {}
        self.cached_image_path: Optional[str] = None
        self._load_cache()

    def _load_cache(self) -> None:
        import os
        from PySide6.QtCore import QStandardPaths
        try:
            cache_dir = QStandardPaths.writableLocation(QStandardPaths.CacheLocation)
            if cache_dir:
                cache_file = os.path.join(cache_dir, "ocr_cache.json")
                if os.path.exists(cache_file):
                    os.remove(cache_file)
                    print("[RegexDetector] Cleaned up legacy disk OCR cache file.")
        except Exception as e:
            print(f"[RegexDetector] Failed to clean up legacy disk cache: {e}")
        self.ocr_cache = {}

    def save_cache(self) -> None:
        import os
        from PySide6.QtCore import QStandardPaths
        try:
            cache_dir = QStandardPaths.writableLocation(QStandardPaths.CacheLocation)
            if cache_dir:
                cache_file = os.path.join(cache_dir, "ocr_cache.json")
                if os.path.exists(cache_file):
                    os.remove(cache_file)
        except Exception:
            pass

    def add_custom_pattern(self, label: str, pattern: str, is_regex: bool = False, is_whole_word: bool = False, keywords: Optional[List[str]] = None) -> None:
        if not is_regex:
            pattern = re.escape(pattern)
            if is_whole_word:
                pattern = r'(?<!\w)' + pattern + r'(?!\w)'
            
        try:
            compiled = re.compile(pattern, re.IGNORECASE)
            self.custom_patterns.append({
                "label": label,
                "pattern": compiled,
                "keywords": keywords or []
            })
        except re.error as e:
            print(f"Failed to compile regex pattern '{pattern}': {e}")

    def clear_custom_patterns(self) -> None:
        self.custom_patterns.clear()

    def detect(self, image_path: str, pdf_words: Optional[list] = None) -> List[SensitiveHit]:
        self.cached_image_path = image_path
        if not self.custom_patterns:
            return []
            
        if image_path in self.ocr_cache:
            hits = []
            for data, scale in self.ocr_cache[image_path]:
                hits.extend(self._scan_data_dict(data, scale))
        else:
            hits = []
            new_cached_list = []
            
            if pdf_words:
                data = {
                    "text": [],
                    "level": [],
                    "block_num": [],
                    "par_num": [],
                    "line_num": [],
                    "left": [],
                    "top": [],
                    "width": [],
                    "height": [],
                    "conf": []
                }
                for w in pdf_words:
                    x0, y0, x1, y1, word_text, block_no, line_no, word_no = w
                    data["text"].append(word_text)
                    data["level"].append(5)
                    data["block_num"].append(block_no)
                    data["par_num"].append(0)
                    data["line_num"].append(line_no)
                    data["left"].append(int(x0))
                    data["top"].append(int(y0))
                    data["width"].append(int(x1 - x0))
                    data["height"].append(int(y1 - y0))
                    data["conf"].append(100.0)
                
                new_cached_list.append((data, 1.0))
                digital_hits = self._scan_data_dict(data, scale=1.0)
                hits.extend(digital_hits)

            import cv2
            import numpy as np
            from PIL import Image

            cv_img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if cv_img is not None:
                h_orig, w_orig = cv_img.shape[:2]
                max_dim = max(h_orig, w_orig)
                if max_dim >= 2000:
                    scale = 1.0
                elif max_dim >= 1000:
                    scale = 1.5
                else:
                    scale = 2.0

                if scale != 1.0:
                    cv_img = cv2.resize(cv_img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
                _, thresh = cv2.threshold(cv_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                img = Image.fromarray(thresh)
                
                try:
                    with pytesseract_env():
                        ocr_data = pytesseract.image_to_data(img, config="--psm 3", output_type=pytesseract.Output.DICT)
                    new_cached_list.append((ocr_data, scale))
                    ocr_hits = self._scan_data_dict(ocr_data, scale=scale)
                    hits.extend(ocr_hits)
                except Exception as e:
                    print(f"Tesseract OCR failed: {e}")

            from PySide6.QtCore import QSettings
            settings = QSettings("SafeMARC", "SafeMARC")
            
            try:
                import psutil
                tot_ram = psutil.virtual_memory().total / (1024 ** 3)
            except Exception:
                tot_ram = 8.0
            
            default_cache = 50 if tot_ram < 8.0 else (100 if tot_ram <= 16.0 else 200)
            max_cache_size = int(settings.value("max_ocr_cache_pages", default_cache))
            self.ocr_cache[image_path] = new_cached_list
            while len(self.ocr_cache) > max_cache_size:
                oldest = next(iter(self.ocr_cache))
                self.ocr_cache.pop(oldest)

        def boxes_overlap_heavily(b1: SensitiveHit, b2: SensitiveHit) -> bool:
            x_left = max(b1.x, b2.x)
            y_top = max(b1.y, b2.y)
            x_right = min(b1.x + b1.w, b2.x + b2.w)
            y_bottom = min(b1.y + b1.h, b2.y + b2.h)
            
            if x_right < x_left or y_bottom < y_top:
                return False
                
            intersect_area = (x_right - x_left) * (y_bottom - y_top)
            b1_area = b1.w * b1.h
            b2_area = b2.w * b2.h
            
            if b1_area == 0 or b2_area == 0:
                return False
                
            overlap_ratio_1 = intersect_area / b1_area
            overlap_ratio_2 = intersect_area / b2_area
            return overlap_ratio_1 > 0.40 or overlap_ratio_2 > 0.40

        unique_hits = []
        for h in hits:
            is_dup = False
            for idx, uh in enumerate(unique_hits):
                if boxes_overlap_heavily(uh, h):
                    is_dup = True
                    if h.confidence > uh.confidence:
                        unique_hits[idx] = h
                    break
            if not is_dup:
                unique_hits.append(h)
                
        return unique_hits

    def _scan_data_dict(self, data: dict, scale: float) -> List[SensitiveHit]:
        hits = []
        n_boxes = len(data["text"])
        if n_boxes == 0:
            return []
            
        lines = {}
        for i in range(n_boxes):
            if int(data['level'][i]) == 5:
                text = str(data["text"][i]).strip()
                if not text:
                    continue
                
                key = (data['block_num'][i], data['par_num'][i], data['line_num'][i])
                if key not in lines:
                    lines[key] = []
                lines[key].append(i)

        for key, word_indices in lines.items():
            line_text = ""
            char_to_word_idx = []
            
            for word_idx in word_indices:
                word = str(data["text"][word_idx]).strip()
                line_text += word + " "
                
                for _ in word:
                    char_to_word_idx.append(word_idx)
                char_to_word_idx.append(word_idx)

            line_text = line_text.strip()
            
            for pat_dict in self.custom_patterns:
                label = pat_dict["label"]
                pattern = pat_dict["pattern"]
                keywords = pat_dict.get("keywords", [])
                
                for match in pattern.finditer(line_text):
                    start_char = match.start()
                    end_char = match.end() - 1
                    
                    if start_char >= len(char_to_word_idx) or end_char >= len(char_to_word_idx):
                        continue
                        
                    start_word_idx = char_to_word_idx[start_char]
                    end_word_idx = char_to_word_idx[end_char]
                    
                    x_coords = []
                    y_coords = []
                    x2_coords = []
                    y2_coords = []
                    confs = []
                    
                    in_range = False
                    for w_idx in word_indices:
                        if w_idx == start_word_idx:
                            in_range = True
                            
                        if in_range:
                            x = int(data['left'][w_idx] / scale)
                            y = int(data['top'][w_idx] / scale)
                            w = int(data['width'][w_idx] / scale)
                            h = int(data['height'][w_idx] / scale)
                            x_coords.append(x)
                            y_coords.append(y)
                            x2_coords.append(x + w)
                            y2_coords.append(y + h)
                            try:
                                conf_val = float(data['conf'][w_idx])
                            except (ValueError, TypeError):
                                conf_val = 100.0
                            confs.append(conf_val)
                            
                        if w_idx == end_word_idx:
                            break
                            
                    if x_coords:
                        min_x = min(x_coords)
                        min_y = min(y_coords)
                        max_x = max(x2_coords)
                        max_y = max(y2_coords)
                        avg_conf = sum(confs) / len(confs) if confs else 100.0
                        
                        match_text = match.group()
                        
                        final_confidence = avg_conf
                        
                        if label == "Credit Card":
                            digits = [int(d) for d in match_text if d.isdigit()]
                            if len(digits) >= 13 and len(digits) <= 19:
                                checksum = 0
                                for i, d in enumerate(digits[::-1]):
                                    if i % 2 == 1:
                                        d *= 2
                                        if d > 9:
                                            d -= 9
                                    checksum += d
                                if checksum % 10 == 0:
                                    final_confidence = 95.0
                                else:
                                    continue
                            else:
                                continue
                        elif label == "EU IBAN":
                            iban_clean = match_text.replace(" ", "").replace("-", "").upper()
                            if len(iban_clean) >= 15:
                                rearranged = iban_clean[4:] + iban_clean[:4]
                                numeric_str = ""
                                for c in rearranged:
                                    if c.isdigit():
                                        numeric_str += c
                                    else:
                                        numeric_str += str(ord(c) - 55)
                                try:
                                    if int(numeric_str) % 97 == 1:
                                        final_confidence = 95.0
                                    else:
                                        continue
                                except ValueError:
                                    continue
                            else:
                                continue
                        
                        elif label in ("US SSN", "IN Aadhaar"):
                            window_start = max(0, start_char - 35)
                            window_end = min(len(line_text), match.end() + 35)
                            context_window = line_text.lower()[window_start:window_end]
                            has_keyword = any(kw.lower() in context_window for kw in keywords)
                            final_confidence = 90.0 if has_keyword else 25.0
                        
                        elif keywords:
                            window_start = max(0, start_char - 35)
                            window_end = min(len(line_text), match.end() + 35)
                            context_window = line_text.lower()[window_start:window_end]
                            
                            has_keyword = any(kw.lower() in context_window for kw in keywords)
                            final_confidence = 90.0 if has_keyword else 30.0

                        hits.append(
                            SensitiveHit(
                                x=min_x,
                                y=min_y,
                                w=max_x - min_x,
                                h=max_y - min_y,
                                label=label,
                                confidence=final_confidence,
                                text_content=match_text,
                            )
                        )
        return hits
