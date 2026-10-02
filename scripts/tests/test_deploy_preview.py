"""Prove provider targeting, source extraction and credential boundary failures."""

import io
import os
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import deploy_preview as deploy


class PreviewBoundaryTests(unittest.TestCase):
    def project(self):
        return {
            "id": deploy.PROJECT,
            "accountId": deploy.TEAM,
            "rootDirectory": "frontend",
            "autoExposeSystemEnvs": True,
            "ssoProtection": {"deploymentType": "prod_deployment_urls"},
        }

    def test_empty_preview_scope_and_correct_protected_project(self):
        deploy.audit_project(self.project(), {"envs": []})
        for changes in [
            {"id": "production"},
            {"accountId": "other"},
            {"ssoProtection": None},
            {"autoExposeSystemEnvs": False},
            {"rootDirectory": "backend"},
        ]:
            with self.assertRaises(ValueError):
                deploy.audit_project({**self.project(), **changes}, {"envs": []})
        with self.assertRaises(ValueError):
            deploy.audit_project(
                self.project(),
                {
                    "envs": [
                        {"key": "DATABASE_URL", "target": ["preview", "production"]}
                    ]
                },
            )
        with self.assertRaises(ValueError):
            deploy.audit_project(
                self.project(), {"envs": [], "pagination": {"next": 10}}
            )
        deploy.audit_project(
            self.project(),
            {"envs": [{"key": "DATABASE_URL", "target": ["production"]}]},
        )

    def test_missing_or_unknown_scope_is_not_empty_preview_evidence(self):
        for variables in [
            {},
            {"envs": None},
            {"envs": [{}]},
            {"envs": [{"target": []}]},
            {"envs": [{"target": ["unknown"]}]},
        ]:
            with self.assertRaises((TypeError, ValueError)):
                deploy.audit_project(self.project(), variables)

    def test_creation_must_be_ready_and_match_requested_revision(self):
        deployment = {
            "id": "dpl_Test123",
            "projectId": deploy.PROJECT,
            "target": None,
            "url": "preview-123.vercel.app",
            "readyState": "READY",
            "meta": {
                "vin45": "reviewed-preview",
                "vin45head": "a" * 40,
                "vin45pr": "45",
            },
        }
        deploy.created_identity(deployment, "a" * 40, 45)
        for changes in [
            {"readyState": "BUILDING"},
            {"meta": {**deployment["meta"], "vin45head": "b" * 40}},
            {"meta": {**deployment["meta"], "vin45pr": "46"}},
        ]:
            with self.assertRaises(ValueError):
                deploy.created_identity({**deployment, **changes}, "a" * 40, 45)

    @patch.dict(
        os.environ,
        {
            "GITHUB_REF": "refs/heads/main",
            "VERCEL_ORG_ID": deploy.TEAM,
            "VERCEL_FRONTEND_PROJECT_ID": deploy.PROJECT,
            "PREVIEW_OPERATION": "retire",
            "PREVIEW_DEPLOYMENT_ID": "dpl_Test123",
            "GITHUB_STEP_SUMMARY": "/unused",
        },
    )
    @patch.object(deploy, "retirement_allowed")
    @patch.object(deploy, "vercel_api")
    def test_delete_does_not_claim_cleanup_while_deployment_still_exists(
        self, api, allowed
    ):
        api.return_value = {}
        with self.assertRaisesRegex(RuntimeError, "not been confirmed"):
            deploy.main()
        self.assertEqual(
            api.call_args_list[-2].args, ("v13/deployments/dpl_Test123", "DELETE")
        )
        self.assertEqual(api.call_args_list[-1].args, ("v13/deployments/dpl_Test123",))

    def test_retirement_rejects_promoted_or_aliased_previews(self):
        deployment = {
            "id": "dpl_Test123",
            "projectId": deploy.PROJECT,
            "target": None,
            "url": "preview-123.vercel.app",
            "meta": {"vin45": "reviewed-preview", "vin45head": "a" * 40},
        }
        project = {
            "id": deploy.PROJECT,
            "targets": {"production": {"id": "dpl_Stable123"}},
        }
        self.assertEqual(
            deploy.retirement_allowed(deployment, project, {"aliases": []}),
            "dpl_Test123",
        )
        for altered in [
            {},
            {"id": deploy.PROJECT},
            {**project, "targets": {"production": {"id": "dpl_Test123"}}},
        ]:
            with self.assertRaises(ValueError):
                deploy.retirement_allowed(deployment, altered, {"aliases": []})
        for aliases in [
            {},
            {"aliases": [{"alias": "forme-ecommerce-development.vercel.app"}]},
            {"aliases": [{"alias": "shop.example"}]},
            {"aliases": [], "pagination": {"next": 1}},
        ]:
            with self.assertRaises(ValueError):
                deploy.retirement_allowed(deployment, project, aliases)

    @patch.dict(
        os.environ,
        {
            "GH_TOKEN": "private-gh",
            "VERCEL_TOKEN": "private-vercel",
            "DATABASE_URL": "private-db",
            "RATE_LIMIT_PROXY_SECRET": "private-signing",
        },
    )
    def test_cli_environment_has_no_credentials(self):
        child = deploy.cli_env()
        self.assertTrue(
            {
                "GH_TOKEN",
                "VERCEL_TOKEN",
                "DATABASE_URL",
                "RATE_LIMIT_PROXY_SECRET",
            }.isdisjoint(child)
        )
        self.assertNotIn("private", str(child))

    def archive(self, name, link=False):
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w") as archive:
            info = tarfile.TarInfo(name)
            if link:
                info.type = tarfile.SYMTYPE
                info.linkname = "/etc/passwd"
                archive.addfile(info)
            else:
                data = b"fictional"
                info.size = len(data)
                archive.addfile(info, io.BytesIO(data))
        return buf.getvalue()

    def test_source_cannot_execute_cli_config_or_upload_environment_files(self):
        with tempfile.TemporaryDirectory() as root:
            for name in [
                "frontend/vercel.ts",
                "frontend/vercel.mts",
                "vercel.js",
                ".vercel/project.json",
                "frontend/.env.local",
                "../escape",
            ]:
                with self.assertRaises((ValueError, tarfile.FilterError)):
                    deploy.extract_source(self.archive(name), Path(root))
            with self.assertRaises(ValueError):
                deploy.extract_source(self.archive("link", True), Path(root))
            deploy.extract_source(self.archive("frontend/.env.example"), Path(root))
            self.assertTrue((Path(root) / "frontend/.env.example").exists())

    def test_retirement_requires_exact_managed_non_production_deployment(self):
        deployment = {
            "id": "dpl_Test123",
            "projectId": deploy.PROJECT,
            "target": None,
            "url": "preview-123.vercel.app",
            "meta": {"vin45": "reviewed-preview", "vin45head": "a" * 40},
        }
        self.assertEqual(
            deploy.preview_identity(deployment),
            ("dpl_Test123", "https://preview-123.vercel.app"),
        )
        for changes in [
            {"target": "production"},
            {"target": "staging"},
            {"projectId": "prod"},
            {"meta": {}},
            {"id": "forme-ecommerce-development"},
            {"url": "attacker.example"},
        ]:
            with self.assertRaises(ValueError):
                deploy.preview_identity({**deployment, **changes})


if __name__ == "__main__":
    unittest.main()
