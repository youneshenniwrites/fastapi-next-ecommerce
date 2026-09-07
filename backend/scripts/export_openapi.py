"""Export deterministic public API types without connecting to a database."""

import json
import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "openapi-export-only-not-a-runtime-secret"

from app.main import app  # noqa: E402

if __name__ == "__main__":
    target = Path(__file__).resolve().parents[2] / "frontend" / "openapi.json"
    target.write_text(json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n")
