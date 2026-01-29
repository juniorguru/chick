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
    thread = cast(discord.Thread, MockThread())
    starting_message = cast(discord.Message, MockMessage(1, 99999, "Other", "Hello"))

    assert can_export_thread(user, thread, starting_message, owner_id=12345) is True


def test_can_export_thread_moderator():
    user = cast(discord.Member, MockMember(user_id=12345, manage_messages=True))
    thread = cast(discord.Thread, MockThread())
    starting_message = cast(discord.Message, MockMessage(1, 99999, "Other", "Hello"))

    assert can_export_thread(user, thread, starting_message, owner_id=0) is True


def test_can_export_thread_author():
    user = cast(discord.Member, MockMember(user_id=12345))
    thread = cast(discord.Thread, MockThread())
    starting_message = cast(discord.Message, MockMessage(1, 12345, "Author", "Hello"))

    assert can_export_thread(user, thread, starting_message, owner_id=0) is True


def test_can_export_thread_unauthorized():
    user = cast(discord.Member, MockMember(user_id=12345))
    thread = cast(discord.Thread, MockThread())
    starting_message = cast(discord.Message, MockMessage(1, 99999, "Other", "Hello"))

    assert can_export_thread(user, thread, starting_message, owner_id=0) is False


def test_can_export_thread_no_starting_message():
    user = cast(discord.Member, MockMember(user_id=12345))
    thread = cast(discord.Thread, MockThread())

    assert can_export_thread(user, thread, None, owner_id=0) is False


def test_can_export_thread_user_not_member():
    user = cast(discord.User, MockUser(user_id=12345))
    thread = cast(discord.Thread, MockThread())
    starting_message = cast(discord.Message, MockMessage(1, 12345, "Author", "Hello"))

    assert can_export_thread(user, thread, starting_message, owner_id=0) is True


def test_can_export_thread_user_not_member_unauthorized():
    user = cast(discord.User, MockUser(user_id=12345))
    thread = cast(discord.Thread, MockThread())
    starting_message = cast(discord.Message, MockMessage(1, 99999, "Other", "Hello"))

    assert can_export_thread(user, thread, starting_message, owner_id=0) is False


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
        pytest.param(100, 100, False, 0, True, id="author can export"),
        pytest.param(100, 200, True, 0, True, id="moderator can export"),
        pytest.param(100, 200, False, 100, True, id="owner can export"),
        pytest.param(100, 200, False, 0, False, id="random user cannot export"),
        pytest.param(100, 200, True, 100, True, id="owner+moderator can export"),
    ],
)
def test_can_export_thread_parametrized(
    user_id: int, author_id: int, is_moderator: bool, owner_id: int, expected: bool
):
    user = cast(
        discord.Member, MockMember(user_id=user_id, manage_messages=is_moderator)
    )
    thread = cast(discord.Thread, MockThread())
    starting_message = cast(
        discord.Message, MockMessage(1, author_id, "Author", "Hello")
    )

    assert can_export_thread(user, thread, starting_message, owner_id) is expected
