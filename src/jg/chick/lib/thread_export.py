import json
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import TYPE_CHECKING

import discord


if TYPE_CHECKING:
    from collections.abc import Sequence


DENICKY_CHANNEL_ID = 1075087192101244928


@dataclass
class ExportedMessage:
    id: int
    author_id: int
    author_name: str
    content: str
    created_at: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ExportedThread:
    id: int
    name: str
    created_at: str
    messages: list[ExportedMessage]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at,
            "messages": [msg.to_dict() for msg in self.messages],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


def is_in_denicky_channel(thread: discord.Thread) -> bool:
    """Check if the thread is in the deníčky channel."""
    if not thread.parent:
        return False
    return thread.parent.id == DENICKY_CHANNEL_ID


def can_export_thread(
    user: discord.Member | discord.User,
    thread: discord.Thread,
    starting_message: discord.Message | None,
    owner_id: int,
) -> bool:
    """
    Check if the user can export the thread.
    User can export if they are:
    - The bot owner
    - A moderator (has manage_messages permission)
    - The author of the first post in the thread
    """
    if user.id == owner_id:
        return True

    if guild_permissions := getattr(user, "guild_permissions", None):
        if guild_permissions.manage_messages:
            return True

    if starting_message and starting_message.author.id == user.id:
        return True

    return False


def format_datetime(dt: datetime) -> str:
    """Format datetime to ISO 8601 string."""
    return dt.isoformat()


def export_message(message: discord.Message) -> ExportedMessage:
    """Export a single message."""
    return ExportedMessage(
        id=message.id,
        author_id=message.author.id,
        author_name=message.author.display_name,
        content=message.content,
        created_at=format_datetime(message.created_at),
    )


async def export_thread_messages(
    thread: discord.Thread,
) -> "Sequence[ExportedMessage]":
    """Fetch and export all messages from a thread, oldest first."""
    messages: list[ExportedMessage] = []

    async for message in thread.history(limit=None, oldest_first=True):
        messages.append(export_message(message))

    return messages


async def export_thread(thread: discord.Thread) -> ExportedThread:
    """Export a thread with all its messages."""
    messages = await export_thread_messages(thread)

    created_at = thread.created_at or thread.archive_timestamp
    created_at_str = format_datetime(created_at) if created_at else ""

    return ExportedThread(
        id=thread.id,
        name=thread.name,
        created_at=created_at_str,
        messages=list(messages),
    )
