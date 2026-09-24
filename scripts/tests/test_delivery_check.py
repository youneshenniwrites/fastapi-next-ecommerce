"""Completion checks must not silently accept missing or pending evidence."""

import copy
import unittest

from scripts.delivery_check import CLOSEOUT, validate


class DeliveryCheckTests(unittest.TestCase):
    def setUp(self):
        self.record = {
            "issue": "VIN-200",
            "revision": "abc123",
            "finish_line": "Open PR",
            "checkpoints": [
                {
                    "outcome": "Check handoff",
                    "verification": "unit tests",
                    "status": "done",
                    "evidence": "test output",
                }
            ],
            "closeout": {
                key: {"status": "not-applicable", "reason": "PR-only scope"}
                for key in CLOSEOUT
            },
        }
        self.record["closeout"]["tracking"] = {
            "status": "done",
            "evidence": "issue URL",
        }

    def test_complete_scoped_handoff(self):
        self.assertEqual(validate(self.record), [])

    def test_each_closeout_is_required(self):
        for key in CLOSEOUT:
            record = copy.deepcopy(self.record)
            del record["closeout"][key]
            self.assertTrue(validate(record), key)

    def test_pending_checkpoint_or_closeout_is_not_complete(self):
        self.record["checkpoints"][0]["status"] = "pending"
        self.assertTrue(validate(self.record))
        self.record["checkpoints"][0]["status"] = "done"
        self.record["closeout"]["review"] = {"status": "pending"}
        self.assertTrue(validate(self.record))

    def test_evidence_and_scope_reasons_cannot_be_empty(self):
        self.record["checkpoints"][0]["evidence"] = " "
        self.record["closeout"]["merge"]["reason"] = ""
        self.record["closeout"]["tracking"]["evidence"] = []
        self.assertEqual(len(validate(self.record)), 3)

    def test_malformed_records_fail(self):
        for record in (None, [], {}, {"checkpoints": [False], "closeout": []}):
            self.assertTrue(validate(record))


if __name__ == "__main__":
    unittest.main()
