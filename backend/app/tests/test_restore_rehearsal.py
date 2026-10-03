"""Safety failures must not redirect or strand disposable restore resources."""

import importlib.util
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location(
    "restore_rehearsal",
    Path(__file__).resolve().parents[2] / "scripts/restore_rehearsal.py",
)
rehearsal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rehearsal)


def test_worker_ignores_host_database_and_services(monkeypatch, tmp_path):
    for key in ["DATABASE_URL", "SENTRY_DSN", "STRIPE_API_KEY", "SECRET_KEY"]:
        monkeypatch.setenv(key, "host-private-value")
    captured = {}

    def command(args, **kwargs):
        captured.update(kwargs["env"])
        return SimpleNamespace(stdout=b"{}\n")

    monkeypatch.setattr(rehearsal, "command", command)
    rehearsal.worker("generated-loopback-url", "verify", tmp_path / "checkpoint")
    assert captured["DATABASE_URL"] == "generated-loopback-url"
    assert captured["SECRET_KEY"] != "host-private-value"
    assert captured["SENTRY_DSN"] == captured["STRIPE_API_KEY"] == ""
    assert captured["STRIPE_ENABLED"] == "false"


def test_cleanup_refuses_foreign_label_and_continues_after_timeout(monkeypatch):
    databases = rehearsal.Databases()
    databases.names = ["timed-out", "foreign", "owned"]
    removed = []
    deleted = set()

    def command(args, **kwargs):
        name = args[-1]
        if args[1] == "inspect":
            if name == "timed-out":
                raise subprocess.TimeoutExpired(args, 20)
            label = "someone-else" if name == "foreign" else databases.owner
            return SimpleNamespace(
                returncode=int(name in deleted),
                stdout=json.dumps(
                    [{"Config": {"Labels": {"vin258.owner": label}}}]
                ).encode(),
            )
        if args[1] == "rm":
            removed.append(name)
            deleted.add(name)
        return SimpleNamespace(returncode=0, stdout=b"")

    monkeypatch.setattr(rehearsal, "command", command)
    with pytest.raises(RuntimeError, match="cleanup failed"):
        databases.cleanup()
    assert removed == ["owned"]


def test_failure_retires_resources_without_printing_success(monkeypatch, capsys):
    cleaned = []
    monkeypatch.setattr(rehearsal.sys, "argv", ["restore_rehearsal.py"])
    monkeypatch.setattr(
        rehearsal,
        "command",
        lambda *args, **kwargs: SimpleNamespace(stdout=b"unix:///disposable.sock"),
    )
    monkeypatch.setattr(
        rehearsal.Databases,
        "create",
        lambda *args: (_ for _ in ()).throw(RuntimeError("injected source failure")),
    )
    monkeypatch.setattr(
        rehearsal.Databases, "cleanup", lambda self: cleaned.append(True)
    )
    with pytest.raises(RuntimeError, match="injected"):
        rehearsal.main()
    assert cleaned == [True]
    assert capsys.readouterr().out == ""
