"""Fail-closed regressions for the temporary development-only audit acceptance."""

import copy
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from scripts import frontend_audit as audit


class FrontendAuditTests(unittest.TestCase):
    def setUp(self):
        self.report = json.loads(
            (Path(__file__).parent / "fixtures/braces-audit.json").read_text()
        )
        self.policy = json.loads(
            (audit.ROOT / "frontend/audit-exception.json").read_text()
        )
        self.files = {
            name: (audit.ROOT / "frontend" / name).read_bytes()
            for name in self.policy["files"]
        }
        self.now = datetime(2026, 10, 3, 21, tzinfo=timezone.utc)

    def evaluate(self, report=None, status=1):
        return audit.evaluate(
            self.report if report is None else report,
            status,
            self.policy,
            self.files,
            self.now,
        )

    def clean(self):
        report = copy.deepcopy(self.report)
        report["vulnerabilities"] = {}
        report["metadata"]["vulnerabilities"] = {
            k: 0 for k in report["metadata"]["vulnerabilities"]
        }
        return report

    def test_actual_full_report_is_visibly_accepted_not_called_clean(self):
        self.assertIn("ACCEPTED RISK (not remediated)", self.evaluate())

    def test_clean_full_report_requires_no_exception_even_after_expiry(self):
        self.now = datetime(2026, 10, 11, tzinfo=timezone.utc)
        self.assertIn("no exception used", self.evaluate(self.clean(), 0))

    def test_expiry_boundary_fails(self):
        self.now = datetime(2026, 10, 10, 23, 59, tzinfo=timezone.utc)
        with self.assertRaisesRegex(ValueError, "expired"):
            self.evaluate()

    def test_both_dependency_files_are_pinned(self):
        for name in self.files:
            with self.subTest(name=name):
                original = self.files[name]
                self.files[name] += b"\n"
                with self.assertRaisesRegex(ValueError, "Dependencies changed"):
                    self.evaluate()
                self.files[name] = original

    def test_runtime_path_rejected_even_if_policy_hash_was_updated(self):
        lock = json.loads(self.files["package-lock.json"])
        lock["packages"]["node_modules/braces"]["dev"] = False
        self.files["package-lock.json"] = json.dumps(lock).encode()
        self.policy["files"]["package-lock.json"] = hashlib.sha256(
            self.files["package-lock.json"]
        ).hexdigest()
        with self.assertRaisesRegex(ValueError, "runtime dependency"):
            self.evaluate()

    def test_additional_advisory_in_same_package_rejected(self):
        self.report["vulnerabilities"]["braces"]["via"].append(
            {
                "name": "braces",
                "severity": "high",
                "url": "https://github.com/advisories/GHSA-other",
            }
        )
        with self.assertRaisesRegex(ValueError, "Unaccepted advisory"):
            self.evaluate()

    def test_advisory_added_to_transitive_package_rejected(self):
        self.report["vulnerabilities"]["shadcn"]["via"].append(
            copy.deepcopy(self.report["vulnerabilities"]["braces"]["via"][0])
        )
        with self.assertRaisesRegex(ValueError, "Unaccepted advisory"):
            self.evaluate()

    def test_new_dependency_path_rejected(self):
        self.report["vulnerabilities"]["braces"]["nodes"].append(
            "node_modules/other/node_modules/braces"
        )
        with self.assertRaisesRegex(ValueError, "paths"):
            self.evaluate()

    def test_changed_transitive_cause_rejected(self):
        self.report["vulnerabilities"]["shadcn"]["via"] = ["braces"]
        with self.assertRaisesRegex(ValueError, "causes"):
            self.evaluate()

    def test_separate_vulnerability_rejected(self):
        self.report["vulnerabilities"]["other"] = {"severity": "high"}
        self.report["metadata"]["vulnerabilities"]["high"] += 1
        self.report["metadata"]["vulnerabilities"]["total"] += 1
        with self.assertRaisesRegex(ValueError, "graph"):
            self.evaluate()

    def test_increased_severity_rejected(self):
        self.report["vulnerabilities"]["braces"]["severity"] = "critical"
        self.report["metadata"]["vulnerabilities"].update(high=6, critical=1)
        with self.assertRaisesRegex(ValueError, "severity"):
            self.evaluate()

    def test_network_error_and_malformed_reports_rejected(self):
        for report, status in [
            ({"error": {"code": "ENOAUDIT"}}, 1),
            ({}, 0),
            (self.clean(), 1),
            (self.report, 0),
            (self.report, 2),
        ]:
            with (
                self.subTest(status=status, report=report),
                self.assertRaises(ValueError),
            ):
                self.evaluate(report, status)

    def test_runtime_findings_cannot_use_exception(self):
        with (
            patch.object(audit, "run_audit", return_value=(self.report, 1)),
            patch.dict("os.environ", {}, clear=True),
        ):
            self.assertEqual(audit.main(), 1)

    def test_raw_failed_report_is_retained(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(audit.subprocess, "run") as run,
        ):
            run.return_value.stdout = json.dumps(self.report)
            run.return_value.returncode = 1
            report, status = audit.run_audit(Path(directory))
            self.assertEqual(status, 1)
            self.assertEqual(
                json.loads((Path(directory) / "audit.json").read_text()), report
            )

    def test_invalid_json_is_retained_and_main_fails(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(audit.subprocess, "run") as run,
        ):
            run.return_value.stdout = "not json"
            with self.assertRaises(ValueError):
                audit.run_audit(Path(directory))
            self.assertEqual((Path(directory) / "audit.json").read_text(), "not json")
        with (
            patch.object(audit, "run_audit", side_effect=ValueError("invalid json")),
            patch.dict("os.environ", {}, clear=True),
        ):
            self.assertEqual(audit.main(), 1)


if __name__ == "__main__":
    unittest.main()
