import unittest

from scripts.docs_review_policy import eligible


class RoutineDocs(unittest.TestCase):
    def test_boundaries(self):
        pr = {
            "state": "open",
            "draft": False,
            "base": {"ref": "main"},
            "head": {"repo": {"full_name": "o/r"}},
            "changed_files": 1,
        }
        for path, expected in [
            ("README.md", True),
            ("docs/plans/roadmap.md", True),
            ("docs/delivery.md", False),
            ("AGENTS.md", False),
            (".agents/skills/a/SKILL.md", False),
            ("scripts/x.py", False),
        ]:
            self.assertEqual(eligible(pr, [{"filename": path}], "o/r"), expected)
        self.assertFalse(eligible(pr, [], "o/r"))
        self.assertFalse(
            eligible(
                pr, [{"filename": "README.md", "previous_filename": "AGENTS.md"}], "o/r"
            )
        )
        self.assertFalse(eligible(pr, [{"filename": "README.md"}], "other/repo"))
        self.assertFalse(
            eligible(dict(pr, draft=True), [{"filename": "README.md"}], "o/r")
        )


class RequestDeduplication(unittest.TestCase):
    def test_repeat_head_does_not_post(self):
        import sys
        from pathlib import Path
        from unittest.mock import patch

        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from scripts import request_docs_review as module

        pr = {"head": {"sha": "abc"}, "state": "open", "draft": False}
        with (
            patch.object(module, "inspect_routine", return_value=(True, pr)),
            patch.object(module, "api", return_value={"login": "owner"}) as api,
            patch.object(
                module,
                "pages",
                return_value=[
                    {
                        "user": {"login": "owner"},
                        "body": "<!-- docs-coderabbit-head:abc -->",
                    }
                ],
            ),
        ):
            module.request("o/r", 1)
            self.assertEqual(api.call_count, 1)

    def test_changed_head_does_not_post(self):
        from unittest.mock import patch

        from scripts import request_docs_review as module

        with (
            patch.object(
                module, "inspect_routine", return_value=(True, {"head": {"sha": "abc"}})
            ),
            patch.object(
                module,
                "api",
                side_effect=[{"login": "owner"}, {"head": {"sha": "def"}}],
            ) as api,
            patch.object(module, "pages", return_value=[]),
        ):
            module.request("o/r", 1)
            self.assertEqual(api.call_count, 2)


class CodexSkip(unittest.TestCase):
    def test_eligible_head_is_not_inspected_or_published(self):
        from unittest.mock import patch

        from scripts import codex_review_gate as gate

        pr = {"number": 7, "head": {"sha": "abc"}}
        with (
            patch.object(gate, "pages", return_value=[pr]),
            patch.object(gate, "inspect_routine", return_value=(True, pr)),
            patch.object(gate, "inspect") as inspect,
            patch.object(gate, "api") as api,
        ):
            gate.publish_reviews("o/r", "https://example.com", only_pr=7)
            inspect.assert_not_called()
            api.assert_not_called()


class CredentialBoundary(unittest.TestCase):
    def test_ineligible_request_never_uses_member_token(self):
        from unittest.mock import patch

        from scripts import request_docs_review as module

        with (
            patch.object(module, "inspect_routine", return_value=(False, {})),
            patch.object(module, "api") as api,
        ):
            module.request("o/r", 7)
            api.assert_not_called()

    def test_workflow_classifies_before_secret_step(self):
        from pathlib import Path

        workflow = (
            Path(__file__).resolve().parents[2] / ".github/workflows/docs-review.yml"
        ).read_text()
        classify, request = workflow.split("      - name: Request CodeRabbit")
        self.assertIn("GH_TOKEN: ${{ github.token }}", classify)
        self.assertNotIn("secrets.DEPENDABOT_REVIEW_TOKEN", classify)
        self.assertIn("if: steps.classify.outputs.eligible == 'true'", request)


class RetargetEvents(unittest.TestCase):
    def test_retarget_reclassifies_and_receives_event(self):
        from pathlib import Path

        pr = {
            "state": "open",
            "draft": False,
            "base": {"ref": "develop"},
            "head": {"repo": {"full_name": "o/r"}},
            "changed_files": 1,
        }
        files = [{"filename": "README.md"}]
        self.assertFalse(eligible(pr, files, "o/r"))
        pr["base"]["ref"] = "main"
        self.assertTrue(eligible(pr, files, "o/r"))
        workflow = (
            Path(__file__).resolve().parents[2] / ".github/workflows/docs-review.yml"
        ).read_text()
        events = workflow.split("types: [", 1)[1].split("]", 1)[0]
        self.assertIn("edited", [event.strip() for event in events.split(",")])
