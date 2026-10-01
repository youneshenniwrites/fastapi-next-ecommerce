"""Release attribution survives deployment from an archive without Git metadata."""

import io
import os
import sys
import tarfile
import tempfile
import unittest
import urllib.error
from email.message import Message
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import deploy_development as deploy


class DeploymentHeaderTests(unittest.TestCase):
    def test_expected_success_and_auth_error_require_real_response_headers(self):
        for status in (200, 401):
            for missing in (None, "X-Content-Type-Options", "Referrer-Policy"):
                with self.subTest(status=status, missing=missing):
                    headers = Message()
                    headers["X-Content-Type-Options"] = "nosniff"
                    headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
                    if missing:
                        del headers[missing]
                    if status == 401:
                        response = urllib.error.HTTPError(
                            "https://fixture.test/me",
                            401,
                            "denied",
                            headers,
                            io.BytesIO(b"unauthorized"),
                        )
                        call = patch.object(
                            deploy.urllib.request, "urlopen", side_effect=response
                        )
                    else:
                        response = MagicMock()
                        response.__enter__.return_value = response
                        response.status = status
                        response.headers = headers
                        response.read.return_value = b"ok"
                        call = patch.object(
                            deploy.urllib.request, "urlopen", return_value=response
                        )
                    with call:
                        if missing:
                            with self.assertRaisesRegex(
                                RuntimeError, "Header check failed"
                            ):
                                deploy.read("https://fixture.test/me", expected=status)
                        else:
                            self.assertEqual(
                                deploy.read("https://fixture.test/me", expected=status),
                                b"ok" if status == 200 else b"unauthorized",
                            )


class DeploymentReleaseTests(unittest.TestCase):
    def test_invalid_release_stops_before_any_command(self):
        for sha in ("main", "abc123", "-HEAD", "g" * 40, "a" * 40 + "\n"):
            with (
                self.subTest(sha=sha),
                patch.dict(os.environ, RELEASE_SHA=sha),
                patch.object(deploy.subprocess, "check_output") as archive,
            ):
                with self.assertRaises(ValueError):
                    deploy.main()
                archive.assert_not_called()

    def test_both_deployments_receive_same_build_and_runtime_release(self):
        archive = io.BytesIO()
        with tarfile.open(fileobj=archive, mode="w"):
            pass
        sha = "a" * 40
        with tempfile.TemporaryDirectory() as directory:
            env = {
                "RELEASE_SHA": sha,
                "VERCEL_API_PROJECT_ID": "api-fixture",
                "VERCEL_FRONTEND_PROJECT_ID": "web-fixture",
                "VERCEL_ORG_ID": "org-fixture",
                "VERCEL_TOKEN": "fictional-test-token",
                "GITHUB_STEP_SUMMARY": str(Path(directory) / "summary"),
            }

            def read(url, **kwargs):
                if url.endswith("/api/v1/products/"):
                    return b'[{"name":"Tea"}]'
                return b"VINDOR Tea"

            with (
                patch.dict(os.environ, env),
                patch.object(
                    deploy.subprocess, "check_output", return_value=archive.getvalue()
                ),
                patch.object(deploy.subprocess, "run") as run,
                patch.object(deploy, "read", side_effect=read),
                patch.object(
                    deploy.urllib.request,
                    "urlopen",
                    side_effect=urllib.error.HTTPError(
                        "fixture", 403, "denied", {}, None
                    ),
                ),
            ):
                deploy.main()
            self.assertEqual(run.call_count, 2)
            for call, project in zip(
                run.call_args_list, ("api-fixture", "web-fixture")
            ):
                command = call.args[0]
                self.assertEqual(
                    command[command.index("--env") + 1], f"SENTRY_RELEASE={sha}"
                )
                self.assertEqual(
                    command[command.index("--build-env") + 1], f"SENTRY_RELEASE={sha}"
                )
                self.assertEqual(call.kwargs["env"]["VERCEL_PROJECT_ID"], project)
