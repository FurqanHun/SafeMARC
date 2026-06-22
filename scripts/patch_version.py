import sys
import re
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python patch_version.py <version>")

    new_version = sys.argv[1]
    ROOT = Path(__file__).resolve().parents[1]

    # 1. Patch setup.py
    setup_path = ROOT / "setup.py"
    if setup_path.exists():
        content = setup_path.read_text(encoding="utf-8")
        # Support single or double quotes
        content = re.sub(r'version\s*=\s*["\'][^"\']+["\']', f'version="{new_version}"', content)
        setup_path.write_text(content, encoding="utf-8")
        print(f"Patched setup.py to version {new_version}")

    # 2. Patch src/version.py
    version_path = ROOT / "src" / "version.py"
    version_path.write_text(f'__version__ = "{new_version}"\n', encoding="utf-8")
    print(f"Patched src/version.py to version {new_version}")

if __name__ == "__main__":
    main()
