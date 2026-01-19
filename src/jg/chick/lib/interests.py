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


class InterestsManager:
    """Manages interests data and notification rate limiting."""

    def __init__(self):
        self.interests: list[dict[str, Any]] = []
        self.last_fetch: datetime | None = None
        self.last_notification: dict[
            int, datetime
        ] = {}  # role_id -> last notification time
        self.thread_to_role: dict[int, int] = {}  # channel_id -> role_id mapping
        self._fetch_lock = asyncio.Lock()

    async def fetch_interests(self) -> bool:
        """
        Fetches interests data from the API.

        Returns:
            True if successful, False otherwise.
        """
        async with self._fetch_lock:
            try:
                logger.info(f"Fetching interests from {INTERESTS_API_URL}")
                async with aiohttp.ClientSession() as session:
                    async with session.get(INTERESTS_API_URL) as resp:
                        if resp.status == 200:
                            self.interests = await resp.json()
                            self.last_fetch = datetime.now()
                            self._rebuild_mappings()
                            logger.info(
                                f"Fetched {len(self.interests)} interest mappings"
                            )
                            return True
                        else:
                            logger.error(
                                f"Failed to fetch interests: HTTP {resp.status}"
                            )
                            return False
            except Exception as e:
                logger.exception(f"Error fetching interests: {e}")
                return False

    def _rebuild_mappings(self):
        """Rebuilds the thread_to_role mapping from interests data."""
        self.thread_to_role = {}
        for interest in self.interests:
            channel_id = interest["channel_id"]
            role_id = interest["role_id"]
            self.thread_to_role[channel_id] = role_id

    def should_refresh(self) -> bool:
        """Checks if interests data should be refreshed."""
        if self.last_fetch is None:
            return True
        return datetime.now() - self.last_fetch >= INTERESTS_REFRESH_INTERVAL

    def can_notify_role(self, role_id: int) -> bool:
        """
        Checks if a role can be notified (not notified recently).

        Args:
            role_id: The Discord role ID to check.

        Returns:
            True if the role can be notified, False if it's in cooldown.
        """
        last_time = self.last_notification.get(role_id)
        if last_time is None:
            return True
        return datetime.now() - last_time >= NOTIFICATION_COOLDOWN

    def mark_role_notified(self, role_id: int):
        """Marks a role as having been notified."""
        self.last_notification[role_id] = datetime.now()

    def get_role_for_thread(self, thread_id: int) -> int | None:
        """
        Gets the role ID for a given thread ID.

        Args:
            thread_id: The Discord thread/channel ID.

        Returns:
            The role ID if found, None otherwise.
        """
        return self.thread_to_role.get(thread_id)

    def is_tracking_thread(self, thread_id: int) -> bool:
        """Checks if a thread is being tracked for interests."""
        return thread_id in self.thread_to_role


async def report_api_error(bot: discord.Client, error_message: str):
    """Reports an API error to the designated error channel."""
    try:
        channel = bot.get_channel(ERROR_REPORT_CHANNEL_ID)
        if channel and isinstance(channel, discord.TextChannel):
            await channel.send(f"⚠️ **Interests API Error**\n\n{error_message}")
            logger.info(f"Reported error to channel {ERROR_REPORT_CHANNEL_ID}")
        else:
            logger.warning(
                f"Could not find error report channel {ERROR_REPORT_CHANNEL_ID}"
            )
    except Exception as e:
        logger.exception(f"Failed to report error to channel: {e}")
