import re
from typing import List

import pytesseract
from PIL import Image

from src.core.detectors.base import BaseDetector
from src.core.types import SensitiveHit


class RegexDetector(BaseDetector):
    def __init__(self):
        # We will store a list of dicts: {"label": str, "pattern": compiled_re}
        self.custom_patterns = []
        # Cache for currently loaded image/page to make real-time updates instantaneous
        self.cached_image_path = None
        self.cached_pdf_words = None
        self.cached_data_list = [] # List of tuples: (data_dict, scale)

    def add_custom_pattern(self, label: str, pattern: str, is_regex: bool = False, is_whole_word: bool = False):
        if not is_regex:
            # Escape literal text so special regex characters don't break
            pattern = re.escape(pattern)
            if is_whole_word:
                # Use lookarounds to ensure it's not surrounded by word characters
                pattern = r'(?<!\w)' + pattern + r'(?!\w)'
            
        # We compile with re.IGNORECASE for user convenience
        try:
            compiled = re.compile(pattern, re.IGNORECASE)
            self.custom_patterns.append({"label": label, "pattern": compiled})
        except re.error as e:
            print(f"Failed to compile regex pattern '{pattern}': {e}")

    def clear_custom_patterns(self):
        self.custom_patterns.clear()

    def detect(self, image_path: str, pdf_words: list = None) -> List[SensitiveHit]:
        if not self.custom_patterns:
            return []
            
        # Check if we can reuse the cached word-extraction dictionaries for the active page
        if (image_path == self.cached_image_path and 
            (pdf_words is self.cached_pdf_words or 
             (pdf_words is not None and self.cached_pdf_words is not None and len(pdf_words) == len(self.cached_pdf_words)))):
            hits = []
            for data, scale in self.cached_data_list:
                hits.extend(self._scan_data_dict(data, scale))
        else:
            hits = []
            new_cached_list = []
            
            # --- 1. PyMuPDF Digital Text Layer Scanning ---
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
                    data["level"].append(5) # 5 means word level
                    data["block_num"].append(block_no)
                    data["par_num"].append(0)
                    data["line_num"].append(line_no)
                    data["left"].append(int(x0))
                    data["top"].append(int(y0))
                    data["width"].append(int(x1 - x0))
                    data["height"].append(int(y1 - y0))
                    data["conf"].append(100.0) # Native text has 100% confidence
                
                new_cached_list.append((data, 1.0))
                digital_hits = self._scan_data_dict(data, scale=1.0)
                hits.extend(digital_hits)

            # --- 2. Tesseract OCR Image Layer Scanning (Best of Both Worlds) ---
            import cv2
            import numpy as np
            from PIL import Image

            cv_img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if cv_img is not None:
                scale = 2.0
                cv_img = cv2.resize(cv_img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
                _, thresh = cv2.threshold(cv_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                img = Image.fromarray(thresh)
                
                try:
                    ocr_data = pytesseract.image_to_data(img, config="--psm 3", output_type=pytesseract.Output.DICT)
                    new_cached_list.append((ocr_data, scale))
                    ocr_hits = self._scan_data_dict(ocr_data, scale=scale)
                    hits.extend(ocr_hits)
                except Exception as e:
                    print(f"Tesseract OCR failed: {e}")

            # Update cache
            self.cached_image_path = image_path
            self.cached_pdf_words = pdf_words
            self.cached_data_list = new_cached_list

        # --- 3. Near-Duplicate Box Deduplication with Coordinate Tolerance ---
        unique_hits = []
        for h in hits:
            is_dup = False
            for uh in unique_hits:
                if uh.label == h.label and abs(uh.x - h.x) <= 4 and abs(uh.y - h.y) <= 4 and abs(uh.w - h.w) <= 8 and abs(uh.h - h.h) <= 8:
                    is_dup = True
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
            if int(data['level'][i]) == 5: # 5 means word level
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
                        
                        hits.append(
                            SensitiveHit(
                                x=min_x,
                                y=min_y,
                                w=max_x - min_x,
                                h=max_y - min_y,
                                label=label,
                                confidence=avg_conf,
                                text_content=match.group(),
                            )
                        )
        return hits
