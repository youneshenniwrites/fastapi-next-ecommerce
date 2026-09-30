"""Explicitly enabled development-only synthetic observability exercise."""

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import require_admin
from app.core.settings import settings

router = APIRouter()


def enabled():
    if (
        not settings.SENTRY_DIAGNOSTICS_ENABLED
        or settings.SENTRY_ENVIRONMENT != "development"
    ):
        raise HTTPException(404, "Not found")


@router.post(
    "/api/v1/diagnostics/sentry",
    include_in_schema=False,
    dependencies=[Depends(enabled), Depends(require_admin)],
)
def sentry_diagnostic():
    raise RuntimeError("Development observability verification")
