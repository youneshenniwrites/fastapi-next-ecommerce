"""Run complete npm audits with the owner's bounded VIN-269 tooling exception."""

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def findings(report, status):
    """Reject failed/malformed audits, including an empty report from a failed run."""
    if (
        status not in (0, 1)
        or report.get("error")
        or report.get("auditReportVersion") != 2
    ):
        raise ValueError("npm audit did not produce a valid version-2 report")
    entries = report.get("vulnerabilities")
    counts = report.get("metadata", {}).get("vulnerabilities", {})
    if not isinstance(entries, dict) or counts.get("total") != len(entries):
        raise ValueError("Missing or inconsistent npm vulnerability report")
    expected = {level: 0 for level in ("info", "low", "moderate", "high", "critical")}
    for entry in entries.values():
        expected[entry["severity"]] += 1
    if any(counts.get(level) != count for level, count in expected.items()):
        raise ValueError("Inconsistent npm severity counts")
    if status != (1 if entries else 0):
        raise ValueError("npm exit status does not match its findings")
    return entries


def evaluate(report, status, policy, files, now):
    """Accept only the exact reviewed development graph until its expiry."""
    entries = findings(report, status)
    if not entries:
        return "Full dependency audit clean; no exception used."
    expires = datetime.fromisoformat(policy["expiresAt"])
    if expires.tzinfo is None or now >= expires:
        raise ValueError("VIN-269 audit exception expired")
    if set(policy["files"]) != {"package.json", "package-lock.json"}:
        raise ValueError("Both dependency files must be pinned")
    for name, expected in policy["files"].items():
        if hashlib.sha256(files[name]).hexdigest() != expected:
            raise ValueError(
                "Dependencies changed; re-assess VIN-269 before using exception"
            )
    locked = json.loads(files["package-lock.json"])["packages"]
    if set(entries) != set(policy["packages"]):
        raise ValueError("Findings differ from the reviewed dependency graph")
    for name, entry in entries.items():
        allowed = policy["packages"][name]
        if entry["name"] != name or entry["severity"] != "high":
            raise ValueError("Unreviewed package or severity")
        if sorted(entry["nodes"]) != sorted(allowed["nodes"]) or not entry["nodes"]:
            raise ValueError("Unreviewed dependency paths")
        for path in entry["nodes"]:
            if locked.get(path, {}).get("dev") is not True:
                raise ValueError("Exception must never cover a runtime dependency")
        causes = []
        for cause in entry["via"]:
            if isinstance(cause, str):
                if cause not in entries:
                    raise ValueError("Missing transitive advisory evidence")
                causes.append(cause)
            else:
                if (
                    name != "braces"
                    or cause.get("name") != "braces"
                    or cause.get("severity") != "high"
                    or cause.get("url") != policy["advisory"]
                ):
                    raise ValueError("Unaccepted advisory")
                causes.append(cause["url"])
        if sorted(causes) != sorted(allowed["via"]):
            raise ValueError("Advisory causes differ from the reviewed graph")
    return (
        f"ACCEPTED RISK (not remediated): {policy['advisory']} in development tooling. "
        f"Expires {policy['expiresAt']}. Tracking: {policy['issue']}. "
        "Complete findings remain in audit.json; runtime audit is clean."
    )


def run_audit(frontend, runtime=False):
    """Retain raw reports even when audit fails; never turn network errors green."""
    command = ["npm", "audit", "--json"]
    if runtime:
        command.append("--omit=dev")
    result = subprocess.run(
        command, cwd=frontend, capture_output=True, text=True, timeout=120, check=False
    )
    (frontend / ("audit-runtime.json" if runtime else "audit.json")).write_text(
        result.stdout
    )
    return json.loads(result.stdout), result.returncode


def main():
    frontend = ROOT / "frontend"
    try:
        report, status = run_audit(frontend)
        runtime, runtime_status = run_audit(frontend, runtime=True)
        if findings(runtime, runtime_status):
            raise ValueError("Runtime vulnerabilities are never excepted")
        policy = json.loads((frontend / "audit-exception.json").read_text())
        files = {
            name: (frontend / name).read_bytes()
            for name in ("package.json", "package-lock.json")
        }
        message = evaluate(report, status, policy, files, datetime.now(timezone.utc))
    except (
        ValueError,
        KeyError,
        TypeError,
        OSError,
        subprocess.SubprocessError,
    ) as error:
        message = f"Frontend audit BLOCKED: {error}"
        code = 1
    else:
        code = 0
    print(message)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as summary:
            summary.write("\n### Frontend dependency audit\n\n" + message + "\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
