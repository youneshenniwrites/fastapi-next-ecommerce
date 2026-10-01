"""Bounded development-only real-ingress probe; emits no bodies or identities."""

import argparse
import datetime
import http.client
import json
import re
import time
from pathlib import Path

HOST = "forme-ecommerce-development.vercel.app"
ORIGIN = f"https://{HOST}"
PATH = "/api/session/login"
BODY = json.dumps({"email": "test@example.test", "password": "Test1234!"})
PREFIX = "X-Vindor-Limiter-"


class Inconclusive(Exception):
    pass


def sample(connection, release):
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    connection.request(
        "POST",
        PATH,
        BODY,
        {
            "Origin": ORIGIN,
            "Content-Type": "application/json",
        },
    )
    response = connection.getresponse()
    # Bounded drain keeps the connection reusable; never store response content.
    if len(response.read(8193)) > 8192:
        raise Inconclusive("Response exceeds probe bound")
    instance = response.getheader(PREFIX + "Instance", "")
    sequence = response.getheader(PREFIX + "Sequence", "")
    if (
        response.status not in (401, 429)
        or not re.fullmatch(r"[0-9a-f]{32}", instance)
        or not re.fullmatch(r"[1-9][0-9]{0,15}", sequence)
        or int(sequence) > 2**53 - 1
        or response.getheader(PREFIX + "Context") != "verified"
        or response.getheader(PREFIX + "Release") != release
        or response.getheader(PREFIX + "Limit") != "60"
    ):
        raise Inconclusive("Missing verified, matching development evidence")
    retry = response.getheader("Retry-After", "")
    if response.status == 429 and (not retry.isdecimal() or not 1 <= int(retry) <= 60):
        raise Inconclusive("Missing bounded retry window")
    return {
        "started": started,
        "finished": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": response.status,
        "instance": instance,
        "sequence": int(sequence),
        "context": "verified",
        "release": release,
        "limit": 60,
        "retry_after": int(retry) if response.status == 429 else None,
    }


def capture(role, release):
    connection = http.client.HTTPSConnection(HOST, timeout=5)
    records = []
    try:
        if role == "observer":
            # Second network stays below the unchanged sixty-request budget.
            deadline = time.monotonic() + 130
            for index in range(24):
                if time.monotonic() >= deadline:
                    raise Inconclusive("Observer exceeded its time bound")
                row = sample(connection, release)
                if row["status"] != 401:
                    raise Inconclusive("Independent visitor was throttled")
                records.append(row)
                if index < 23:
                    time.sleep(5)
            return records
        deadline = time.monotonic() + 45
        for _ in range(61):
            if time.monotonic() >= deadline:
                raise Inconclusive("Throttle preparation exceeded its time bound")
            row = sample(connection, release)
            records.append(row)
            if row["status"] == 429:
                break
        else:
            raise Inconclusive("No throttle inside the request bound")
        first = records[-1]
        expires = time.monotonic() + first["retry_after"]
        for _ in range(8):
            if time.monotonic() + 3 >= expires:
                break
            time.sleep(3)
            row = sample(connection, release)
            if row["instance"] != first["instance"] or row["status"] != 429:
                raise Inconclusive("Throttle bracket changed instance or window")
            records.append(row)
        time.sleep(max(0, expires + 1 - time.monotonic()))
        row = sample(connection, release)
        if row["status"] != 401 or row["instance"] != first["instance"]:
            raise Inconclusive("Deliberate retry did not reach the original limiter")
        records.append(row)
        return records
    finally:
        connection.close()


def prove(first, second, release):
    """Use server ordering, never infer ordering from two machines' UTC clocks."""
    for rows in (first, second):
        if not isinstance(rows, list) or not rows or len(rows) > 70:
            raise Inconclusive("Invalid bounded sample set")
        for row in rows:
            if (
                row.get("release") != release
                or row.get("context") != "verified"
                or not re.fullmatch(r"[0-9a-f]{32}", str(row.get("instance", "")))
                or type(row.get("sequence")) is not int
                or not 1 <= row["sequence"] <= 2**53 - 1
                or type(row.get("limit")) is not int
                or row["limit"] != 60
            ):
                raise Inconclusive("Invalid sample evidence")
    rejected = [
        x
        for x in first
        if x.get("status") == 429
        and type(x.get("retry_after")) is int
        and 1 <= x["retry_after"] <= 60
    ]
    retry = first[-1]
    for a in rejected:
        for b in second:
            for c in rejected:
                if (
                    b.get("status") == 401
                    and a["instance"]
                    == b["instance"]
                    == c["instance"]
                    == retry["instance"]
                    and a["sequence"]
                    < b["sequence"]
                    < c["sequence"]
                    < retry["sequence"]
                    and retry.get("status") == 401
                    # A shared bucket allowing B needs >=60 subsequent decisions
                    # to throttle again. Exclude expiry/refill false positives.
                    and c["sequence"] - b["sequence"] < 60
                ):
                    return {
                        "result": "verified",
                        "release": release,
                        "bracket": [a, b, c],
                        "deliberate_retry": retry,
                    }
    raise Inconclusive("No same-instance ordered isolation bracket")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--role", choices=("throttle", "observer", "compare"), required=True
    )
    parser.add_argument("--release", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--first", type=Path)
    parser.add_argument("--second", type=Path)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.release):
        parser.error("release must be an exact commit SHA")
    try:
        if args.role == "compare":
            if not args.first or not args.second:
                parser.error("compare requires both sample files")
            result = prove(
                json.loads(args.first.read_text())["samples"],
                json.loads(args.second.read_text())["samples"],
                args.release,
            )
        else:
            result = {
                "result": "captured",
                "role": args.role,
                "release": args.release,
                "samples": capture(args.role, args.release),
            }
        args.output.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps({"result": result["result"], "release": args.release}))
        return 0
    except (
        Inconclusive,
        OSError,
        http.client.HTTPException,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
    ):
        # Third-party exception strings can contain URLs/headers: do not publish them.
        args.output.write_text(
            json.dumps({"result": "inconclusive", "release": args.release}) + "\n"
        )
        print("Verification inconclusive; no completion is claimed.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
