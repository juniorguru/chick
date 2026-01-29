from datetime import UTC, datetime
from typing import cast

import discord
import pytest

from jg.chick.lib.thread_export import (
    DENICKY_CHANNEL_ID,
    ExportedMessage,
    ExportedThread,
    can_export_thread,
    export_message,
    export_thread,
    export_thread_messages,
    format_datetime,
    is_in_denicky_channel,
)


class MockGuildPermissions:
    def __init__(self, manage_messages: bool = False):
        self.manage_messages = manage_messages


class MockMember:
    def __init__(self, user_id: int, manage_messages: bool = False):
        self.id = user_id
        self.guild_permissions = MockGuildPermissions(manage_messages)


class MockUser:
    def __init__(self, user_id: int):
        self.id = user_id


class MockAuthor:
    def __init__(self, user_id: int, display_name: str):
        self.id = user_id
        self.display_name = display_name


class MockMessage:
    def __init__(self, message_id: int, author_id: int, author_name: str, content: str):
        self.id = message_id
        self.author = MockAuthor(author_id, author_name)
        self.content = content
        self.created_at = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)


class MockParentChannel:
    def __init__(self, channel_id: int):
        self.id = channel_id


class MockThread:
    def __init__(self, parent_id: int | None = None):
        self.parent = MockParentChannel(parent_id) if parent_id else None


# Tests for is_in_denicky_channel


def test_is_in_denicky_channel_true():
    thread = cast(discord.Thread, MockThread(parent_id=DENICKY_CHANNEL_ID))
    assert is_in_denicky_channel(thread) is True


def test_is_in_denicky_channel_false_different_channel():
    thread = cast(discord.Thread, MockThread(parent_id=123456789))
    assert is_in_denicky_channel(thread) is False


def test_is_in_denicky_channel_false_no_parent():
    thread = cast(discord.Thread, MockThread(parent_id=None))
    assert is_in_denicky_channel(thread) is False


# Tests for can_export_thread


def test_can_export_thread_owner():
    user = cast(discord.Member, MockMember(user_id=12345))
    starting_message = cast(discord.Message, MockMessage(1, 99999, "Other", "Hello"))

    assert can_export_thread(user, starting_message, owner_id=12345) is True


def test_can_export_thread_moderator():
    user = cast(discord.Member, MockMember(user_id=12345, manage_messages=True))
    starting_message = cast(discord.Message, MockMessage(1, 99999, "Other", "Hello"))

    assert can_export_thread(user, starting_message, owner_id=None) is True


def test_can_export_thread_author():
    user = cast(discord.Member, MockMember(user_id=12345))
    starting_message = cast(discord.Message, MockMessage(1, 12345, "Author", "Hello"))

    assert can_export_thread(user, starting_message, owner_id=None) is True


def test_can_export_thread_unauthorized():
    user = cast(discord.Member, MockMember(user_id=12345))
    starting_message = cast(discord.Message, MockMessage(1, 99999, "Other", "Hello"))

    assert can_export_thread(user, starting_message, owner_id=None) is False


def test_can_export_thread_no_starting_message():
    user = cast(discord.Member, MockMember(user_id=12345))

    assert can_export_thread(user, None, owner_id=None) is False


def test_can_export_thread_user_not_member():
    user = cast(discord.User, MockUser(user_id=12345))
    starting_message = cast(discord.Message, MockMessage(1, 12345, "Author", "Hello"))

    assert can_export_thread(user, starting_message, owner_id=None) is True


def test_can_export_thread_user_not_member_unauthorized():
    user = cast(discord.User, MockUser(user_id=12345))
    starting_message = cast(discord.Message, MockMessage(1, 99999, "Other", "Hello"))

    assert can_export_thread(user, starting_message, owner_id=None) is False


# Tests for format_datetime


def test_format_datetime():
    dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
    assert format_datetime(dt) == "2024-01-15T10:30:00+00:00"


def test_format_datetime_naive():
    dt = datetime(2024, 1, 15, 10, 30, 0)
    assert format_datetime(dt) == "2024-01-15T10:30:00"


# Tests for export_message


def test_export_message():
    message = cast(discord.Message, MockMessage(123, 456, "TestUser", "Hello world"))
    exported = export_message(message)

    assert exported.id == 123
    assert exported.author_id == 456
    assert exported.author_name == "TestUser"
    assert exported.content == "Hello world"
    assert exported.created_at == "2024-01-15T10:30:00+00:00"


# Tests for ExportedMessage


def test_exported_message_to_dict():
    msg = ExportedMessage(
        id=123,
        author_id=456,
        author_name="TestUser",
        content="Hello world",
        created_at="2024-01-15T10:30:00+00:00",
    )
    result = msg.to_dict()

    assert result == {
        "id": 123,
        "author_id": 456,
        "author_name": "TestUser",
        "content": "Hello world",
        "created_at": "2024-01-15T10:30:00+00:00",
    }


# Tests for ExportedThread


