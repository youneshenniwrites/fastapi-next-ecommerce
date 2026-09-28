"""Security boundary and race regression tests for the trusted uv exporter."""

import base64
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import dependabot_export as export

MANIFEST = '[project]\nname="backend"\nversion="1"\ndependencies=["fastapi>=1"]\n'
LOCK = 'version=1\n[[package]]\nname="backend"\nversion="1"\nsource={virtual="."}\n[[package]]\nname="fastapi"\nversion="1"\nsource={registry="https://pypi.org/simple"}\n'


class ExportTests(unittest.TestCase):
    def test_registry_dependency_update_allowed(self):
        export.validate_inputs(
            MANIFEST, MANIFEST.replace("fastapi>=1", "fastapi>=2"), LOCK
        )

    def test_rejects_configuration_sources_and_code(self):
        bad = [
            MANIFEST + '\n[tool.uv]\nindex-url="https://evil.test"\n',
            MANIFEST + '\n[build-system]\nrequires=["evil"]\n',
            MANIFEST.replace('version="1"', 'version="2"'),
            MANIFEST.replace("fastapi>=1", "fastapi @ https://evil.test/x.whl"),
            MANIFEST + '\n[dependency-groups]\ndev=[{include-group="other"}]\n',
        ]
        for manifest in bad:
            with (
                self.subTest(manifest=manifest),
                self.assertRaises(export.ExportNotSafe),
            ):
                export.validate_inputs(MANIFEST, manifest, LOCK)
        for source in [
            '{path="../evil"}',
            '{git="https://evil.test"}',
            '{registry="https://evil.test"}',
        ]:
            with self.subTest(source=source), self.assertRaises(export.ExportNotSafe):
                export.validate_inputs(
                    MANIFEST,
                    MANIFEST,
                    LOCK.replace('{registry="https://pypi.org/simple"}', source),
                )

    def test_rejects_artifact_credentials(self):
        with self.assertRaises(export.ExportNotSafe):
            export.validate_inputs(
                MANIFEST,
                MANIFEST,
                LOCK
                + 'sdist={url="https://secret@files.pythonhosted.org/file.tar.gz"}\n',
            )

    def test_child_receives_only_data_and_no_secrets(self):
        calls = []

        def run(command, **kwargs):
            calls.append(command)
            self.assertNotIn("GH_TOKEN", kwargs["env"])
            self.assertNotIn("DEPENDABOT_REVIEW_TOKEN", kwargs["env"])
            self.assertNotIn("UV_INDEX_URL", kwargs["env"])
            self.assertEqual(
                {p.name for p in Path(kwargs["cwd"]).iterdir()},
                {"pyproject.toml", "uv.lock"},
            )
            if "--version" in command:
                return subprocess.CompletedProcess(command, 0, "uv 0.8.22\n")
            self.assertIn("--offline", command)
            self.assertIn("--locked", command)
            self.assertIn("--no-config", command)
            return subprocess.CompletedProcess(command, 0, "fastapi==1\n")

        with (
            patch.dict(
                "os.environ",
                {
                    "GH_TOKEN": "secret",
                    "DEPENDABOT_REVIEW_TOKEN": "member",
                    "UV_INDEX_URL": "evil",
                },
            ),
            patch.object(export.shutil, "which", return_value="/usr/bin/uv"),
            patch.object(export.subprocess, "run", side_effect=run),
        ):
            self.assertIn(
                "fastapi==1", export.generate_export(MANIFEST, MANIFEST, LOCK)
            )
        self.assertEqual(len(calls), 2)

    def test_unpinned_uv_cannot_export(self):
        with (
            patch.object(export.shutil, "which", return_value="/usr/bin/uv"),
            patch.object(
                export.subprocess,
                "run",
                return_value=subprocess.CompletedProcess([], 0, "uv 0.9.0\n"),
            ) as run,
        ):
            with self.assertRaises(export.ExportNotSafe):
                export.generate_export(MANIFEST, MANIFEST, LOCK)
            self.assertEqual(run.call_count, 1)

    def fixture(self, stale=False, symlink=False):
        pr = {
            "state": "open",
            "draft": False,
            "user": {"login": "dependabot[bot]"},
            "base": {"ref": "main", "sha": "base"},
            "head": {
                "sha": "head",
                "ref": "dependabot/uv/update",
                "repo": {"full_name": "o/r"},
            },
            "changed_files": 1,
        }
        blobs = {"manifest": MANIFEST, "lock": LOCK, "export": "fastapi==0\n"}
        reads = []
        writes = []

        def api(path):
            reads.append(path)
            if path.endswith("/pulls/1"):
                if stale and reads.count(path) > 1:
                    return dict(pr, head=dict(pr["head"], sha="new-head"))
                return pr
            if "/files?" in path:
                return [{"filename": "backend/uv.lock", "status": "modified"}]
            if "/git/trees/" in path:
                return {
                    "tree": [
                        {
                            "path": name,
                            "type": "blob",
                            "mode": "120000" if symlink else "100644",
                            "size": 200,
                            "sha": blob,
                        }
                        for name, blob in [
                            ("backend/pyproject.toml", "manifest"),
                            ("backend/uv.lock", "lock"),
                            ("backend/requirements.txt", "export"),
                        ]
                    ]
                }
            if "/git/blobs/" in path:
                value = blobs[path.rsplit("/", 1)[1]].encode()
                return {
                    "content": base64.b64encode(value).decode(),
                    "encoding": "base64",
                    "size": len(value),
                }
            if "/git/commits/" in path:
                return {"tree": {"sha": "original-tree"}}
            raise AssertionError(path)

        def writer(path, **kwargs):
            writes.append((path, kwargs))
            return {"sha": "repair" if path.endswith("/commits") else "tree"}

        return api, writer, writes

    def test_publish_preserves_parent_and_never_force_pushes(self):
        api, writer, writes = self.fixture()
        with patch.object(export, "generate_export", return_value="fastapi==1\n"):
            self.assertTrue(export.repair_export("o/r", 1, "head", api, writer))
        self.assertEqual(writes[0][1]["json_body"]["base_tree"], "original-tree")
        self.assertEqual(writes[1][1]["json_body"]["parents"], ["head"])
        self.assertNotIn("author", writes[1][1]["json_body"])
        self.assertEqual(writes[2][1]["json_body"], {"sha": "repair", "force": False})
        self.assertEqual(writes[2][1]["method"], "PATCH")

    def test_concurrent_head_change_prevents_all_writes(self):
        api, writer, writes = self.fixture(stale=True)
        with (
            patch.object(export, "generate_export", return_value="fastapi==1\n"),
            self.assertRaises(export.ExportNotSafe),
        ):
            export.repair_export("o/r", 1, "head", api, writer)
        self.assertEqual(writes, [])

    def test_symlink_is_not_exported(self):
        api, writer, writes = self.fixture(symlink=True)
        with (
            patch.object(export, "generate_export") as generate,
            self.assertRaises(export.ExportNotSafe),
        ):
            export.repair_export("o/r", 1, "head", api, writer)
        generate.assert_not_called()
        self.assertEqual(writes, [])

    def test_matching_export_does_not_publish_comments_only_change(self):
        api, writer, writes = self.fixture()
        with patch.object(
            export, "generate_export", return_value="# different header\nfastapi==0\n"
        ):
            self.assertFalse(export.repair_export("o/r", 1, "head", api, writer))
        self.assertEqual(writes, [])

    def test_ref_race_propagates_without_retry_or_force(self):
        api, writer, writes = self.fixture()

        def raced(path, **kwargs):
            result = writer(path, **kwargs)
            if "/git/refs/" in path:
                raise RuntimeError("Not a fast forward")
            return result

        with (
            patch.object(export, "generate_export", return_value="fastapi==1\n"),
            self.assertRaises(RuntimeError),
        ):
            export.repair_export("o/r", 1, "head", api, raced)
        self.assertEqual(len(writes), 3)
        self.assertFalse(writes[-1][1]["json_body"]["force"])


if __name__ == "__main__":
    unittest.main()
