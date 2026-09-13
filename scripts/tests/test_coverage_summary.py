import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "coverage_summary", Path(__file__).parents[1] / "coverage_summary.py"
)
coverage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coverage)


class CoverageSummaryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.report = Path(self.directory.name) / "report"

    def test_backend_counts_and_failed_gate_are_not_conflated(self):
        self.report.write_text(
            '<coverage lines-covered="8" lines-valid="10" branches-covered="1" branches-valid="4"/>'
        )
        text, valid = coverage.render("backend", self.report, "failure")
        self.assertTrue(valid)
        self.assertIn("8 / 10 | 80.0%", text)
        self.assertIn("1 / 4 | 25.0%", text)
        self.assertIn("outcome:** failure", text)
        self.assertIn("85% combined", text)

    def test_frontend_aggregates_counts_not_percentages_and_states_scope(self):
        self.report.write_text(
            "SF:src/lib/catalog.ts\nLH:1\nLF:1\nBRH:0\nBRF:0\nend_of_record\nSF:src/lib/session.ts\nLH:1\nLF:9\nBRH:0\nBRF:0\nend_of_record\n"
        )
        text, valid = coverage.render(
            "frontend",
            self.report,
            "success",
            "https://github.com/owner/repo/actions/runs/1/artifacts/2",
            "a" * 40,
        )
        self.assertTrue(valid)
        self.assertIn("2 / 10 | 20.0%", text)
        self.assertIn("N/A", text)
        self.assertIn("NOT whole-frontend", text)
        self.assertIn("Download HTML and raw reports", text)

    def test_missing_malformed_negative_and_impossible_reports_are_unavailable(self):
        for content in [
            None,
            "not XML",
            "<coverage/>",
            '<coverage lines-covered="-1" lines-valid="3"/>',
            '<coverage lines-covered="4" lines-valid="3"/>',
        ]:
            with self.subTest(content=content):
                if content is not None:
                    self.report.write_text(content)
                text, valid = coverage.render("backend", self.report, "failure")
                self.assertFalse(valid)
                self.assertIn("Coverage unavailable", text)
                self.assertNotIn("| Lines |", text)

    def test_frontend_wrong_scope_and_missing_branch_totals_are_rejected(self):
        for content in [
            "SF:src/other.ts\nLH:1\nLF:1\nBRH:0\nBRF:0\nend_of_record",
            "SF:src/lib/catalog.ts\nLH:1\nLF:1\nend_of_record",
        ]:
            self.report.write_text(content)
            self.assertFalse(coverage.render("frontend", self.report, "success")[1])

    def test_oversized_reports_and_untrusted_summary_metadata_are_rejected(self):
        self.report.write_text("x" * (coverage.MAX_REPORT_BYTES + 1))
        self.assertFalse(coverage.render("backend", self.report, "failure")[1])
        with self.assertRaises(ValueError):
            coverage.render(
                "backend", self.report, "success", "https://example.com/report)"
            )
        with self.assertRaises(ValueError):
            coverage.render("backend", self.report, "success", revision="`injected`")
