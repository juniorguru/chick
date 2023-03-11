import logging
from datetime import datetime

from aiohttp.web import Application, RouteTableDef, json_response, Request


LAUNCH_AT = datetime.utcnow()


logger = logging.getLogger("chick.web")


web = Application()
routes = RouteTableDef()


@routes.get('/')
async def index(request: Request) -> None:
    logger.info(f'Received {request!r}')
    return json_response({'status': 'ok',
                          'launch_at': LAUNCH_AT.isoformat(),
                          'uptime_sec': (datetime.utcnow() - LAUNCH_AT).seconds})


web.add_routes(routes)
