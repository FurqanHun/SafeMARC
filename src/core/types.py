from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class SensitiveHit:
    """Represents a detected sensitive item."""

    x: int
    y: int
    w: int
    h: int
    label: str  # Category label.
    confidence: float
    text_content: str = ""  # Text content associated with the hit.
    identity: str = ""      # Matched identity name.
