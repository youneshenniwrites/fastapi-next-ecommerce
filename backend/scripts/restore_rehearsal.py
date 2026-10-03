"""Restore only freshly generated fictional databases; accept no database URLs."""

import hashlib
import json
import os
import secrets
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
RUNTIME_ENV = {key: os.environ[key] for key in ("PATH", "HOME") if key in os.environ}


def utc():
    return datetime.now(UTC).isoformat()


def command(args, *, env=None, input=None, timeout=120, check=True):
    result = subprocess.run(
        args,
        cwd=BACKEND,
        env=RUNTIME_ENV if env is None else env,
        input=input,
        capture_output=True,
        timeout=timeout,
    )
    if check and result.returncode:
        # Child output may contain credentials or database rows. Never publish it.
        raise RuntimeError(f"{args[0]} failed with exit {result.returncode}")
    return result


class Databases:
    def __init__(self):
        self.owner = secrets.token_hex(12)
        self.names = []
        self.password = secrets.token_hex(24)
        self.env = {**RUNTIME_ENV, "POSTGRES_PASSWORD": self.password}

    def create(self, role):
        name = f"vin258-{self.owner}-{role}"
        self.names.append(name)
        command(
            [
                "docker",
                "create",
                "--name",
                name,
                "--label",
                f"vin258.owner={self.owner}",
                "--tmpfs",
                "/var/lib/postgresql/data:rw,size=256m",
                "-p",
                "127.0.0.1::5432",
                "-e",
                "POSTGRES_PASSWORD",
                "-e",
                "POSTGRES_DB=rehearsal",
                "postgres:17",
            ],
            env=self.env,
        )
        command(["docker", "start", name])
        for _ in range(60):
            ready = command(
                [
                    "docker",
                    "exec",
                    name,
                    "pg_isready",
                    "-U",
                    "postgres",
                    "-d",
                    "rehearsal",
                ],
                check=False,
            )
            if ready.returncode == 0:
                break
            time.sleep(1)
        else:
            raise RuntimeError("Disposable PostgreSQL did not become ready")
        mapping = command(["docker", "port", name, "5432/tcp"]).stdout.decode().strip()
        if not mapping.startswith("127.0.0.1:") or not mapping[10:].isdigit():
            raise RuntimeError("Disposable database must bind only to loopback")
        return (
            name,
            f"postgresql+psycopg://postgres:{self.password}@{mapping}/rehearsal",
        )

    def cleanup(self):
        failures = []
        for name in self.names:
            try:
                found = command(["docker", "inspect", name], check=False, timeout=20)
                if found.returncode:
                    command(["docker", "info"], timeout=20)
                    continue
                label = json.loads(found.stdout)[0]["Config"]["Labels"].get(
                    "vin258.owner"
                )
                if label != self.owner:
                    failures.append(name)
                    continue
                removed = command(
                    ["docker", "rm", "-f", "-v", name], check=False, timeout=20
                )
                if (
                    removed.returncode
                    or command(
                        ["docker", "inspect", name], check=False, timeout=20
                    ).returncode
                    == 0
                ):
                    failures.append(name)
                else:
                    command(["docker", "info"], timeout=20)
            except (RuntimeError, subprocess.SubprocessError, OSError):
                failures.append(name)
        if failures:
            raise RuntimeError("Owned resource cleanup failed; do not claim completion")


