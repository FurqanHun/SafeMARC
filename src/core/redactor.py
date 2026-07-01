import logging
logger = logging.getLogger(__name__)
import os
from typing import List

import cv2

from src.core.types import SensitiveHit


class Redactor:
    """Applies destructive pixel-level obfuscation to image arrays based on coordinate hits."""

    def apply(
        self, input_path: str, output_path: str, hits: List[SensitiveHit]
    ) -> bool:
        """
        Draws black boxes on the detected areas.
        Returns True if successful.
        """
        image = cv2.imread(input_path)

        if image is None:
            logger.error(f"Error: Could not read image at {input_path}")
            return False

        for hit in hits:
            cv2.rectangle(
                image, (hit.x, hit.y), (hit.x + hit.w, hit.y + hit.h), (0, 0, 0), -1
            )

        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        try:
            success = cv2.imwrite(output_path, image)
            if success:
                logger.success(f"Redacted image saved to: {output_path}")
                return True
            else:
                logger.error(f"Failed to save image to: {output_path}")
                return False
        except Exception as e:
            logger.error(f"Failed to save image to {output_path}: {e}")
            return False
