"""Load the same modules and imports used by the distributed skills."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for relative in ('machine-design/shared/scripts', 'machine-texture/scripts', 'machine-review/scripts', 'mod-resource-extract/scripts'):
    sys.path.insert(0, str(ROOT / 'skills' / relative))
