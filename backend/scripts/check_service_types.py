"""Check the bounded service scope, then prove representative mistakes fail."""

import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

BACKEND = Path(__file__).resolve().parents[1]
PRELUDE = """from sqlalchemy.orm import Session
from app.models.order import Order
from app.providers.payment_types import PaymentProvider
from app.services.orders import place_order
from app.services.payments import finish, provider_call, start_payment

def check(db: Session, provider: PaymentProvider, order: Order) -> None:
"""
# Matching valid examples ensure import/configuration failures cannot masquerade
# as rejection proof. Each invalid line must produce its expected diagnostic.
CASES = [
    ('place_order(db, 1, 2, "key")', 'place_order(db, 1, "wrong", "key")', "arg-type"),
    ('finish(db, order, "paid")', 'finish(db, order, "pending")', "arg-type"),
    (
        'url: str | None = start_payment(db, 1, 2)["checkout_url"]',
        'url: str = start_payment(db, 1, 2)["checkout_url"]',
        "assignment",
    ),
    (
        "account: str = provider_call(provider.account_id)",
        "account: int = provider_call(provider.account_id)",
        "assignment",
    ),
]


def check_types(*paths: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "mypy",
            "--config-file",
            str(BACKEND / "pyproject.toml"),
            "--no-color-output",
            "--no-error-summary",
            *paths,
        ],
        cwd=BACKEND,
        capture_output=True,
        text=True,
    )


def main() -> None:
    scoped = check_types()
    print(scoped.stdout, end="")
    if scoped.returncode:
        raise SystemExit(scoped.stderr or "Scoped service type check failed")
    with TemporaryDirectory(prefix="vin261-types-") as temporary:
        # Distinct module names prevent incremental diagnostic replay from a
        # previous temporary path while retaining the expensive SDK import cache.
        suffix = Path(temporary).name.replace("-", "_")
        valid = Path(temporary) / f"valid_{suffix}.py"
        invalid = Path(temporary) / f"invalid_{suffix}.py"
        valid.write_text(PRELUDE + "".join(f"    {case[0]}\n" for case in CASES))
        invalid.write_text(PRELUDE + "".join(f"    {case[1]}\n" for case in CASES))
        accepted = check_types(str(valid))
        if accepted.returncode:
            raise SystemExit(accepted.stdout + accepted.stderr)
        rejected = check_types(str(invalid))
        diagnostics = [line for line in rejected.stdout.splitlines() if line.strip()]
        first_line = len(PRELUDE.splitlines()) + 1
        if (
            rejected.returncode != 1
            or rejected.stderr
            or len(diagnostics) != len(CASES)
            or any(
                not diagnostic.startswith(f"{invalid}:{first_line + index}: error:")
                or not diagnostic.endswith(f"[{case[2]}]")
                for index, (diagnostic, case) in enumerate(zip(diagnostics, CASES))
            )
        ):
            raise SystemExit(
                "Expected all four deliberate service type errors; got:\n"
                + rejected.stdout
                + rejected.stderr
            )
    print("Scoped service types pass; four representative mistakes rejected.")


if __name__ == "__main__":
    main()
