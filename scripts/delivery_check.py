"""Check handoff completeness, not the truth of evidence or merge eligibility."""

import argparse
import json
from pathlib import Path

CLOSEOUT = ("review", "merge", "deployment", "tracking")


def text(value):
    return isinstance(value, str) and bool(value.strip())


def validate(record):
    """Return missing/invalid evidence fields in an issue-handoff snapshot."""
    errors = []
    if not isinstance(record, dict):
        return ["handoff must be an object"]
    for key in ("issue", "revision", "finish_line"):
        if not text(record.get(key)):
            errors.append(f"{key}: nonempty text required")
    checkpoints = record.get("checkpoints")
    if not isinstance(checkpoints, list) or not checkpoints:
        errors.append("checkpoints: nonempty list required")
        checkpoints = []
    for index, checkpoint in enumerate(checkpoints, 1):
        prefix = f"checkpoint {index}"
        if not isinstance(checkpoint, dict):
            errors.append(f"{prefix}: object required")
            continue
        for key in ("outcome", "verification", "evidence"):
            if not text(checkpoint.get(key)):
                errors.append(f"{prefix}: {key} required")
        if checkpoint.get("status") != "done":
            errors.append(f"{prefix}: not done")
    closeout = record.get("closeout")
    if not isinstance(closeout, dict):
        closeout = {}
    for key in CLOSEOUT:
        item = closeout.get(key)
        if not isinstance(item, dict):
            errors.append(f"{key}: disposition required")
            continue
        status = item.get("status")
        if status == "done":
            if not text(item.get("evidence")):
                errors.append(f"{key}: evidence required")
        elif status == "not-applicable":
            if not text(item.get("reason")):
                errors.append(f"{key}: scope reason required")
        else:
            errors.append(f"{key}: unfinished or invalid status")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("handoff", type=Path)
    args = parser.parse_args()
    try:
        record = json.loads(args.handoff.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"Cannot read handoff: {exc}")
        return 2
    errors = validate(record)
    if errors:
        print("Completion evidence incomplete:\n- " + "\n- ".join(errors))
        return 1
    print(
        "Handoff fields complete. Independently verify evidence and scope; "
        "this is not merge approval."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
