import os
import tempfile
import fitz  # PyMuPDF
from PIL import Image

class PDFHandler:
    @staticmethod
    def extract_pages(pdf_path: str) -> list[dict]:
        """
        Extracts all pages of a PDF to a temporary directory as high-quality PNGs.
        Returns a list of dicts with file paths and word bounding boxes:
        [{"image_path": str, "words": list}]
        """
        doc = fitz.open(pdf_path)
        temp_dir = tempfile.mkdtemp(prefix="safemarc_pdf_")
        pages_data = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            # Increase resolution for better OCR and redaction accuracy
            zoom = 4.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            out_path = os.path.join(temp_dir, f"page_{page_num + 1}.png")
            pix.save(out_path)
            
            # Extract word level bounding boxes directly from PDF using PyMuPDF
            # page.get_text("words") returns list of tuples:
            # (x0, y0, x1, y1, "word", block_no, line_no, word_no)
            words = []
            for w in page.get_text("words"):
                x0, y0, x1, y1, text, block_no, line_no, word_no = w
                words.append((x0 * zoom, y0 * zoom, x1 * zoom, y1 * zoom, text, block_no, line_no, word_no))
                
            pages_data.append({
                "image_path": out_path,
                "words": words
            })
            
        return pages_data

    @staticmethod
    def extract_first_page(pdf_path: str) -> str:
        doc = fitz.open(pdf_path)
        if len(doc) > 0:
            temp_dir = tempfile.mkdtemp(prefix="safemarc_pdf_")
            page = doc.load_page(0)
            zoom = 4.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            out_path = os.path.join(temp_dir, "page_1.png")
            pix.save(out_path)
            return out_path
        return None

    @staticmethod
    def build_pdf(image_paths: list[str], output_pdf_path: str) -> bool:
        """
        Combines a list of image paths into a single PDF.
        """
        if not image_paths:
            return False
            
        try:
            # Ensure the output directory exists
            output_dir = os.path.dirname(output_pdf_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                
            # We use PIL to save the images as a multi-page PDF
            images = [Image.open(img_path).convert('RGB') for img_path in image_paths]
            if images:
                images[0].save(
                    output_pdf_path, 
                    save_all=True, 
                    append_images=images[1:]
                )
            return True
        except Exception as e:
            print(f"Failed to build PDF: {e}")
            return False
