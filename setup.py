from setuptools import find_packages, setup

setup(
    name="SafeMARC",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "PySide6",
        "pymupdf",
        "opencv-python",
        "mediapipe",
        "pytesseract",
        "numpy",
        "Pillow",
    ],
    entry_points={
        "console_scripts": [
            "safemarc=main:main",
        ],
    },
)