def worker(url, mode, checkpoint):
    # Allow only the generated endpoint and basic runtime environment into the child.
    env = {
        "PATH": os.environ["PATH"],
        "PYTHONPATH": str(BACKEND),
        "DATABASE_URL": url,
        "SECRET_KEY": secrets.token_hex(32),
        "STRIPE_ENABLED": "false",
        "STRIPE_API_KEY": "",
        "STRIPE_WEBHOOK_SECRET": "",
        "SENTRY_DSN": "",
        "RATE_LIMIT_PROXY_SECRET": "",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
        "RATE_LIMIT_AUTH_REGISTER": "60",
        "RATE_LIMIT_AUTH_LOGIN": "60",
        "RATE_LIMIT_WRITE": "300",
        "RATE_LIMIT_DIAGNOSTICS_ENABLED": "false",
        "STRIPE_CHECKOUT_ORIGIN": "",
        "SENTRY_DIAGNOSTICS_ENABLED": "false",
        "SENTRY_ENVIRONMENT": "local",
        "SENTRY_RELEASE": "",
        "SENTRY_TRACES_SAMPLE_RATE": "0",
    }
    result = command(
        [sys.executable, "scripts/restore_fixture.py", mode, str(checkpoint)], env=env
    )
    return json.loads(result.stdout.decode().splitlines()[-1])


def restore(name, archive, *, check=True):
    return command(
        [
            "docker",
            "exec",
            "-i",
            name,
            "pg_restore",
            "-U",
            "postgres",
            "-d",
            "rehearsal",
            "--single-transaction",
            "--exit-on-error",
            "--no-owner",
            "--no-privileges",
        ],
        input=archive,
        check=check,
    )


def main():
    if len(sys.argv) != 1:
        raise RuntimeError("No URL, database, archive or target overrides are accepted")
    docker_host = (
        command(
            ["docker", "context", "inspect", "--format", "{{.Endpoints.docker.Host}}"]
        )
        .stdout.decode()
        .strip()
    )
    if not docker_host.startswith("unix://"):
        raise RuntimeError("This local rehearsal requires a Unix-socket Docker context")
    dbs = Databases()
    report = {
        "environment": "local disposable PostgreSQL",
        "started_utc": utc(),
        "revision": command(["git", "rev-parse", "HEAD"]).stdout.decode().strip(),
        "working_tree_dirty": bool(command(["git", "status", "--porcelain"]).stdout),
    }
    try:
        with tempfile.TemporaryDirectory(prefix="vin258-") as directory:
            checkpoint = Path(directory) / "checkpoint.json"
            source, source_url = dbs.create("source")
            target, target_url = dbs.create("target")
            report["source"] = source
            report["target"] = target
            report["postgres_version"] = (
                command(["docker", "exec", source, "postgres", "--version"])
                .stdout.decode()
                .strip()
            )
            report["fixture"] = worker(source_url, "seed", checkpoint)
            report["dump_started_utc"] = utc()
            archive = command(
                [
                    "docker",
                    "exec",
                    source,
                    "pg_dump",
                    "-U",
                    "postgres",
                    "-d",
                    "rehearsal",
                    "-Fc",
                ]
            ).stdout
            backup_completed = time.monotonic()
            report["backup_completed_utc"] = utc()
            report["archive_bytes"] = len(archive)
            report["archive_sha256"] = hashlib.sha256(archive).hexdigest()
            # A truncated archive must fail and leave the empty target unchanged.
            if restore(target, archive[:32], check=False).returncode == 0:
                raise RuntimeError("Truncated archive unexpectedly restored")
            worker(target_url, "empty", checkpoint)
            report["truncated_archive_rejected"] = True
            report["restore_started_utc"] = utc()
            report["backup_age_seconds"] = round(time.monotonic() - backup_completed, 3)
            began = time.monotonic()
            restore(target, archive)
            report["restore_seconds"] = round(time.monotonic() - began, 3)
            report["restore_completed_utc"] = utc()
            report["restored"] = worker(target_url, "verify", checkpoint)
            report["verified_utc"] = utc()
    finally:
        dbs.cleanup()
    report["cleanup"] = (
        "owned containers, in-memory data, archive and checkpoint retired"
    )
    report["finished_utc"] = utc()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, subprocess.SubprocessError, OSError) as error:
        print(
            f"Rehearsal failed ({type(error).__name__}); no acceptance claimed",
            file=sys.stderr,
        )
        sys.exit(1)
