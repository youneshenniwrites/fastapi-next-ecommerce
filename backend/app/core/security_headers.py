"""Baseline response headers; CSP and transport policy are separate work."""

from fastapi import Request
from fastapi.responses import PlainTextResponse
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        async def send_response(message: Message) -> None:
            if scope["type"] == "http" and message["type"] == "http.response.start":
                MutableHeaders(scope=message).update(SECURITY_HEADERS)
            await send(message)

        await self.app(scope, receive, send_response)


async def internal_server_error(request: Request, exc: Exception) -> PlainTextResponse:
    """Keep Starlette's default body; its outer error middleware still re-raises."""
    return PlainTextResponse(
        "Internal Server Error", status_code=500, headers=SECURITY_HEADERS
    )
