"""
Create magic-pdf.json configuration file for MinerU

This script creates the required configuration file in the user's home directory.
"""
import json
import os
from pathlib import Path
import sys

def create_config():
    """Create magic-pdf.json configuration file"""

    # Get home directory
    home_dir = Path.home()
    config_path = home_dir / "magic-pdf.json"

    # Default model directory (MinerU default location)
    models_dir = home_dir / ".magic-pdf" / "models"

    # Configuration structure
    config = {
        "models-dir": str(models_dir).replace("\\", "/"),
        "device-mode": "cpu"  # Change to "cuda" if you have NVIDIA GPU
    }

    print("=" * 60)
    print("  MinerU Configuration Generator")
    print("=" * 60)
    print()

    # Check if config already exists
    if config_path.exists():
        print(f"⚠️  Configuration file already exists:")
        print(f"   {config_path}")
        print()
        response = input("Overwrite existing config? (y/N): ").strip().lower()
        if response != 'y':
            print()
            print("❌ Cancelled. Existing configuration preserved.")
            return False

    # Ask about device
    print()
    print("Select device mode:")
    print("  1. CPU (slower, works on all machines)")
    print("  2. CUDA (faster, requires NVIDIA GPU with CUDA)")
    print()
    device_choice = input("Enter choice (1/2) [default: 1]: ").strip()

    if device_choice == "2":
        config["device-mode"] = "cuda"
        print("   Selected: CUDA (GPU)")
    else:
        config["device-mode"] = "cpu"
        print("   Selected: CPU")

    # Ask about custom model directory
    print()
    print(f"Default model directory:")
    print(f"  {models_dir}")
    print()
    custom_dir = input("Use custom directory? (press Enter to use default): ").strip()

    if custom_dir:
        models_dir = Path(custom_dir)
        config["models-dir"] = str(models_dir).replace("\\", "/")
        print(f"   Using custom: {models_dir}")
    else:
        print(f"   Using default: {models_dir}")

    # Create config file
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print()
        print("=" * 60)
        print("✅ Configuration created successfully!")
        print("=" * 60)
        print()
        print(f"Location: {config_path}")
        print()
        print("Configuration:")
        print(json.dumps(config, indent=2))
        print()
        print("Next steps:")
        print("  1. Download models: mineru-models-download -m pipeline -s huggingface")
        print("  2. Or run: .\\backend\\setup_mineru.ps1")
        print()

        return True

    except Exception as e:
        print()
        print(f"❌ Error creating configuration: {e}")
        return False

if __name__ == "__main__":
    success = create_config()
    sys.exit(0 if success else 1)
