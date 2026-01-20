"""Interests management for automatically adding role members to threads.

This module follows the "functional core, imperative shell" architecture:
- Pure functions (functional core) are in this module and are unit tested
- I/O operations (imperative shell) are in bot.py and tested manually
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

import discord


INTERESTS_API_URL = "https://junior.guru/api/interests.json"
INTERESTS_REFRESH_INTERVAL = timedelta(days=1)
NOTIFICATION_COOLDOWN = timedelta(days=1)
ERROR_REPORT_CHANNEL_ID = 1135903241792651365


logger = logging.getLogger("jg.chick.interests")


# Functional Core - Pure functions with no side effects


def build_thread_to_role_mapping(interests: list[dict[str, Any]]) -> dict[int, int]:
    """
    Builds a thread_id -> role_id mapping from interests data.

    Args:
        interests: List of interest mappings with thread_id and role_id.

    Returns:
        Dictionary mapping thread IDs to role IDs.
    """
    mapping = {}
    for interest in interests:
        thread_id = interest["thread_id"]
        role_id = interest["role_id"]
        mapping[thread_id] = role_id
    return mapping


def should_refresh(last_fetch: datetime | None, now: datetime) -> bool:
    """
    Checks if interests data should be refreshed.

    Args:
        last_fetch: When data was last fetched, or None if never fetched.
        now: Current datetime.

    Returns:
        True if data should be refreshed, False otherwise.
    """
    if last_fetch is None:
        return True
    return now - last_fetch >= INTERESTS_REFRESH_INTERVAL


def try_notify_role(
    role_id: int, last_notifications: dict[int, datetime], now: datetime
) -> tuple[bool, dict[int, datetime]]:
    """
    Checks if a role can be notified and returns updated notification state.

    This function is atomic - it checks and marks in one operation to avoid race conditions.

    Args:
        role_id: The Discord role ID to check.
        last_notifications: Current notification state (role_id -> datetime).
        now: Current datetime.

    Returns:
        Tuple of (can_notify, updated_last_notifications).
        If can_notify is True, the role should be notified and the returned dict
        has been updated with the current time.
    """
    last_time = last_notifications.get(role_id)
    can_notify = last_time is None or (now - last_time >= NOTIFICATION_COOLDOWN)

    if can_notify:
        # Create a new dict with the updated notification time
        updated = last_notifications.copy()
        updated[role_id] = now
        return True, updated
    else:
        return False, last_notifications


# Imperative Shell - Stateful manager with I/O operations


class InterestsManager:
    """
    Manages interests data and notification rate limiting.

    This is the "imperative shell" that coordinates I/O operations and maintains state.
    It delegates pure logic to functional core functions above.
    """

    def __init__(self):
        self.interests: list[dict[str, Any]] = []
        self.last_fetch: datetime | None = None
        self.last_notifications: dict[int, datetime] = {}  # role_id -> last time
        self._thread_to_role: dict[int, int] = {}  # thread_id -> role_id mapping
        self._lock = asyncio.Lock()

    def update_interests(self, interests: list[dict[str, Any]], fetch_time: datetime):
        """
        Updates interests data and rebuilds mappings atomically.

        Args:
            interests: New interests data.
            fetch_time: When the data was fetched.
        """
        # Build new mapping before assigning to ensure atomic replacement
        new_mapping = build_thread_to_role_mapping(interests)

        self.interests = interests
        self.last_fetch = fetch_time
        self._thread_to_role = new_mapping

        logger.info(f"Updated {len(interests)} interest mappings")

    def should_refresh_now(self) -> bool:
        """Checks if interests data should be refreshed now."""
        return should_refresh(self.last_fetch, datetime.now())

    def get_role_for_thread(self, thread_id: int) -> int | None:
        """
        Gets the role ID for a given thread ID.

        Args:
            thread_id: The Discord thread/channel ID.

        Returns:
            The role ID if found, None otherwise.
        """
        # Dictionary reads are atomic in Python, so no lock needed
        return self._thread_to_role.get(thread_id)

    async def try_notify_role_async(self, role_id: int) -> bool:
        """
        Atomically checks if a role can be notified and marks it as notified.

        Args:
            role_id: The Discord role ID to notify.

        Returns:
            True if the role should be notified, False if in cooldown.
        """
        async with self._lock:
            can_notify, updated_notifications = try_notify_role(
                role_id, self.last_notifications, datetime.now()
            )
            if can_notify:
                self.last_notifications = updated_notifications
            return can_notify


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
