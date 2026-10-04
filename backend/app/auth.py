"""Single-user gate. HTTP Basic over HTTPS covers the whole app (API and static files) when
HUB_BASIC_AUTH is set; the browser prompts once and remembers. The dashboard-to-hub bearer
token from the brief lands in phase 5 alongside the metrics endpoint."""

import base64
import secrets

from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send


class BasicAuthMiddleware:
    def __init__(self, app: ASGIApp, credentials: str, exempt_paths: tuple[str, ...] = ()):
        self.app = app
        self.expected = credentials.encode()
        self.exempt_paths = exempt_paths

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["path"] in self.exempt_paths:
            await self.app(scope, receive, send)
            return
        request = Request(scope)
        if self._authorized(request.headers.get("authorization", "")):
            await self.app(scope, receive, send)
            return
        response = Response(
            "Authentication required",
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="Finance Hub", charset="UTF-8"'},
        )
        await response(scope, receive, send)

    def _authorized(self, header: str) -> bool:
        scheme, _, encoded = header.partition(" ")
        if scheme.lower() != "basic" or not encoded:
            return False
        try:
            supplied = base64.b64decode(encoded, validate=True)
        except (ValueError, TypeError):
            return False
        return secrets.compare_digest(supplied, self.expected)
