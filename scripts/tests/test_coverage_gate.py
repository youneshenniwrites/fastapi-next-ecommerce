import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
import coverage_gate as gate


def report(path, covered, total=200, branches=100, branch_total=200):
    records = "".join(
        f'<line number="{i + 1}" hits="{int(i < covered)}"/>' for i in range(total)
    )
    path.write_text(
        f'<coverage lines-covered="{covered}" lines-valid="{total}" branches-covered="{branches}" branches-valid="{branch_total}"><sources><source>app</source></sources><packages><package><classes><class filename="main.py"><lines>{records}</lines></class></classes></package></packages></coverage>'
    )


class CoverageGateTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.head = Path(folder.name) / "head.xml"
        self.base = Path(folder.name) / "base.xml"

    def test_exact_half_point_drop_passes_but_larger_drop_fails(self):
        report(self.base, 200)
        report(self.head, 199)
        self.assertTrue(gate.evaluate("backend", self.head, self.base, "")[1])
        report(self.head, 198)
        self.assertFalse(gate.evaluate("backend", self.head, self.base, "")[1])

    def test_branch_regression_and_zero_denominator_are_explicit(self):
        report(self.base, 200, branches=200)
        report(self.head, 200, branches=199)
        self.assertTrue(gate.evaluate("backend", self.head, self.base, "")[1])
        report(self.head, 200, branches=198)
        self.assertFalse(gate.evaluate("backend", self.head, self.base, "")[1])
        report(self.head, 200, branches=0, branch_total=0)
        text, passed = gate.evaluate("backend", self.head, self.base, "")
        self.assertTrue(passed)
        self.assertIn("Branches regression: **N/A", text)
        self.assertIn("Changed measured lines: **N/A", text)

    def test_changed_line_boundary_still_applies_without_baseline(self):
        diff = "diff --git a/backend/app/main.py b/backend/app/main.py\n+++ b/backend/app/main.py\n@@ -0,0 +1,10 @@\n"
        for covered, expected in [(9, True), (8, False)]:
            report(self.head, covered, total=10)
            text, passed = gate.evaluate("backend", self.head, self.base, diff)
            self.assertEqual(passed, expected)
            self.assertIn("baseline unavailable or incompatible", text)
            self.assertIn(f"{covered}/10 covered", text)

    def test_unmeasured_files_are_not_invented_as_covered_lines(self):
        report(self.head, 200)
        diff = "diff --git a/frontend/src/other.ts b/frontend/src/other.ts\n+++ b/frontend/src/other.ts\n@@ -0,0 +1 @@\n"
        text, passed = gate.evaluate("backend", self.head, self.base, diff)
        self.assertTrue(passed)
        self.assertIn("Changed measured lines: **N/A", text)


class CartCoverageGateTests(unittest.TestCase):
    """The frontend gate consumes the newly measured component, not just backend XML."""

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.head = Path(folder.name) / "head.lcov"
        self.base = Path(folder.name) / "base.lcov"
        self.component = "src/components/add-to-cart-button.tsx"
        self.diff = (
            f"diff --git a/frontend/{self.component} b/frontend/{self.component}\n"
            f"+++ b/frontend/{self.component}\n@@ -0,0 +1,10 @@\n"
        )

    def frontend_report(self, path, component_hits=10, omit_component=False):
        from coverage_summary import frontend_files

        records = []
        for name in frontend_files():
            if name == self.component and omit_component:
                continue
            hits = component_hits if name == self.component else 10
            lines = "\n".join(f"DA:{i + 1},{int(i < hits)}" for i in range(10))
            records.append(
                f"SF:{name}\n{lines}\nLH:{hits}\nLF:10\nBRH:2\nBRF:2\nend_of_record"
            )
        path.write_text("\n".join(records))

    def test_compatible_cart_report_and_changed_line_boundary(self):
        self.frontend_report(self.base)
        self.frontend_report(self.head)
        text, passed = gate.evaluate("frontend", self.head, self.base, self.diff)
        self.assertTrue(passed)
        self.assertIn("Lines regression: **PASS**", text)
        self.assertIn("10/10 covered", text)
        self.frontend_report(self.head, component_hits=8)
        text, passed = gate.evaluate("frontend", self.head, self.base, self.diff)
        self.assertFalse(passed)
        self.assertIn("Changed measured lines: **FAIL**; 8/10", text)

    def test_missing_and_old_scope_baseline_cannot_skip_changed_line_failure(self):
        self.frontend_report(self.head, component_hits=8)
        for old_scope in (False, True):
            if old_scope:
                self.frontend_report(self.base, omit_component=True)
            text, passed = gate.evaluate("frontend", self.head, self.base, self.diff)
            self.assertFalse(passed)
            self.assertIn("baseline unavailable or incompatible", text)
            self.assertIn("Changed measured lines: **FAIL**", text)

    def test_compatible_total_regression_fails_even_without_changed_sources(self):
        self.frontend_report(self.base)
        self.frontend_report(self.head, component_hits=0)
        text, passed = gate.evaluate("frontend", self.head, self.base, "")
        self.assertFalse(passed)
        self.assertIn("Lines regression: **FAIL**", text)
        self.assertIn("Changed measured lines: **N/A", text)


if __name__ == "__main__":
    unittest.main()
