"""The ownership helper copies the linked issue sidebar and assigns the owner."""

import importlib.util
import io
import json
import subprocess
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / ".agents/skills/ecommerce-pr-ownership/scripts/set_metadata.py"
)
spec = importlib.util.spec_from_file_location("set_metadata", MODULE_PATH)
metadata = importlib.util.module_from_spec(spec)
spec.loader.exec_module(metadata)


def issue(
    number=287,
    milestone=5,
    title="Richer catalog and discovery",
    labels=("enhancement", "priority: high"),
):
    return {
        "number": number,
        "milestone": None
        if milestone is None
        else {"number": milestone, "title": title},
        "labels": [{"name": name} for name in labels],
        "assignees": [{"login": metadata.OWNER}],
    }


class LinkedIssue(unittest.TestCase):
    def test_title_key_wins_over_another_closing_reference(self):
        self.assertEqual(
            metadata.linked_issue_number(
                "[VIN-287] [docs] Record delivery",
                "Codex review is deferred by VIN-38.\nCloses #38\nCloses #287",
            ),
            287,
        )

    def test_closing_keyword_then_refs(self):
        self.assertEqual(metadata.linked_issue_number("", "Fixes #172"), 172)
        self.assertEqual(metadata.linked_issue_number(None, "refs #154"), 154)
        self.assertIsNone(metadata.linked_issue_number("maintenance", "see #12"))

    def test_sidebar_copies_milestone_and_priority_only(self):
        milestone, priority = metadata.issue_sidebar(issue())
        self.assertEqual(milestone["number"], 5)
        self.assertEqual(priority, ["priority: high"])
        self.assertEqual(metadata.issue_sidebar(None), (None, []))
        bare, labels = metadata.issue_sidebar(issue(milestone=None, labels=("bug",)))
        self.assertIsNone(bare)
        self.assertEqual(labels, [])


class ApplySidebar(unittest.TestCase):
    def test_dry_run_does_not_write(self):
        pull = {
            "title": "[VIN-287] [docs] Record delivery",
            "body": "Closes #287",
            "user": {"login": "owner"},
        }
        calls = []

        def fake_api(path, payload=None, method=None):
            calls.append((path, payload, method))
            if path.endswith("/pulls/311"):
                return pull
            if path.endswith("/issues/287"):
                return issue()
            raise AssertionError(path)

        with (
            patch.object(metadata, "api", fake_api),
            patch(
                "sys.argv",
                ["set_metadata.py", "311", "--labels", "documentation", "--dry-run"],
            ),
            redirect_stdout(io.StringIO()),
        ):
            metadata.main()
        self.assertEqual(
            [path for path, _, _ in calls],
            [
                "repos/youneshenniwrites/fastapi-next-ecommerce/pulls/311",
                "repos/youneshenniwrites/fastapi-next-ecommerce/issues/287",
            ],
        )

    def test_writes_assignee_priority_and_milestone(self):
        pull = {
            "title": "[VIN-287] [docs] Record delivery",
            "body": "Closes #287",
            "user": {"login": "owner"},
        }
        stored = issue(labels=("documentation",))
        calls = []

        def fake_api(path, payload=None, method=None):
            calls.append((path, payload, method))
            if path.endswith("/pulls/311"):
                return pull
            if path.endswith("/issues/287"):
                return issue()
            if path.endswith("/assignees"):
                stored["assignees"] = [{"login": payload["assignees"][0]}]
                return stored
            if path.endswith("/labels"):
                names = {label["name"] for label in stored["labels"]}
                names.update(payload["labels"])
                stored["labels"] = [{"name": name} for name in names]
                return stored
            if path.endswith("/issues/311") and method == "PATCH":
                stored["milestone"] = {"number": payload["milestone"], "title": "copied"}
                return stored
            if path.endswith("/issues/311"):
                return stored
            raise AssertionError(path)

        output = io.StringIO()
        with (
            patch.object(metadata, "api", fake_api),
            patch("sys.argv", ["set_metadata.py", "311", "--labels", "documentation"]),
            redirect_stdout(output),
        ):
            metadata.main()
        self.assertIn(
            (
                "repos/youneshenniwrites/fastapi-next-ecommerce/issues/311/assignees",
                {"assignees": [metadata.OWNER]},
                None,
            ),
            calls,
        )
        label_call = next(payload for path, payload, _ in calls if path.endswith("/labels"))
        self.assertEqual(label_call["labels"], ["documentation", "priority: high"])
        milestone_call = next(
            payload for path, payload, method in calls if method == "PATCH"
        )
        self.assertEqual(milestone_call, {"milestone": 5})
        reported = json.loads(output.getvalue())
        self.assertEqual(reported["milestone"]["number"], 5)
        self.assertIn("priority: high", reported["labels"])

    def test_assignee_route_falls_back_to_patch(self):
        calls = []

        def fake_api(path, payload=None, method=None):
            calls.append((path, payload, method))
            if path.endswith("/assignees"):
                raise subprocess.CalledProcessError(1, "gh")
            return {}

        with patch.object(metadata, "api", fake_api):
            metadata.assign_owner(311)
        self.assertIn(
            (
                "repos/youneshenniwrites/fastapi-next-ecommerce/issues/311",
                {"assignees": [metadata.OWNER]},
                "PATCH",
            ),
            calls,
        )

    def test_labels_and_milestone_proceed_when_assignment_is_forbidden(self):
        pull = {
            "title": "[VIN-287] [docs] Record delivery",
            "body": "",
            "user": {"login": "owner"},
        }
        calls = []
        readback = issue(labels=("documentation", "priority: high"))
        readback["assignees"] = []

        def fake_api(path, payload=None, method=None):
            calls.append((path, payload, method))
            if path.endswith("/pulls/311"):
                return pull
            if path.endswith("/issues/287"):
                return issue()
            if payload and "assignees" in payload:
                raise subprocess.CalledProcessError(1, "gh")
            if path.endswith("/issues/311") and method is None:
                return readback
            return {}

        with (
            patch.object(metadata, "api", fake_api),
            patch("sys.argv", ["set_metadata.py", "311", "--labels", "documentation"]),
            redirect_stdout(io.StringIO()),
            self.assertRaises(SystemExit) as raised,
        ):
            metadata.main()
        self.assertIn("ownership", str(raised.exception))
        self.assertTrue(any(path.endswith("/labels") for path, _, _ in calls))
        self.assertTrue(
            any(method == "PATCH" and payload == {"milestone": 5} for _, payload, method in calls)
        )

    def test_missing_milestone_is_a_failure(self):
        pull = {
            "title": "[VIN-287] [docs] Record delivery",
            "body": "",
            "user": {"login": "owner"},
        }

        def fake_api(path, payload=None, method=None):
            if path.endswith("/pulls/4"):
                return pull
            if path.endswith("/issues/287"):
                return issue()
            if path.endswith("/issues/4"):
                return issue(milestone=None, labels=("documentation", "priority: high"))
            return {}

        with (
            patch.object(metadata, "api", fake_api),
            patch("sys.argv", ["set_metadata.py", "4", "--labels", "documentation"]),
            self.assertRaises(SystemExit) as raised,
        ):
            metadata.main()
        self.assertIn("milestone", str(raised.exception))
