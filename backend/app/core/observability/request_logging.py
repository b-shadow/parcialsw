import logging
import time
from uuid import uuid4

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger("case_inteligente.requests")


class RequestLoggingMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        started_at = time.perf_counter()
        request_id = str(uuid4())

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
                headers = MutableHeaders(scope=message)
                headers.setdefault("X-Request-ID", request_id)
                logger.info(
                    "request completed",
                    extra={
                        "request_id": request_id,
                        "method": scope.get("method"),
                        "path": scope.get("path"),
                        "status_code": message.get("status"),
                        "elapsed_ms": elapsed_ms,
                    },
                )
            await send(message)

        await self.app(scope, receive, send_with_request_id)
