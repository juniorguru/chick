import asyncio
import logging
import subprocess

import click
from aiohttp.web import AppRunner, TCPSite

from jg.chick.bot import bot
from jg.chick.web import web


logger = logging.getLogger("jg.chick")


async def run(host, port, discord_api_key) -> None:
    # inspired by https://stackoverflow.com/a/54462411/325365
    logger.info(f"Starting the web app at {host}:{port}")
    runner = AppRunner(web)
    await runner.setup()
    site = TCPSite(runner, host, port)
    await site.start()

    logger.info("Starting the Discord bot")
    try:
        await bot.start(discord_api_key)
    except:
        await bot.close()
        raise
    finally:
        await runner.cleanup()


@click.command()
@click.option(
    "-d",
    "--debug",
    default=False,
    is_flag=True,
    help="Show debug logs.",
)
@click.option(
    "--prod",
    "production",
    default=False,
    is_flag=True,
    help="Replace production with this instance.",
)
@click.option(
    "-h",
    "--host",
    envvar="HOST",
    default="0.0.0.0",
    help="Web app host.",
)
@click.option(
    "-p",
    "--port",
    envvar="PORT",
    default=8080,
    help="Web app port.",
    type=int,
)
@click.option(
    "--discord-api-key",
    envvar="DISCORD_API_KEY",
    help="Discord API key.",
)
def main(
    debug: bool, production: bool, host: str, port: int, discord_api_key: str
) -> None:
    logging.basicConfig()
    logging.getLogger("jg").setLevel(logging.DEBUG if debug else logging.INFO)

    logger.info("Starting")
    if production:
        logger.warning("Stopping production environment")
        subprocess.run(["flyctl", "machine", "stop"])

    try:
        asyncio.run(run(host, port, discord_api_key))
    except KeyboardInterrupt:
        logger.info("Terminating")
    finally:
        if production:
            logger.warning("Starting production environment")
            subprocess.run(["flyctl", "machine", "start"])
