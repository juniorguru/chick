import os
import asyncio
import logging

from aiohttp.web import AppRunner, TCPSite

from juniorguru_chick.web import web
from juniorguru_chick.bot import bot


HOST = os.getenv('HOST', '0.0.0.0')

PORT = int(os.getenv('PORT', '8080'))

DISCORD_API_KEY = os.getenv('DISCORD_API_KEY')


logging.basicConfig()
logger = logging.getLogger("chick")
logger.setLevel(logging.INFO)


async def run() -> None:
    # inspired by https://stackoverflow.com/a/54462411/325365
    logger.info(f'Starting the web app at {HOST}:{PORT}')
    runner = AppRunner(web)
    await runner.setup()
    site = TCPSite(runner, HOST, PORT)
    await site.start()

    logger.info('Starting the Discord bot')
    try:
        await bot.start(DISCORD_API_KEY)
    except:
        bot.close()
        raise
    finally:
        await runner.cleanup()


def main() -> None:
    logger.info('Starting')
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run())
    except KeyboardInterrupt:
        logger.info('Terminating')
