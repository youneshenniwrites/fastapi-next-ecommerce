"""Enforced framing, transport and nonce-backed content security policies."""

import secrets

from fastapi import Request
from fastapi.responses import PlainTextResponse
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "frame-ancestors 'none'",
}

DENY_CONTENT_POLICY = (
    "default-src 'none'; base-uri 'none'; object-src 'none'; "
    "form-action 'none'; frame-ancestors 'none'"
)

# ReDoc 2.5.4's perfect-scrollbar style-loader inserts an empty <style>, then
# fills it before Redoc.init can supply the nonce. These exact browser-verified
# hashes allow that stylesheet and its empty insertion, without allowing other
# inline style elements. Reverify both against the CDN bundle when upgrading
# the pinned redoc_js_url in app.main; runtime styled-components use the nonce.
REDOC_EARLY_STYLE_HASHES = (
    "'sha256-47DEQpj8HBSa+/TImW+5JCeuQeRkm5NMpJWZG3hSuFU=' "
    "'sha256-QMIg+bpjm3JdElJ388KYke01izlUW0UoNOeKjpMxdgc='"
)


def content_policy(document: str | None = None, nonce: str = "") -> str:
    """Allow only the sources needed by the generated documentation page."""
    if document not in {"swagger", "redoc", "oauth-redirect"}:
        return DENY_CONTENT_POLICY

    directives = [
        "default-src 'none'",
        "base-uri 'none'",
        "object-src 'none'",
        "form-action 'self'",
        "frame-ancestors 'none'",
        "connect-src 'self'",
    ]
    script_sources = f"'nonce-{nonce}'"
    if document in {"swagger", "redoc"}:
        # External UI scripts carry a nonce too; no broad CDN script allowance.
        image_sources = "'self' data: https://fastapi.tiangolo.com"
        if document == "redoc":
            image_sources += " https://cdn.redoc.ly"
        directives.extend(
            [
                f"img-src {image_sources}",
                # Both documentation UIs set layout styles directly on elements.
                # This exception does not allow inline scripts or style elements.
                "style-src-attr 'unsafe-inline'",
            ]
        )
        style_sources = f"'self' 'nonce-{nonce}'"
        if document == "swagger":
            style_sources += " https://cdn.jsdelivr.net"
            directives.append("font-src 'self' data:")
        else:
            style_sources += f" {REDOC_EARLY_STYLE_HASHES}"
            directives.append("font-src 'self'")
            # ReDoc's search index is built in an embedded blob worker.
            directives.append("worker-src blob:")
        directives.append(f"style-src {style_sources}")
    directives.append(f"script-src {script_sources}")
    return "; ".join(directives)


def response_security_headers(
    document: str | None = None, nonce: str = "", *, https: bool = False
) -> dict[str, str]:
    headers = {
        **SECURITY_HEADERS,
        "Content-Security-Policy": content_policy(document, nonce),
    }
    # ASGI's scheme is authoritative; never trust arbitrary forwarded headers here.
    # Browsers ignore HSTS on HTTP. Subdomains/preload are deliberately excluded.
    if https:
        headers["Strict-Transport-Security"] = "max-age=31536000"
    return headers


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        state = scope.setdefault("state", {})
        # Each response gets a cryptographically random nonce, never a cached value.
        state["csp_nonce"] = secrets.token_urlsafe(32)

        async def send_response(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                document = None
                if message["status"] == 200 and headers.get(
                    "content-type", ""
                ).startswith("text/html"):
                    document = state.get("csp_document")
                    # Nonce-bearing HTML must not be replayed from a shared cache.
                    headers["Cache-Control"] = "private, no-store"
                headers.update(
                    response_security_headers(
                        document,
                        state["csp_nonce"],
                        https=scope.get("scheme") == "https",
                    )
                )
            await send(message)

        await self.app(scope, receive, send_response)


async def internal_server_error(request: Request, exc: Exception) -> PlainTextResponse:
    """Keep Starlette's default body; its outer error middleware still re-raises."""
    return PlainTextResponse(
        "Internal Server Error",
        status_code=500,
        headers=response_security_headers(https=request.scope.get("scheme") == "https"),
    )
