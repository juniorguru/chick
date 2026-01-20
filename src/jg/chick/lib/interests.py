"""Interests management for automatically adding role members to threads."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp
import discord


INTERESTS_API_URL = "https://junior.guru/api/interests.json"
INTERESTS_REFRESH_INTERVAL = timedelta(days=1)
NOTIFICATION_COOLDOWN = timedelta(days=1)
ERROR_REPORT_CHANNEL_ID = 1135903241792651365


logger = logging.getLogger("jg.chick.interests")


# Module-level state
_last_fetch_time: datetime | None = None
_last_notifications: dict[int, datetime] = {}
_thread_to_role: dict[int, int] = {}
_lock = asyncio.Lock()


def should_refresh(last_fetch_time: datetime | None, now: datetime) -> bool:
    if last_fetch_time is None:
        return True
    return now - last_fetch_time >= INTERESTS_REFRESH_INTERVAL


def try_notify_role(
    role_id: int, last_notifications: dict[int, datetime], now: datetime
) -> tuple[bool, dict[int, datetime]]:
    last_time = last_notifications.get(role_id)
    can_notify = last_time is None or (now - last_time >= NOTIFICATION_COOLDOWN)

    if can_notify:
        updated = last_notifications | {role_id: now}
        return True, updated
    return False, last_notifications


def update(interests: list[dict[str, Any]], fetch_time: datetime):
    global _last_fetch_time, _thread_to_role
    _thread_to_role = {
        interest["thread_id"]: interest["role_id"] for interest in interests
    }
    _last_fetch_time = fetch_time
    logger.info(f"Updated {len(interests)} interest mappings")


def should_refresh_now(now: datetime | None = None) -> bool:
    now = now or datetime.now()
    return should_refresh(_last_fetch_time, now)


def get_role_for_thread(thread_id: int) -> int | None:
    return _thread_to_role.get(thread_id)


async def try_notify_role_async(role_id: int) -> bool:
    global _last_notifications
    async with _lock:
        can_notify, updated_notifications = try_notify_role(
            role_id, _last_notifications, datetime.now()
        )
        if can_notify:
            _last_notifications = updated_notifications
        return can_notify


async def fetch_interests(
    interests_api_url: str, client: discord.Client, now: datetime | None = None
) -> list[dict[str, Any]] | None:
    try:
        logger.info(f"Fetching interests from {interests_api_url}")
        async with (
            aiohttp.ClientSession() as session,
            session.get(interests_api_url) as resp,
        ):
            if resp.status == 200:
                return await resp.json()
            else:
                error_msg = f"Failed to fetch interests: HTTP {resp.status}"
                logger.error(error_msg)
                await report_api_error(client, error_msg)
                return None
    except Exception as e:
        error_msg = f"Error fetching interests: {e}"
        logger.exception(error_msg)
        await report_api_error(client, error_msg)
        return None


async def report_api_error(client: discord.Client, error_message: str):
    try:
        channel = client.get_channel(ERROR_REPORT_CHANNEL_ID)
        if channel and isinstance(channel, discord.TextChannel):
            await channel.send(f"⚠️ **Interests API Error**\n\n{error_message}")
            logger.info(f"Reported error to channel {ERROR_REPORT_CHANNEL_ID}")
        else:
            logger.warning(
                f"Could not find error report channel {ERROR_REPORT_CHANNEL_ID}"
            )
    except Exception as e:
        logger.exception(f"Failed to report error to channel: {e}")
