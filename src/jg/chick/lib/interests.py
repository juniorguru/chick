"""Interest thread management for the Discord server.

This module handles interest-based threads where members with specific roles
are automatically notified when there's activity in threads they're interested in.
It includes functionality for fetching interest data, managing notification
cooldowns, and thread-safe state modifications.
"""

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
    """Fetch interest thread data from the junior.guru API.

    Args:
        interests_api_url: URL of the interests API endpoint.

    Returns:
        List of interest dictionaries from the API.

    Raises:
        aiohttp.ClientResponseError: If the API request fails.
    """
    async with (
        aiohttp.ClientSession(raise_for_status=True) as session,
        session.get(interests_api_url) as resp,
    ):
        return await resp.json()


def parse(api_payload: list[dict], current_interests: Interests) -> Interests:
    """Parse API payload into internal interests state.

    Preserves last_notified_at timestamps from the current state for
    existing threads, while initializing new threads with None.

    Args:
        api_payload: Raw data from the interests API.
        current_interests: Current in-memory interest state.

    Returns:
        Updated interests dictionary mapping thread IDs to Interest data.
    """
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
    """Context manager that reports fetch errors to a Discord channel.

    Args:
        client: Discord client for sending messages.
        channel_id: Channel ID to send error reports to.

    Yields:
        Nothing, but catches and reports any exceptions.
    """
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
    """Check if a role should be notified about activity in an interest thread.

    Args:
        interest: The interest data containing last notification time.
        now: Current timestamp for comparison.
        cooldown: Optional custom cooldown duration (defaults to NOTIFICATION_COOLDOWN).

    Returns:
        True if enough time has passed since the last notification.
    """
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
