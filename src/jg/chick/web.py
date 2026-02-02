"""Simple web server for health checks and monitoring.

This module provides a minimal HTTP server used by deployment platforms
(like Fly.io) to verify the bot is running and healthy.
"""

import logging
from datetime import UTC, datetime

from aiohttp.web import Application, Request, Response, RouteTableDef, json_response


LAUNCH_AT = datetime.now(UTC)


logger = logging.getLogger("jg.chick.web")


web = Application()
routes = RouteTableDef()


@routes.get("/")
async def index(request: Request) -> Response:
    logger.info(f"Received {request!r}")
    return json_response(
        {
            "status": "ok",
            "launch_at": LAUNCH_AT.isoformat(),
            "uptime_sec": (datetime.now(UTC) - LAUNCH_AT).seconds,
        }
    )


web.add_routes(routes)
