import sys

print(f"🐍 Python Executable: {sys.executable}")

try:
    import mediapipe

    print(f"✅ MediaPipe Imported successfully.")
    print(f"📂 Location: {mediapipe.__file__}")
    print(f"📜 Dir(mediapipe): {dir(mediapipe)}")

    try:
        from mediapipe.tasks.python import vision

        print("✅ MODERN TASKS API FOUND!")
    except ImportError as e:
        print(f"❌ TASKS API MISSING: {e}")

except ImportError as e:
    print(f"❌ CRITICAL: Could not import mediapipe at all. {e}")
