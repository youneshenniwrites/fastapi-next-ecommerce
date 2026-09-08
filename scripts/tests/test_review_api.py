import unittest
from unittest.mock import patch

from scripts import codex_review_gate as gate


class EvidenceApi(unittest.TestCase):
    def connection(self, nodes, more=False, cursor=None):
        return {
            "data": {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {
                            "nodes": nodes,
                            "pageInfo": {"hasNextPage": more, "endCursor": cursor},
                        }
                    }
                }
            }
        }

    def test_rest_reads_last_page(self):
        with patch.object(gate, "api", side_effect=[[{}] * 100, [{"id": 101}]]) as api:
            self.assertEqual(len(gate.pages("example")), 101)
            self.assertIn("page=2", api.call_args.args[0])

    def test_later_rest_page_failure_is_not_partial_success(self):
        with (
            patch.object(gate, "api", side_effect=[[{}] * 100, RuntimeError("API")]),
            self.assertRaises(RuntimeError),
        ):
            gate.pages("example")

    def test_unresolved_thread_on_second_page(self):
        with patch.object(
            gate,
            "api",
            side_effect=[
                self.connection([{"isResolved": True}], True, "next"),
                self.connection([{"isResolved": False}]),
            ],
        ):
            self.assertTrue(gate.threads("owner/repo", 1))

    def test_graphql_errors_reject_partial_data(self):
        with (
            patch.object(
                gate, "api", return_value={"errors": [{"message": "unavailable"}]}
            ),
            self.assertRaises(RuntimeError),
        ):
            gate.threads("owner/repo", 1)

    def test_repeated_graphql_cursor_fails_closed(self):
        with (
            patch.object(gate, "api", return_value=self.connection([], True, "same")),
            self.assertRaises(RuntimeError),
        ):
            gate.threads("owner/repo", 1)

    def test_push_during_inspection_invalidates_result(self):
        old = {"head": {"sha": "a" * 40}, "draft": False, "state": "open"}
        new = dict(old, head={"sha": "b" * 40})
        with (
            patch.object(gate, "api", side_effect=[old, new]),
            patch.object(gate, "pages", return_value=[]),
            patch.object(gate, "threads", return_value=False),
            patch.object(gate, "review_history", return_value=[]),
            patch.object(gate, "evaluate", return_value=("success", "clean")),
        ):
            self.assertEqual(gate.inspect("owner/repo", 1)[1], "pending")

    def test_draft_transition_during_inspection_invalidates_result(self):
        old = {"head": {"sha": "a" * 40}, "draft": False, "state": "open"}
        new = dict(old, draft=True)
        with (
            patch.object(gate, "api", side_effect=[old, new]),
            patch.object(gate, "pages", return_value=[]),
            patch.object(gate, "threads", return_value=False),
            patch.object(gate, "review_history", return_value=[]),
            patch.object(gate, "evaluate", return_value=("success", "clean")),
        ):
            self.assertEqual(gate.inspect("owner/repo", 1)[1], "pending")
