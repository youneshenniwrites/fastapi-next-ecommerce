import importlib.util
import unittest
from pathlib import Path
from unittest.mock import Mock

spec = importlib.util.spec_from_file_location(
    "limiter_probe", Path(__file__).parents[1] / "limiter_probe.py"
)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
RELEASE = "a" * 40


def row(status, sequence, instance="b" * 32):
    return {
        "status": status,
        "sequence": sequence,
        "instance": instance,
        "release": RELEASE,
        "context": "verified",
        "limit": 60,
        "retry_after": 12 if status == 429 else None,
    }


class IsolationProofTests(unittest.TestCase):
    def test_capture_uses_only_fixed_ingress_and_sanitizes_response(self):
        response = Mock(status=401)
        headers = {
            probe.PREFIX + "Instance": "b" * 32,
            probe.PREFIX + "Sequence": "1",
            probe.PREFIX + "Context": "verified",
            probe.PREFIX + "Release": RELEASE,
            probe.PREFIX + "Limit": "60",
            "Set-Cookie": "fictional-private-token",
        }
        response.getheader.side_effect = lambda key, default=None: headers.get(
            key, default
        )
        response.read.return_value = b"fictional-private-response"
        connection = Mock()
        connection.getresponse.return_value = response
        captured = probe.sample(connection, RELEASE)
        self.assertEqual(captured["status"], 401)
        self.assertNotIn("private", str(captured))
        args = connection.request.call_args.args
        self.assertEqual(args[:2], ("POST", "/api/session/login"))
        self.assertEqual(set(args[3]), {"Origin", "Content-Type"})
        for status in (302, 500):
            response.status = status
            with self.assertRaises(probe.Inconclusive):
                probe.sample(connection, RELEASE)
        response.status = 401
        headers[probe.PREFIX + "Release"] = "c" * 40
        with self.assertRaises(probe.Inconclusive):
            probe.sample(connection, RELEASE)

    def test_accepts_only_same_limiter_server_order(self):
        a = [row(429, 61), row(429, 63), row(401, 64)]
        b = [row(401, 62)]
        # Different machine clocks are immaterial: order comes from the limiter.
        a[0]["started"] = "2099-01-01"
        b[0]["started"] = "2000-01-01"
        self.assertEqual(probe.prove(a, b, RELEASE)["result"], "verified")

    def test_rejects_false_isolation_and_stale_evidence(self):
        cases = [
            [row(401, 62, "c" * 32)],
            [row(401, 60)],
            [row(401, 63)],
            [row(429, 62)],
            [{**row(401, 62), "context": "fallback"}],
            [{**row(401, 62), "release": "d" * 40}],
            [{**row(401, 62), "sequence": True}],
            [{**row(401, 62), "limit": 10}],
        ]
        for b in cases:
            with self.subTest(b=b), self.assertRaises(probe.Inconclusive):
                probe.prove([row(429, 61), row(429, 63), row(401, 64)], b, RELEASE)

    def test_requires_active_bracket_and_same_instance_retry(self):
        for a in [
            [row(429, 61), row(401, 63)],
            [row(429, 61), row(429, 63), row(401, 64, "c" * 32)],
            [row(429, 61), {**row(429, 63), "retry_after": 0}, row(401, 64)],
            [row(429, 61), row(429, 130), row(401, 131)],
        ]:
            with self.subTest(a=a), self.assertRaises(probe.Inconclusive):
                probe.prove(a, [row(401, 62)], RELEASE)


if __name__ == "__main__":
    unittest.main()
