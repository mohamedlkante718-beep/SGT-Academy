import os
from pathlib import Path

MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT", "./media")).resolve()
PHOTOS_DIR = MEDIA_ROOT / "photos"
