"""Run the real API against a newly migrated, disposable database for browser tests."""

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--payments", action="store_true", help="Use isolated sandbox fixture on port 18302"
)
args = parser.parse_args()
backend = Path(__file__).resolve().parents[2] / "backend"
with tempfile.TemporaryDirectory(prefix="forme-browser-") as directory:
    env = {
        **os.environ,
        "DATABASE_URL": f"sqlite:///{directory}/demo.db",
        "SENTRY_DSN": "",
        "SECRET_KEY": "browser-tests-only-not-a-production-secret",
        "PYTHONPATH": str(backend),
        "STRIPE_ENABLED": "true" if args.payments else "false",
        "STRIPE_API_KEY": "rk_test_browser_fixture" if args.payments else "",
        "STRIPE_WEBHOOK_SECRET": "whsec_browser_fixture_only" if args.payments else "",
        "STRIPE_CHECKOUT_ORIGIN": os.environ.get(
            "PAYMENT_TEST_STOREFRONT_ORIGIN", "http://127.0.0.1:3302"
        )
        if args.payments
        else "",
    }
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=backend,
        env=env,
        check=True,
    )
    subprocess.run(
        [sys.executable, "-m", "app.bootstrap", "seed-demo", "--confirm-demo"],
        cwd=backend,
        env=env,
        check=True,
    )
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "payment_api:app" if args.payments else "browser_api:app",
            "--app-dir",
            str(Path(__file__).resolve().parent),
            "--host",
            "127.0.0.1",
            "--port",
            "18302" if args.payments else "18300",
        ],
        cwd=backend,
        env=env,
    )
    try:
        raise SystemExit(process.wait())
    finally:
        process.terminate()
        process.wait()