def test_exported_thread_to_dict():
    messages = [
        ExportedMessage(1, 100, "User1", "First message", "2024-01-15T10:00:00+00:00"),
        ExportedMessage(2, 200, "User2", "Second message", "2024-01-15T10:01:00+00:00"),
    ]
    thread = ExportedThread(
        id=999,
        name="Test Thread",
        created_at="2024-01-15T09:00:00+00:00",
        messages=messages,
    )
    result = thread.to_dict()

    assert result["id"] == 999
    assert result["name"] == "Test Thread"
    assert result["created_at"] == "2024-01-15T09:00:00+00:00"
    assert len(result["messages"]) == 2
    assert result["messages"][0]["author_name"] == "User1"
    assert result["messages"][1]["author_name"] == "User2"


def test_exported_thread_to_json():
    messages = [
        ExportedMessage(1, 100, "User1", "Hello", "2024-01-15T10:00:00+00:00"),
    ]
    thread = ExportedThread(
        id=999,
        name="Test Thread",
        created_at="2024-01-15T09:00:00+00:00",
        messages=messages,
    )
    json_output = thread.to_json()

    assert '"id": 999' in json_output
    assert '"name": "Test Thread"' in json_output
    assert '"author_name": "User1"' in json_output


def test_exported_thread_to_json_unicode():
    messages = [
        ExportedMessage(1, 100, "Honza", "Ahoj světe! 👋", "2024-01-15T10:00:00+00:00"),
    ]
    thread = ExportedThread(
        id=999,
        name="Můj deníček",
        created_at="2024-01-15T09:00:00+00:00",
        messages=messages,
    )
    json_output = thread.to_json()

    assert "Ahoj světe! 👋" in json_output
    assert "Můj deníček" in json_output


@pytest.mark.parametrize(
    "user_id, author_id, is_moderator, owner_id, expected",
    [
        pytest.param(100, 100, False, None, True, id="author can export"),
        pytest.param(100, 200, True, None, True, id="moderator can export"),
        pytest.param(100, 200, False, 100, True, id="owner can export"),
        pytest.param(100, 200, False, None, False, id="random user cannot export"),
        pytest.param(100, 200, True, 100, True, id="owner+moderator can export"),
    ],
)
def test_can_export_thread_parametrized(
    user_id: int,
    author_id: int,
    is_moderator: bool,
    owner_id: int | None,
    expected: bool,
):
    user = cast(
        discord.Member, MockMember(user_id=user_id, manage_messages=is_moderator)
    )
    starting_message = cast(
        discord.Message, MockMessage(1, author_id, "Author", "Hello")
    )

    assert can_export_thread(user, starting_message, owner_id) is expected


# Tests for async functions


class MockThreadWithHistory:
    def __init__(
        self,
        thread_id: int,
        name: str,
        messages: list,
        created_at: datetime | None = None,
    ):
        self.id = thread_id
        self.name = name
        self._messages = messages
        self.created_at = created_at
        self.archive_timestamp = datetime(2024, 1, 15, 8, 0, 0, tzinfo=UTC)

    def history(self, limit: int | None = None, oldest_first: bool = False):
        return MockAsyncIterator(self._messages, oldest_first)


class MockAsyncIterator:
    def __init__(self, items: list, oldest_first: bool = False):
        self._items = items if oldest_first else list(reversed(items))
        self._index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._index >= len(self._items):
            raise StopAsyncIteration
        item = self._items[self._index]
        self._index += 1
        return item


@pytest.mark.asyncio
async def test_export_thread_messages():
    messages = [
        MockMessage(1, 100, "User1", "First message"),
        MockMessage(2, 200, "User2", "Second message"),
        MockMessage(3, 100, "User1", "Third message"),
    ]
    thread = cast(discord.Thread, MockThreadWithHistory(999, "Test Thread", messages))

    exported = await export_thread_messages(thread)

    assert len(exported) == 3
    assert exported[0].id == 1
    assert exported[0].author_name == "User1"
    assert exported[0].content == "First message"
    assert exported[1].id == 2
    assert exported[1].author_name == "User2"
    assert exported[2].id == 3


@pytest.mark.asyncio
async def test_export_thread_messages_empty():
    thread = cast(discord.Thread, MockThreadWithHistory(999, "Empty Thread", []))

    exported = await export_thread_messages(thread)

    assert len(exported) == 0


@pytest.mark.asyncio
async def test_export_thread():
    messages = [
        MockMessage(1, 100, "User1", "Hello"),
        MockMessage(2, 200, "User2", "World"),
    ]
    created_at = datetime(2024, 1, 15, 9, 0, 0, tzinfo=UTC)
    thread = cast(
        discord.Thread,
        MockThreadWithHistory(999, "Test Thread", messages, created_at=created_at),
    )

    exported = await export_thread(thread)

    assert exported.id == 999
    assert exported.name == "Test Thread"
    assert exported.created_at == "2024-01-15T09:00:00+00:00"
    assert len(exported.messages) == 2
    assert exported.messages[0].content == "Hello"
    assert exported.messages[1].content == "World"


@pytest.mark.asyncio
async def test_export_thread_uses_archive_timestamp_when_no_created_at():
    messages = [MockMessage(1, 100, "User1", "Hello")]
    thread = cast(
        discord.Thread,
        MockThreadWithHistory(999, "Test Thread", messages, created_at=None),
    )

    exported = await export_thread(thread)

    assert exported.created_at == "2024-01-15T08:00:00+00:00"
