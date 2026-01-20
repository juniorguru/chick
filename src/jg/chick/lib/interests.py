import asyncio
import contextlib
import logging
from datetime import datetime, timedelta
from typing import TypedDict

import aiohttp
import discord


INTERESTS_API_URL = "https://junior.guru/api/interests.json"

ERROR_REPORT_CHANNEL_ID = 1135903241792651365

NOTIFICATION_COOLDOWN = timedelta(days=1)


logger = logging.getLogger("jg.chick.interests")

_lock = asyncio.Lock()


ThreadID = int
RoleID = int
LastNotifiedAt = datetime


class Role(TypedDict):
    id: RoleID
    last_notified_at: LastNotifiedAt | None


Interests = dict[ThreadID, Role]


async def fetch(interests_api_url: str = INTERESTS_API_URL) -> Interests:
    async with (
        aiohttp.ClientSession(raise_for_status=True) as session,
        session.get(interests_api_url) as resp,
    ):
        return {
            interest["thread_id"]: {"id": interest["role_id"], "last_notified_at": None}
            for interest in (await resp.json())
        }


@contextlib.asynccontextmanager
async def report_fetch_error(
    client: discord.Client, channel_id: int = ERROR_REPORT_CHANNEL_ID
):
    try:
        yield
    except Exception as e:
        logger.exception("Failed to fetch interests")
        if channel := client.get_partial_messageable(channel_id):
            try:
                await channel.send(f"⚠️ Failed to fetch interests:\n\n```\n{e}\n```")
            except Exception as send_exc:
                logger.exception(
                    "Failed to send error report message", exc_info=send_exc
                )


def should_notify(role: Role, now: datetime, cooldown: timedelta | None = None) -> bool:
    last_notified_at = role["last_notified_at"]
    if last_notified_at is None:
        return True
    return now - last_notified_at >= (cooldown or NOTIFICATION_COOLDOWN)


@contextlib.asynccontextmanager
async def notifying():
    async with _lock:
        yield
