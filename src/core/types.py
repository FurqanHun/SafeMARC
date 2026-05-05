from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class SensitiveHit:
    """Represents one found item (text or face)"""

    x: int
    y: int
    w: int
    h: int
    label: str  # e.g., "Phone", "CNIC", "Face"
    confidence: float
    text_content: str = ""  # Only for text hits
    identity: str = ""      # e.g., "John Doe" (if matched)
