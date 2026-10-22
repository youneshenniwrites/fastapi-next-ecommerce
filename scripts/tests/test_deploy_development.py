"""Release attribution survives deployment from an archive without Git metadata."""

import io
import os
import sys
import tarfile
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from email.message import Message
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import deploy_development as deploy


def baseline_headers(**extra):
    headers = Message()
    headers["X-Content-Type-Options"] = "nosniff"
    headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    for name, value in extra.items():
        headers[name] = value
    return headers


class Response:
    def __init__(self, status, headers, payload):
        self.status = status
        self.headers = headers
        self._payload = payload
        self.closed = False

    def read(self, amount=-1):
        payload, self._payload = self._payload, b""
        return payload

    def close(self):
        self.closed = True


class DeploymentHeaderTests(unittest.TestCase):
    def test_expected_success_and_auth_error_require_real_response_headers(self):
        for status in (200, 401):
            for missing in (None, "X-Content-Type-Options", "Referrer-Policy"):
                with self.subTest(status=status, missing=missing):
                    headers = baseline_headers()
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

                        def open_error(request, timeout, response=response):
                            raise response

                        call = patch.object(
                            deploy, "open_smoke", side_effect=open_error
                        )
                    else:
                        response = Response(status, headers, b"ok")
                        call = patch.object(deploy, "open_smoke", return_value=response)
                    with call:
                        if missing:
                            with self.assertRaisesRegex(
                                RuntimeError, "Smoke check failed"
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
                    deploy,
                    "open_smoke",
                    side_effect=urllib.error.HTTPError(
                        "fixture", 403, "denied", {}, None
                    ),
                ) as opened,
            ):
                deploy.main()
            self.assertEqual(opened.call_count, 1)
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


