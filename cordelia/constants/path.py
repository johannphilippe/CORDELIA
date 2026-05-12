from pathlib import Path
from constants.var import cordelia_date

# Derive the project root from this file's location:
# cordelia/constants/path.py -> cordelia/constants/ -> cordelia/ -> project root
CORDELIA_ROOT = Path(__file__).resolve().parent.parent.parent
CORDELIA_PKG  = Path(__file__).resolve().parent.parent

# Legacy name kept for any importer still using cordelia_dir
cordelia_dir = CORDELIA_ROOT

cordelia_score = CORDELIA_ROOT / '_score' / f'cor{cordelia_date}'
