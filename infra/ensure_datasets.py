#!/usr/bin/env python3
"""
Ensure default datasets (Andromeda, Earth, Sun, Hockey) are present.

- Checks for downloaded originals in infra/downloads/
- Checks for DZI tiles in infra/tiles/{dataset}/
- Generates missing pieces by invoking existing processors

Usage:
    python infra/ensure_datasets.py
"""
import sys
from pathlib import Path
import subprocess

REPO_ROOT = Path(__file__).parent.parent
INFRA_DIR = REPO_ROOT / "infra"
DOWNLOADS = INFRA_DIR / "downloads"
TILES = INFRA_DIR / "tiles"

ANDROMEDA_JPG = DOWNLOADS / "andromeda_hubble_2025.jpg"
ANDROMEDA_DZI = TILES / "andromeda" / "info.dzi"
EARTH_JPG = DOWNLOADS / "earth_suomi_original.jpg"
EARTH_DZI = TILES / "earth" / "info.dzi"
SUN_JPG = DOWNLOADS / "sun_sdo_original.jpg"
SUN_DZI = TILES / "sun" / "info.dzi"
HOCKEY_JPG = DOWNLOADS / "hockey_original.jpg"
HOCKEY_DZI = TILES / "hockey" / "info.dzi"


def ensure_andromeda() -> None:
    need_download = not ANDROMEDA_JPG.exists()
    need_tiles = not ANDROMEDA_DZI.exists()
    if need_download or need_tiles:
        print("Ensuring Andromeda dataset (this may take time)...")
        subprocess.run([sys.executable, str(INFRA_DIR / "process_real_image.py")], check=True)
    else:
        print("✓ Andromeda present")


def ensure_earth() -> None:
    need_download = not EARTH_JPG.exists()
    need_tiles = not EARTH_DZI.exists()
    if need_download or need_tiles:
        print("Ensuring Earth dataset (this may take time)...")
        subprocess.run([sys.executable, str(INFRA_DIR / "process_earth_image.py")], check=True)
    else:
        print("✓ Earth present")


def ensure_sun() -> None:
    need_download = not SUN_JPG.exists()
    need_tiles = not SUN_DZI.exists()
    if need_download or need_tiles:
        print("Ensuring Sun dataset (this may take time)...")
        subprocess.run([sys.executable, str(INFRA_DIR / "process_sun_image.py")], check=True)
    else:
        print("✓ Sun present")



def main() -> None:
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    TILES.mkdir(parents=True, exist_ok=True)

    ensure_andromeda()
    ensure_earth()
    ensure_sun()
    print("✓ Default datasets ensured")


if __name__ == "__main__":
    main()
