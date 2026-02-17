from abc import ABC, abstractmethod
from typing import List

from src.core.types import SensitiveHit


class BaseDetector(ABC):
    @abstractmethod
    def detect(self, image_path: str) -> List[SensitiveHit]:
        """Input: Image path. Output: List of hits."""
        pass
