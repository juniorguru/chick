import os
import asyncio
import logging

from aiohttp.web import AppRunner, TCPSite

from jg.chick.web import web
from jg.chick.bot import bot


logging.basicConfig()
logger = logging.getLogger("jg.chick")
logger.setLevel(logging.INFO)


async def run(host, port, api_key) -> None:
    # inspired by https://stackoverflow.com/a/54462411/325365
    logger.info(f'Starting the web app at {host}:{port}')
    runner = AppRunner(web)
    await runner.setup()
    site = TCPSite(runner, host, port)
    await site.start()

    logger.info('Starting the Discord bot')
    try:
        await bot.start(api_key)
    except:
        await bot.close()
        raise
    finally:
        await runner.cleanup()


def main() -> None:
    logger.info('Configuring')
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '8080'))
    api_key = os.environ['DISCORD_API_KEY']

    logger.info('Starting')
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run(host, port, api_key))
    except KeyboardInterrupt:
        logger.info('Terminating')
