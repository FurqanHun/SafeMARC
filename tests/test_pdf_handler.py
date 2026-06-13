import os
import tempfile
import pytest
import fitz
from src.utils.pdf_handler import PDFHandler


@pytest.fixture
def sample_pdf_path():
    # Write a test PDF using PyMuPDF to test text/coord extraction in sandbox
    temp_dir = tempfile.mkdtemp()
    pdf_path = os.path.join(temp_dir, "test_doc.pdf")
    
    doc = fitz.open()
    page1 = doc.new_page()
    page1.insert_text((50, 50), "First Page text content")
    page2 = doc.new_page()
    page2.insert_text((50, 50), "Second Page text content")
    
    doc.save(pdf_path)
    doc.close()
    
    yield pdf_path
    
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
    os.rmdir(temp_dir)


def test_extract_pages(sample_pdf_path):
    pages_data = PDFHandler.extract_pages(sample_pdf_path)
    
    assert len(pages_data) == 2
    assert "image_path" in pages_data[0]
    assert "words" in pages_data[0]
    assert os.path.exists(pages_data[0]["image_path"])
    assert pages_data[0]["image_path"].endswith(".png")
    
    words = pages_data[0]["words"]
    assert len(words) > 0
    assert len(words[0]) == 8
    assert "First" in [w[4] for w in words]
    
    for page in pages_data:
        if os.path.exists(page["image_path"]):
            os.remove(page["image_path"])
        parent_dir = os.path.dirname(page["image_path"])
        if os.path.exists(parent_dir):
            try:
                os.rmdir(parent_dir)
            except OSError:
                pass


def test_extract_first_page(sample_pdf_path):
    img_path = PDFHandler.extract_first_page(sample_pdf_path)
    assert img_path is not None
    assert os.path.exists(img_path)
    assert img_path.endswith(".png")
    
    os.remove(img_path)
    parent_dir = os.path.dirname(img_path)
    if os.path.exists(parent_dir):
        try:
            os.rmdir(parent_dir)
        except OSError:
            pass


def test_build_pdf():
    from PIL import Image
    temp_dir = tempfile.mkdtemp()
    
    img1_path = os.path.join(temp_dir, "img1.png")
    img2_path = os.path.join(temp_dir, "img2.png")
    
    Image.new("RGB", (100, 100), color="blue").save(img1_path)
    Image.new("RGB", (100, 100), color="red").save(img2_path)
    
    output_pdf = os.path.join(temp_dir, "output.pdf")
    
    success = PDFHandler.build_pdf([img1_path, img2_path], output_pdf)
    assert success is True
    assert os.path.exists(output_pdf)
    
    doc = fitz.open(output_pdf)
    assert len(doc) == 2
    doc.close()
    
    os.remove(img1_path)
    os.remove(img2_path)
    os.remove(output_pdf)
    os.rmdir(temp_dir)