class SmokeContractTests(unittest.TestCase):
    def setUp(self):
        self.sleep = patch.object(deploy.time, "sleep")
        self.paused = self.sleep.start()
        self.addCleanup(self.sleep.stop)

    def test_transient_header_and_status_recover_before_the_budget_ends(self):
        calls = {"count": 0}

        def open_smoke(request, timeout):
            calls["count"] += 1
            if calls["count"] == 1:
                return Response(503, baseline_headers(), b"fictional-secret")
            return Response(
                200,
                baseline_headers(**{"Content-Type": "application/json"}),
                b'{"status":"ok"}',
            )

        with patch.object(deploy, "open_smoke", side_effect=open_smoke):
            body = deploy.read(
                "https://fixture.test/health?token=fictional-secret",
                retry=True,
                content_type="application/json",
                json_status=True,
            )
        self.assertEqual(body, b'{"status":"ok"}')
        self.assertEqual(calls["count"], 2)
        self.paused.assert_called()

    def test_persistent_wrong_page_fails_without_leaking_the_body_or_query(self):
        def open_smoke(request, timeout):
            return Response(
                200,
                baseline_headers(**{"Content-Type": "text/html"}),
                b"<html>fictional-secret</html>",
            )

        with (
            patch.object(deploy, "open_smoke", side_effect=open_smoke) as opened,
            self.assertRaises(RuntimeError) as caught,
        ):
            deploy.read(
                "https://user:fictional-secret@fixture.test/health?token=fictional-secret",
                retry=True,
                content_type="application/json",
                contains=b"VINDOR",
            )
        self.assertEqual(opened.call_count, deploy.RETRY_ATTEMPTS)
        message = str(caught.exception)
        self.assertNotIn("fictional-secret", message)
        self.assertNotIn("token", message)
        self.assertIn("HTTP 200 https://fixture.test/health type=text/html", message)

    def test_deadline_during_body_read_is_absolute(self):
        clock = {"now": 0}

        def monotonic():
            return clock["now"]

        def open_smoke(request, timeout):
            response = Response(
                200, baseline_headers(**{"Content-Type": "text/plain"}), b""
            )

            def read(amount=-1):
                clock["now"] = deploy.RETRY_BUDGET_SECONDS + 5
                return b"fictional-secret"

            response.read = read
            return response

        with (
            patch.object(deploy.time, "monotonic", side_effect=monotonic),
            patch.object(deploy, "open_smoke", side_effect=open_smoke),
            self.assertRaises(RuntimeError) as caught,
        ):
            deploy.read(
                "https://fixture.test/page", retry=True, content_type="text/plain"
            )
        self.assertNotIn("fictional-secret", str(caught.exception))
        self.assertIn("type=text/plain", str(caught.exception))

    def test_body_limit_and_transport_failure_stay_inside_the_budget(self):
        calls = {"count": 0}

        def open_smoke(request, timeout):
            calls["count"] += 1
            if calls["count"] == 1:
                raise urllib.error.URLError("timed out")
            return Response(
                200,
                baseline_headers(**{"Content-Type": "text/plain"}),
                b"x" * (deploy.MAX_BODY_BYTES + 1),
            )

        with (
            patch.object(deploy, "open_smoke", side_effect=open_smoke),
            self.assertRaises(RuntimeError) as caught,
        ):
            deploy.read(
                "https://fixture.test/page", retry=True, content_type="text/plain"
            )
        self.assertGreaterEqual(calls["count"], 2)
        self.assertNotIn("timed out", str(caught.exception))

    def test_expected_401_is_accepted_once_and_mutations_are_not_replayed(self):
        calls = {"gets": 0}

        def open_smoke(request, timeout):
            calls["gets"] += 1
            raise urllib.error.HTTPError(
                request.full_url,
                401,
                "denied",
                baseline_headers(**{"Content-Type": "application/json"}),
                io.BytesIO(b'{"detail":"unauthorized"}'),
            )

        with patch.object(deploy, "open_smoke", side_effect=open_smoke):
            body = deploy.read(
                "https://fixture.test/api/v1/auth/me",
                expected=401,
                retry=True,
                content_type="application/json",
            )
        self.assertEqual(body, b'{"detail":"unauthorized"}')
        self.assertEqual(calls["gets"], 1)

        posts = []

        def post_once(request, timeout):
            posts.append(request.get_method())
            raise urllib.error.URLError("reset")

        with (
            patch.object(deploy, "open_smoke", side_effect=post_once),
            self.assertRaises(urllib.error.URLError),
        ):
            deploy.send_once(
                urllib.request.Request(
                    "https://fixture.test/api/session/logout",
                    data=b"{}",
                    method="POST",
                )
            )
        self.assertEqual(posts, ["POST"])

    def test_only_the_same_origin_docs_redirect_is_followed(self):
        seen = []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                seen.append((self.path, self.headers.get("x-vercel-protection-bypass")))
                if self.path == "/":
                    self.send_response(307)
                    self.send_header("Location", "/docs")
                    self._baseline()
                    self.end_headers()
                    return
                if self.path == "/docs":
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self._baseline()
                    self.end_headers()
                    self.wfile.write(b"<html>docs</html>")
                    return
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"unexpected")

            def _baseline(self):
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")

            def log_message(self, fmt, *args):
                return

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        port = server.server_address[1]
        with patch.dict(os.environ, {"VERCEL_PROTECTION_BYPASS": "fictional-bypass"}):
            body = deploy.read(
                f"http://127.0.0.1:{port}/",
                content_type="text/html",
                allow_docs_redirect=True,
            )
        self.assertEqual(body, b"<html>docs</html>")
        self.assertEqual([path for path, _header in seen], ["/", "/docs"])
        self.assertEqual({header for _path, header in seen}, {"fictional-bypass"})

        seen.clear()

        class Unsafe(Handler):
            def do_GET(self):
                seen.append(self.path)
                self.send_response(307)
                self.send_header(
                    "Location",
                    "http://127.0.0.1:9/private?token=fictional-secret",
                )
                self._baseline()
                self.end_headers()

        unsafe = HTTPServer(("127.0.0.1", 0), Unsafe)
        threading.Thread(target=unsafe.serve_forever, daemon=True).start()
        self.addCleanup(unsafe.server_close)
        self.addCleanup(unsafe.shutdown)
        with (
            patch.dict(os.environ, {"VERCEL_PROTECTION_BYPASS": "fictional-bypass"}),
            self.assertRaises(RuntimeError) as caught,
        ):
            deploy.read(
                f"http://127.0.0.1:{unsafe.server_address[1]}/",
                allow_docs_redirect=True,
            )
        self.assertEqual(seen, ["/"])
        message = str(caught.exception)
        self.assertNotIn("fictional-secret", message)
        self.assertNotIn("fictional-bypass", message)
        self.assertIn("HTTP 307", message)
