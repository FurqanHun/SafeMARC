import os
import sys

# Add the project root directory to the python path so that 'src' can be imported during test collection
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
