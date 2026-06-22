import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

try:
    from core.scanner import SafeScanner
    from core.types import SensitiveHit
except ImportError as e:
    print(f"❌ IMPORT ERROR: {e}")
    print("Did you run this from the root folder?")
    sys.exit(1)


def main():
    # Setup paths.
    input_image = "test_data/test.jpg"  # Input image path.
    output_image = "test_data/test_redacted.jpg"

    if not os.path.exists(input_image):
        print(f"❌ ERROR: I can't find '{input_image}'")
        print("Please put a file named 'test.jpg' in this folder.")
        return

    # Initialize the Engine.
    print("Initializing SafeScanner...")
    try:
        scanner = SafeScanner()
        print("✅ Scanner initialized (MediaPipe is working!)")
    except Exception as e:
        print(f"❌ CRASH during init: {e}")
        return

    # Run scan.
    print(f"Scanning '{input_image}'...")
    hits = scanner.scan(input_image)

    print(f"\n📊 FOUND {len(hits)} SENSITIVE ITEMS:")
    for i, hit in enumerate(hits):
        print(f"   {i + 1}. [{hit.label}] Confidence: {hit.confidence:.2f}")
        if hit.text_content:
            print(f"      Text: '{hit.text_content}'")
        print(f"      Box: x={hit.x}, y={hit.y}, w={hit.w}, h={hit.h}")

    if not hits:
        print("\n⚠️ No sensitive data found. Try a different image.")
        return

    # Run redaction.
    print("\n🎨 Redacting items...")
    success = scanner.redact(input_image, output_image, hits)

    if success:
        print(f"✅ SUCCESS! Redacted image saved to: {output_image}")
        print("Go open it and see the black boxes!")
    else:
        print("❌ Redaction failed.")


if __name__ == "__main__":
    main()
