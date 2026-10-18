"""Load the same modules and imports used by the distributed skills."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for relative in ('block-asset-design/shared/scripts', 'block-asset-design/texture/scripts', 'block-asset-design/review/scripts', 'block-asset-design/mod-resource-extract/scripts'):
    sys.path.insert(0, str(ROOT / 'skills' / relative))
