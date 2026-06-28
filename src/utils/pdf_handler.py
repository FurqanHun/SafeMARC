import os
import tempfile
from typing import List, Dict, Optional, Tuple, Callable
import fitz  # PyMuPDF
from PIL import Image

class PDFHandler:
    @staticmethod
    def extract_pages(pdf_path: str, progress_callback: Optional[Callable[[int, int], None]] = None) -> List[Dict]:
        """
        Extracts all pages of a PDF to a temporary directory as high-quality PNGs.
        Returns a list of dicts with file paths and word bounding boxes:
        [{"image_path": str, "words": list}]
        """
        from PySide6.QtCore import QSettings
        settings = QSettings("SafeMARC", "SafeMARC")
        zoom = float(settings.value("pdf_extract_zoom", 2.0))

        doc = fitz.open(pdf_path)
        safemarc_temp = os.path.join(tempfile.gettempdir(), "safemarc_temp", "pdf")
        os.makedirs(safemarc_temp, exist_ok=True)
        temp_dir = tempfile.mkdtemp(prefix="safemarc_pdf_", dir=safemarc_temp)
        pages_data = []
        
        try:
            for page_num in range(len(doc)):
                if progress_callback:
                    try:
                        progress_callback(page_num + 1, len(doc))
                    except Exception:
                        pass
                page = doc.load_page(page_num)
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                
                out_path = os.path.join(temp_dir, f"page_{page_num + 1}.png")
                pix.save(out_path)
                
                # Extract word bounding boxes: (x0, y0, x1, y1, text, block, line, word).
                words = []
                for w in page.get_text("words"):
                    x0, y0, x1, y1, text, block_no, line_no, word_no = w
                    words.append((x0 * zoom, y0 * zoom, x1 * zoom, y1 * zoom, text, block_no, line_no, word_no))
                    
                rect = page.rect
                pages_data.append({
                    "image_path": out_path,
                    "words": words,
                    "width": rect.width,
                    "height": rect.height
                })
        finally:
            doc.close()
            
        return pages_data

    @staticmethod
    def extract_first_page(pdf_path: str) -> Optional[str]:
        doc = fitz.open(pdf_path)
        try:
            if len(doc) > 0:
                from PySide6.QtCore import QSettings
                settings = QSettings("SafeMARC", "SafeMARC")
                zoom = float(settings.value("pdf_extract_zoom", 2.0))

                safemarc_temp = os.path.join(tempfile.gettempdir(), "safemarc_temp", "pdf")
                os.makedirs(safemarc_temp, exist_ok=True)
                temp_dir = tempfile.mkdtemp(prefix="safemarc_pdf_", dir=safemarc_temp)
                page = doc.load_page(0)
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                out_path = os.path.join(temp_dir, "page_1.png")
                pix.save(out_path)
                return out_path
        finally:
            doc.close()
        return None

    @staticmethod
    def build_pdf(image_paths: List[str], output_pdf_path: str, page_sizes: Optional[List[Tuple[float, float]]] = None) -> bool:
        """
        Combines a list of image paths into a single PDF.
        """
        if not image_paths:
            return False
            
        temp_files = []
        doc = None
        try:
            output_dir = os.path.dirname(output_pdf_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            doc = fitz.open()
            for idx, img_path in enumerate(image_paths):
                import time
                time.sleep(0.01)
                fd, temp_jpg = tempfile.mkstemp(suffix=".jpg")
                os.close(fd)
                temp_files.append(temp_jpg)
                
                with Image.open(img_path) as img:
                    width, height = img.size
                    
                    if page_sizes and idx < len(page_sizes):
                        orig_w, orig_h = page_sizes[idx]
                    else:
                        from PySide6.QtCore import QSettings
                        settings = QSettings("SafeMARC", "SafeMARC")
                        zoom_factor = float(settings.value("pdf_extract_zoom", 2.0))
                        if width > 1500 or height > 1500:
                            orig_w, orig_h = width / zoom_factor, height / zoom_factor
                        else:
                            orig_w, orig_h = width, height
                            
                    # Downscale extracted PDF pages to 2x zoom to optimize final file size
                    is_pdf_extracted = (page_sizes is not None) or (width > 1500 or height > 1500)
                    if is_pdf_extracted:
                        target_w = int(orig_w * 2.0)
                        target_h = int(orig_h * 2.0)
                        if width > target_w and height > target_h:
                            img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                            
                    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                        bg = Image.new("RGB", img.size, (255, 255, 255))
                        bg.paste(img, mask=img.split()[-1])
                        bg.save(temp_jpg, "JPEG", quality=85)
                    else:
                        img.convert("RGB").save(temp_jpg, "JPEG", quality=85)
                        
                p_width, p_height = orig_w, orig_h
                        
                page = doc.new_page(width=p_width, height=p_height)
                page.insert_image(page.rect, filename=temp_jpg)
                
            doc.save(output_pdf_path, garbage=4, deflate=True)
            return True
        except Exception as e:
            print(f"Failed to build PDF: {e}")
            return False
        finally:
            if doc is not None:
                try:
                    doc.close()
                except Exception:
                    pass
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception:
                    pass
