"""Coverage comparison behavior across regressions and absent evidence."""

import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from coverage_compare import changed_lines, compare, executable_lines

HEAD = "a" * 40
BASE = "b" * 40


def xml(hits="1", filename="example.py"):
    return f'''<coverage lines-covered="{hits}" lines-valid="1" branches-covered="0" branches-valid="0"><sources><source>app</source></sources><packages><package><classes><class filename="{filename}"><lines><line number="3" hits="{hits}"/></lines></class></classes></package></packages></coverage>'''


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.head = Path(self.directory.name) / "head.xml"
        self.base = Path(self.directory.name) / "base.xml"
        self.head.write_text(xml("0"))
        self.base.write_text(xml())
        self.diff = "+++ b/backend/app/example.py\n@@ -3 +3 @@\n-old\n+new\n"

    def result(self):
        return compare("backend", self.head, self.base, self.diff, HEAD, BASE)

    def test_reports_regression_and_changed_uncovered_line(self):
        result = self.result()
        self.assertIn("-100.00 pp", result)
        self.assertIn("0/1 (0.0%)", result)
        self.assertIn(HEAD, result)
        self.assertIn(BASE, result)

    def test_missing_or_incompatible_base_does_not_claim_no_regression(self):
        self.base.unlink()
        self.assertIn("Baseline unavailable or incompatible", self.result())
        self.base.write_text(xml(filename="other.py"))
        self.assertIn("Baseline unavailable or incompatible", self.result())

    def test_unmeasured_file_is_not_credited_and_deleted_lines_not_counted(self):
        self.diff += "diff --git a/frontend/src/untested.ts b/frontend/src/untested.ts\n+++ b/frontend/src/untested.ts\n@@ -0,0 +1,2 @@\n+x\n+y\n"
        self.assertIn("outside the measured scope: **2**", self.result())
        self.diff = "+++ b/backend/app/example.py\n@@ -3 +2,0 @@\n-old\n"
        self.assertIn("N/A (none measured)", self.result())

    def test_bad_head_evidence_fails_instead_of_inventing_zero(self):
        self.head.write_text("<broken>")
        with self.assertRaises(ET.ParseError):
            self.result()

    def test_paths_cannot_escape_report_scope(self):
        self.head.write_text(xml(filename="../secret.py"))
        with self.assertRaises(ValueError):
            executable_lines("backend", self.head)
        with self.assertRaises(ValueError):
            changed_lines("+++ b/../../secret\n@@ -0,0 +1 @@\n+x")

    def test_added_header_shaped_text_cannot_redirect_later_hunks(self):
        diff = """diff --git a/text.ts b/text.ts
--- a/text.ts
+++ b/text.ts
@@ -0,0 +1,3 @@
+const example = `
+++ b/not-this-file.ts
+`;
@@ -5 +8 @@
-old
+new
"""
        self.assertEqual(changed_lines(diff), {"text.ts": {1, 2, 3, 8}})

    def test_changed_backend_source_root_is_not_mapped_to_app(self):
        self.head.write_text(
            xml().replace("<source>app</source>", "<source>other</source>")
        )
        with self.assertRaises(ValueError):
            executable_lines("backend", self.head)

    def test_frontend_lcov_and_inconsistent_totals(self):
        self.head.write_text(
            "\n".join(
                f"SF:src/lib/{name}.ts\nDA:3,1\nLH:1\nLF:1\nBRH:0\nBRF:0\nend_of_record"
                for name in ("catalog", "session")
            )
        )
        self.assertEqual(
            executable_lines("frontend", self.head)["frontend/src/lib/catalog.ts"],
            {3: True},
        )
        self.head.write_text(self.head.read_text().replace("LH:1", "LH:0"))
        with self.assertRaises(ValueError):
            executable_lines("frontend", self.head)

    def test_malformed_line_cannot_disappear_from_zero_totals(self):
        self.head.write_text(
            "\n".join(
                f"SF:src/lib/{name}.ts\nDA:-1,0\nLH:0\nLF:0\nBRH:0\nBRF:0\nend_of_record"
                for name in ("catalog", "session")
            )
        )
        with self.assertRaises(ValueError):
            executable_lines("frontend", self.head)

    def test_zero_context_hunks_and_non_executable_additions(self):
        self.assertEqual(changed_lines("+++ b/a.py\n@@ -1 +1,2 @@\n"), {"a.py": {1, 2}})
        self.diff = "+++ b/backend/app/example.py\n@@ -0,0 +1 @@\n+# comment"
        self.assertIn("N/A (none measured)", self.result())


if __name__ == "__main__":
    unittest.main()
