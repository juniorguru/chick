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


class Interest(TypedDict):
    role_id: RoleID
    last_notified_at: LastNotifiedAt | None


Interests = dict[ThreadID, Interest]


async def fetch(interests_api_url: str = INTERESTS_API_URL) -> list[dict]:
    async with (
        aiohttp.ClientSession(raise_for_status=True) as session,
        session.get(interests_api_url) as resp,
    ):
        return await resp.json()


def parse(api_payload: list[dict], current_interests: Interests) -> Interests:
    current_state = {
        interest_id: interest["last_notified_at"]
        for interest_id, interest in (current_interests or {}).items()
    }
    return {
        item["thread_id"]: {
            "role_id": item["role_id"],
            "last_notified_at": current_state.get(item["thread_id"]),
        }
        for item in api_payload
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


def should_notify(
    interest: Interest, now: datetime, cooldown: timedelta | None = None
) -> bool:
    last_notified_at = interest["last_notified_at"]
    if last_notified_at is None:
        return True
    return now - last_notified_at >= (cooldown or NOTIFICATION_COOLDOWN)


@contextlib.asynccontextmanager
async def modifications():
    """
    Avoids duplicate notifications or updating notification state inconsistently
    """
    async with _lock:
        yield
