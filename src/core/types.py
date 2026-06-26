from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class SensitiveHit:
    """Represents a detected sensitive item."""

    x: int
    y: int
    w: int
    h: int
    label: str
    confidence: float
    text_content: str = ""
    identity: str = ""
