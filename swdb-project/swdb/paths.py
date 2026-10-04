"""Where the database lives. The tool runs from its repo (or an editable install)."""

import os
from pathlib import Path

HOME = Path(os.environ.get("SWDB_HOME", Path(__file__).resolve().parent.parent))
SCHEMAS = HOME / "schemas"
VOCAB = HOME / "vocab"
RECORDS = HOME / "records"
