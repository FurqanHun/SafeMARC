import os
from typing import List, Generator, Tuple

from src.core.scanner import SafeScanner
from src.core.types import SensitiveHit
import logging
logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.pdf', '.webp', '.bmp', '.tiff'}

class BatchProcessor:
    """Coordinates recursive file discovery, path resolution, and batch processing pipelines."""

    def __init__(self, scanner: SafeScanner = None):
        self.scanner = scanner or SafeScanner()

    def _get_supported_files(self, input_path: str) -> List[str]:
        logger.debug(f"Discovering supported files in: {input_path}")
        files = []
        if os.path.isfile(input_path):
            _, ext = os.path.splitext(input_path)
            if ext.lower() in SUPPORTED_EXTENSIONS:
                files.append(input_path)
            else:
                logger.warning(f"File {input_path} has unsupported extension.")
        elif os.path.isdir(input_path):
            for root, _, filenames in os.walk(input_path):
                for filename in filenames:
                    _, ext = os.path.splitext(filename)
                    if ext.lower() in SUPPORTED_EXTENSIONS:
                        files.append(os.path.join(root, filename))
        
        logger.info(f"Discovered {len(files)} supported files for processing.")
        return files

    def get_output_path(self, input_path: str, output_dir: str = None, use_suffix: bool = False) -> str:
        """Resolves the destination path based on output constraints and suffix requirements."""
        base_dir = os.path.dirname(input_path)
        file_name = os.path.basename(input_path)
        name, ext = os.path.splitext(file_name)

        out_name = f"{name}_safemarc_redacted{ext}" if use_suffix else file_name

        if output_dir:
            return os.path.join(output_dir, out_name)
        elif use_suffix:
            return os.path.join(base_dir, out_name)
        else:
            new_dir = os.path.join(base_dir, "safemarc_redacted_output")
            return os.path.join(new_dir, out_name)

    def process(self, input_path: str, output_dir: str = None, use_suffix: bool = False) -> Generator[Tuple[str, bool, str], None, None]:
        """
        Yields (file_path, success, message) for each processed file.
        """
        files = self._get_supported_files(input_path)
        
        if not files:
            logger.warning(f"No supported files found in: {input_path}")
            yield input_path, False, "No supported files found."
            return

        logger.info(f"Starting batch process on {len(files)} files.")
        for file_path in files:
            try:
                out_path = self.get_output_path(file_path, output_dir, use_suffix)
                hits = self.scanner.scan(file_path)
                if not hits:
                    yield file_path, True, "No sensitive data found."
                    continue

                success = self.scanner.redact(file_path, out_path, hits)
                if success:
                    yield file_path, True, f"Redacted {len(hits)} items. Saved to {out_path}"
                else:
                    yield file_path, False, "Failed to save redacted file."
            except Exception as e:
                yield file_path, False, f"Error: {e}"
