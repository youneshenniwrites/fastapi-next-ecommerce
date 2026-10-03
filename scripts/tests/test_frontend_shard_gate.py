"""Keep the protected browser check fail-closed when shards do not all succeed."""

import itertools
import os
import subprocess
import unittest
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/frontend.yml"


class BrowserShardGateTests(unittest.TestCase):
    def test_actual_gate_rejects_incomplete_or_failed_dependencies(self):
        workflow = WORKFLOW.read_text()
        gate = workflow.split("      - name: Require every browser shard to succeed\n")[
            1
        ]
        command = gate.split("        run: |\n", 1)[1].split("      - name:", 1)[0]
        states = ("success", "failure", "cancelled", "skipped", "")
        for changes, shards in itertools.product(states, repeat=2):
            with self.subTest(changes=changes, shards=shards):
                result = subprocess.run(
                    ["bash", "-e", "-c", command],
                    env={
                        **os.environ,
                        "CHANGES_RESULT": changes,
                        "SHARDS_RESULT": shards,
                    },
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(result.returncode == 0, changes == shards == "success")

    def test_gate_cannot_be_skipped_by_a_failed_dependency(self):
        workflow = WORKFLOW.read_text()
        gate = workflow.split("\n  browser:\n", 1)[1]
        self.assertIn("needs: [changes, browser_shards]", gate)
        self.assertIn(
            "if: always() && (needs.changes.result != 'success' || needs.changes.outputs.docs_only != 'true')",
            gate,
        )
        self.assertIn("name: Frontend · Production build and browser tests", gate)
        self.assertLess(
            gate.index("Require every browser shard"), gate.index("Publish validated")
        )


if __name__ == "__main__":
    unittest.main()
