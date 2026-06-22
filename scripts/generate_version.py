import subprocess
import re
from pathlib import Path
import sys

# Path to the root of the repository (assumed to be two levels up from this script)
ROOT = Path(__file__).resolve().parents[1]

# Read base version from setup.py
setup_path = ROOT / "setup.py"
setup_content = setup_path.read_text()
match = re.search(r'version\s*=\s*"([^"]+)"', setup_content)
if not match:
    sys.exit("Could not find version in setup.py")
base_version = match.group(1)

# Get short git SHA (8 characters)
sha = subprocess.check_output(["git", "rev-parse", "--short=8", "HEAD"], cwd=ROOT).decode().strip()

device_version = f"{base_version}+dev.{sha}"
print(device_version)
