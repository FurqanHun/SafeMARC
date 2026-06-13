import os
import sys
import shutil
import tempfile
import pytest

# Add the project root directory to the python path to import 'src' during test collection.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def pytest_sessionfinish(session, exitstatus):
    """Clear all temporary test files generated during the test session."""
    temp_dir = os.path.join(tempfile.gettempdir(), "safemarc_temp")
    if os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)
            tr = session.config.pluginmanager.get_plugin("terminalreporter")
            if tr:
                tr.write_line(f"\n[Cleanup] Cleared temporary test files at {temp_dir}")
        except Exception as e:
            tr = session.config.pluginmanager.get_plugin("terminalreporter")
            if tr:
                tr.write_line(f"\n[Cleanup] Failed to clear temporary test files: {e}")
