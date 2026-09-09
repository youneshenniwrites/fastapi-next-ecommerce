import io
import json
import os
import tarfile
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

import deploy_production
import production_ready
from production_ready import passed

SHA = "a" * 40


def run(id=1):
    return {
        "id": id,
        "head_sha": SHA,
        "head_branch": "main",
        "event": "push",
        "conclusion": "success",
    }


class ProductionGateTests(unittest.TestCase):
    def test_requires_exact_main_push(self):
        self.assertTrue(passed([run()], SHA))
        for key, value in [
            ("head_sha", "b" * 40),
            ("head_branch", "feature"),
            ("event", "pull_request"),
            ("conclusion", "failure"),
            ("conclusion", None),
        ]:
            candidate = run()
            candidate[key] = value
            self.assertFalse(passed([candidate], SHA))
        self.assertFalse(passed([], SHA))

    def test_new_failed_or_pending_run_invalidates_old_success(self):
        for conclusion in ["failure", None]:
            latest = run(id=2)
            latest["conclusion"] = conclusion
            self.assertFalse(passed([latest, run()], SHA))

    def evaluate(self, missing=None, deployed=False, current=SHA):
        def api(path):
            if path.endswith("commits/main"):
                return {"sha": current}
            if "/actions/workflows/" in path:
                return {"workflow_runs": [] if missing and missing in path else [run()]}
            if "/statuses?" in path:
                return [{"state": "success"}]
            return [{"id": 12}] if deployed else []

        with tempfile.NamedTemporaryFile(mode="r+") as output:
            with (
                patch.dict(
                    os.environ,
                    {
                        "GITHUB_REPOSITORY": "owner/repo",
                        "CANDIDATE_SHA": SHA,
                        "GITHUB_OUTPUT": output.name,
                    },
                ),
                patch.object(production_ready, "api", side_effect=api),
            ):
                production_ready.main()
            output.seek(0)
            return "ready=true" in output.read()

    def test_requires_every_workflow_and_current_main(self):
        self.assertTrue(self.evaluate())
        for name in production_ready.WORKFLOWS:
            self.assertFalse(self.evaluate(missing=name))
        self.assertFalse(self.evaluate(current="b" * 40))

    def test_skips_already_successful_release(self):
        self.assertFalse(self.evaluate(deployed=True))


class DeploymentFailureTests(unittest.TestCase):
    def test_api_smoke_failure_stops_before_frontend_deploy(self):
        archive = io.BytesIO()
        with tarfile.open(fileobj=archive, mode="w"):
            pass
        env = {
            "RELEASE_SHA": SHA,
            "VERCEL_ORG_ID": "team-test",
            "VERCEL_API_PROJECT_ID": "api-test",
            "VERCEL_FRONTEND_PROJECT_ID": "frontend-test",
            "VERCEL_TOKEN": "test-placeholder",
        }
        with (
            patch.dict(os.environ, env),
            patch.object(
                deploy_production.subprocess,
                "check_output",
                return_value=archive.getvalue(),
            ),
            patch.object(deploy_production.subprocess, "run") as deploy,
            patch.object(
                deploy_production, "read", side_effect=RuntimeError("API unavailable")
            ),
        ):
            with self.assertRaisesRegex(RuntimeError, "API unavailable"):
                deploy_production.main()
            self.assertEqual(deploy.call_count, 1)

    def test_cli_receives_matching_org_and_project_for_each_component(self):
        archive = io.BytesIO()
        with tarfile.open(fileobj=archive, mode="w"):
            pass
        selected = []

        def cli(args, check, env=None):
            env = os.environ if env is None else env
            # Vercel rejects an exported org without its paired project, even
            # when the archive includes a valid .vercel/project.json file.
            self.assertEqual(env["VERCEL_ORG_ID"], "team-test")
            project = env["VERCEL_PROJECT_ID"]
            root = Path(args[args.index("--cwd") + 1])
            self.assertEqual(
                json.loads((root / ".vercel/project.json").read_text())["projectId"],
                project,
            )
            selected.append(project)

        def read(url, **kwargs):
            if url.endswith("/api/v1/products/"):
                return b'[{"name":"Demo product"}]'
            return b"VINDOR Demo product"

        with tempfile.NamedTemporaryFile() as summary:
            env = {
                "RELEASE_SHA": SHA,
                "VERCEL_ORG_ID": "team-test",
                "VERCEL_API_PROJECT_ID": "api-test",
                "VERCEL_FRONTEND_PROJECT_ID": "frontend-test",
                "VERCEL_PROJECT_ID": "stale-inherited-project",
                "VERCEL_TOKEN": "test-placeholder",
                "GITHUB_STEP_SUMMARY": summary.name,
            }
            with (
                patch.dict(os.environ, env),
                patch.object(
                    deploy_production.subprocess,
                    "check_output",
                    return_value=archive.getvalue(),
                ),
                patch.object(deploy_production.subprocess, "run", side_effect=cli),
                patch.object(deploy_production, "read", side_effect=read),
                patch.object(
                    deploy_production.urllib.request,
                    "urlopen",
                    side_effect=urllib.error.HTTPError(
                        "https://example.com", 403, "Forbidden", {}, None
                    ),
                ),
            ):
                deploy_production.main()
        self.assertEqual(selected, ["api-test", "frontend-test"])

    def test_read_only_retry_is_bounded(self):
        failure = urllib.error.URLError("unavailable")
        with patch.object(
            deploy_production.urllib.request, "urlopen", side_effect=failure
        ) as request:
            with (
                patch.object(deploy_production.time, "sleep"),
                self.assertRaises(urllib.error.URLError),
            ):
                deploy_production.read("https://example.com", retry=True)
            self.assertEqual(request.call_count, 6)


if __name__ == "__main__":
    unittest.main()
