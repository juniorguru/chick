"""Tests for interests management functionality."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import discord
import pytest

from jg.chick.lib import interests
from jg.chick.lib.interests import (
    NOTIFICATION_COOLDOWN,
    report_api_error,
    should_refresh,
    try_notify_role,
)


@pytest.fixture
def sample_interests_data():
    """Sample interests data as returned from the API (new format with thread_id)."""
    return [
        {
            "thread_id": 1417459492093693952,
            "role_id": 1420401262658060328,
        },
        {
            "thread_id": 1303022608148594808,
            "role_id": 1420401262658060328,
        },
        {
            "thread_id": 1421134766488420368,
            "role_id": 1085220896005963778,
        },
    ]


@pytest.fixture(autouse=True)
def reset_interests_state():
    """Reset the module-level state before each test."""
    interests._last_fetch_time = None
    interests._last_notifications = {}
    interests._thread_to_role = {}
    yield


def test_should_refresh_never_fetched():
    now = datetime.now()
    assert should_refresh(None, now) is True


def test_should_refresh_recently_fetched():
    now = datetime.now()
    last_fetch_time = now - timedelta(hours=12)
    assert should_refresh(last_fetch_time, now) is False


def test_should_refresh_old_fetch():
    now = datetime.now()
    last_fetch_time = now - timedelta(days=2)
    assert should_refresh(last_fetch_time, now) is True


def test_try_notify_role_never_notified():
    last_notifications = {}
    now = datetime.now()

    can_notify, updated = try_notify_role(12345, last_notifications, now)

    assert can_notify is True
    assert 12345 in updated
    assert updated[12345] == now
    assert 12345 not in last_notifications


def test_try_notify_role_recently_notified():
    now = datetime.now()
    last_notifications = {12345: now - timedelta(hours=12)}

    can_notify, updated = try_notify_role(12345, last_notifications, now)

    assert can_notify is False
    assert updated == last_notifications


def test_try_notify_role_cooldown_expired():
    now = datetime.now()
    old_time = now - NOTIFICATION_COOLDOWN - timedelta(seconds=1)
    last_notifications = {12345: old_time}

    can_notify, updated = try_notify_role(12345, last_notifications, now)

    assert can_notify is True
    assert updated[12345] == now
    assert updated[12345] != old_time


def test_update(sample_interests_data):
    now = datetime.now()
    interests.update(sample_interests_data, now)

    assert interests._last_fetch_time == now
    assert interests.get_role_for_thread(1417459492093693952) == 1420401262658060328


def test_should_refresh_now_never_fetched():
    assert interests.should_refresh_now() is True


def test_should_refresh_now_recently_fetched(sample_interests_data):
    interests.update(sample_interests_data, datetime.now())
    assert interests.should_refresh_now() is False


def test_should_refresh_now_old_fetch(sample_interests_data):
    old_time = datetime.now() - timedelta(days=2)
    interests.update(sample_interests_data, old_time)
    assert interests.should_refresh_now() is True


def test_should_refresh_now_with_dependency_injection(sample_interests_data):
    fetch_time = datetime(2024, 1, 1, 12, 0)
    interests.update(sample_interests_data, fetch_time)

    now = datetime(2024, 1, 1, 18, 0)
    assert interests.should_refresh_now(now) is False

    now = datetime(2024, 1, 3, 18, 0)
    assert interests.should_refresh_now(now) is True


def test_get_role_for_thread(sample_interests_data):
    interests.update(sample_interests_data, datetime.now())

    assert interests.get_role_for_thread(1417459492093693952) == 1420401262658060328
    assert interests.get_role_for_thread(1421134766488420368) == 1085220896005963778
    assert interests.get_role_for_thread(99999) is None


@pytest.mark.asyncio
async def test_try_notify_role_async_success():
    role_id = 12345

    result = await interests.try_notify_role_async(role_id)
    assert result is True

    result = await interests.try_notify_role_async(role_id)
    assert result is False


@pytest.mark.asyncio
async def test_report_api_error():
    mock_bot = MagicMock()
    mock_channel = MagicMock(spec=discord.TextChannel)
    mock_channel.send = MagicMock(return_value=None)
    mock_bot.get_channel.return_value = mock_channel

    await report_api_error(mock_bot, "Test error message")

    mock_channel.send.assert_called_once()
    call_args = mock_channel.send.call_args[0][0]
    assert "Test error message" in call_args
    assert "Interests API Error" in call_args


@pytest.mark.asyncio
async def test_report_api_error_channel_not_found():
    mock_bot = MagicMock()
    mock_bot.get_channel.return_value = None

    await report_api_error(mock_bot, "Test error message")
