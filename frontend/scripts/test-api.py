"""Run the real API against a newly migrated, disposable database for browser tests."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

backend = Path(__file__).resolve().parents[2] / "backend"
with tempfile.TemporaryDirectory(prefix="forme-browser-") as directory:
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{directory}/demo.db", "SECRET_KEY": "browser-tests-only-not-a-production-secret", "PYTHONPATH": str(backend)}
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=backend, env=env, check=True)
    subprocess.run([sys.executable, "-m", "app.bootstrap", "seed-demo", "--confirm-demo"], cwd=backend, env=env, check=True)
    process = subprocess.Popen([sys.executable, "-m", "uvicorn", "browser_api:app", "--app-dir", str(Path(__file__).resolve().parent), "--host", "127.0.0.1", "--port", "18300"], cwd=backend, env=env)
    try:
        process.wait()
    finally:
        process.terminate()
        process.wait()
