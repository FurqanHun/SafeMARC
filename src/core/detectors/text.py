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
            
        if pdf_words:
            # Reconstruct Tesseract-like 'data' dictionary directly from native PDF words
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

            scale = 1.0
        else:
            import cv2
            import numpy as np
            from PIL import Image

            # Pre-process image via OpenCV for highest character recognition accuracy
            cv_img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if cv_img is None:
                return []
                
            scale = 2.0
            # Upscale 2x to help Tesseract detect small text and handwriting
            cv_img = cv2.resize(cv_img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            
            # Apply Otsu's thresholding to get high-contrast black-and-white
            _, thresh = cv2.threshold(cv_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            img = Image.fromarray(thresh)
            
            # Run Tesseract OCR with fully automatic page segmentation
            data = pytesseract.image_to_data(img, config="--psm 3", output_type=pytesseract.Output.DICT)

        hits = []
        n_boxes = len(data["text"])
        
        # 1. Group words by line to support multi-word phrase matching
        lines = {}
        for i in range(n_boxes):
            if int(data['level'][i]) == 5: # 5 means word level
                text = data["text"][i].strip()
                if not text:
                    continue
                
                key = (data['block_num'][i], data['par_num'][i], data['line_num'][i])
                if key not in lines:
                    lines[key] = []
                lines[key].append(i)

        # 2. Process each line
        for key, word_indices in lines.items():
            line_text = ""
            char_to_word_idx = []
            
            # Build full text for the line and map character indices to word indices
            for word_idx in word_indices:
                word = data["text"][word_idx].strip()
                line_text += word + " "
                
                # Map every character in this word to its bounding box index
                for _ in word:
                    char_to_word_idx.append(word_idx)
                # Map the trailing space to this word's index as well
                char_to_word_idx.append(word_idx)

            line_text = line_text.strip()
            
            # 3. Match patterns against the reconstructed line
            for pat_dict in self.custom_patterns:
                label = pat_dict["label"]
                pattern = pat_dict["pattern"]
                
                for match in pattern.finditer(line_text):
                    start_char = match.start()
                    end_char = match.end() - 1 # inclusive index of last char
                    
                    if start_char >= len(char_to_word_idx) or end_char >= len(char_to_word_idx):
                        continue
                        
                    # Find which words comprise this match span
                    start_word_idx = char_to_word_idx[start_char]
                    end_word_idx = char_to_word_idx[end_char]
                    
                    # Compute a single bounding box encompassing all words in the span
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
                            confs.append(float(data['conf'][w_idx]))
                            
                        if w_idx == end_word_idx:
                            break
                            
                    if x_coords:
                        min_x = min(x_coords)
                        min_y = min(y_coords)
                        max_x = max(x2_coords)
                        max_y = max(y2_coords)
                        avg_conf = sum(confs) / len(confs)
                        
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
