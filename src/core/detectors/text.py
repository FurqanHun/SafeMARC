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

    def detect(self, image_path: str) -> List[SensitiveHit]:
        if not self.custom_patterns:
            return []
            
        img = Image.open(image_path)
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

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
                            x = data['left'][w_idx]
                            y = data['top'][w_idx]
                            w = data['width'][w_idx]
                            h = data['height'][w_idx]
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
