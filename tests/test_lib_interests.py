"""Tests for interests management functionality."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import discord
import pytest

from jg.chick.lib.interests import (
    NOTIFICATION_COOLDOWN,
    InterestsManager,
    build_thread_to_role_mapping,
    report_api_error,
    should_refresh,
    try_notify_role,
)


@pytest.fixture
def interests_manager():
    """Creates a fresh InterestsManager instance for each test."""
    return InterestsManager()


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


# Tests for functional core (pure functions)


def test_build_thread_to_role_mapping(sample_interests_data):
    """Test building thread-to-role mapping from interests data."""
    mapping = build_thread_to_role_mapping(sample_interests_data)

    assert len(mapping) == 3
    assert mapping[1417459492093693952] == 1420401262658060328
    assert mapping[1303022608148594808] == 1420401262658060328
    assert mapping[1421134766488420368] == 1085220896005963778


def test_build_thread_to_role_mapping_empty():
    """Test building mapping from empty data."""
    mapping = build_thread_to_role_mapping([])
    assert len(mapping) == 0


def test_should_refresh_never_fetched():
    """Test should_refresh returns True when never fetched."""
    now = datetime.now()
    assert should_refresh(None, now) is True


def test_should_refresh_recently_fetched():
    """Test should_refresh returns False when recently fetched."""
    now = datetime.now()
    last_fetch = now - timedelta(hours=12)
    assert should_refresh(last_fetch, now) is False


def test_should_refresh_old_fetch():
    """Test should_refresh returns True when fetch is old."""
    now = datetime.now()
    last_fetch = now - timedelta(days=2)
    assert should_refresh(last_fetch, now) is True


def test_try_notify_role_never_notified():
    """Test try_notify_role returns True for a role that was never notified."""
    last_notifications = {}
    now = datetime.now()

    can_notify, updated = try_notify_role(12345, last_notifications, now)

    assert can_notify is True
    assert 12345 in updated
    assert updated[12345] == now
    # Original dict should not be modified
    assert 12345 not in last_notifications


def test_try_notify_role_recently_notified():
    """Test try_notify_role returns False for a recently notified role."""
    now = datetime.now()
    last_notifications = {12345: now - timedelta(hours=12)}

    can_notify, updated = try_notify_role(12345, last_notifications, now)

    assert can_notify is False
    # Dict should not be modified
    assert updated == last_notifications


def test_try_notify_role_cooldown_expired():
    """Test try_notify_role returns True when cooldown has expired."""
    now = datetime.now()
    old_time = now - NOTIFICATION_COOLDOWN - timedelta(seconds=1)
    last_notifications = {12345: old_time}

    can_notify, updated = try_notify_role(12345, last_notifications, now)

    assert can_notify is True
    assert updated[12345] == now
    assert updated[12345] != old_time


# Tests for InterestsManager (imperative shell with state)


def test_update_interests(interests_manager, sample_interests_data):
    """Test updating interests data."""
    now = datetime.now()
    interests_manager.update_interests(sample_interests_data, now)

    assert len(interests_manager.interests) == 3
    assert interests_manager.last_fetch == now
    assert (
        interests_manager.get_role_for_thread(1417459492093693952)
        == 1420401262658060328
    )


def test_should_refresh_now_never_fetched(interests_manager):
    """Test should_refresh_now returns True when never fetched."""
    assert interests_manager.should_refresh_now() is True


def test_should_refresh_now_recently_fetched(interests_manager, sample_interests_data):
    """Test should_refresh_now returns False when recently fetched."""
    interests_manager.update_interests(sample_interests_data, datetime.now())
    assert interests_manager.should_refresh_now() is False


def test_should_refresh_now_old_fetch(interests_manager, sample_interests_data):
    """Test should_refresh_now returns True when fetch is old."""
    old_time = datetime.now() - timedelta(days=2)
    interests_manager.update_interests(sample_interests_data, old_time)
    assert interests_manager.should_refresh_now() is True


def test_get_role_for_thread(interests_manager, sample_interests_data):
    """Test getting role ID for a thread."""
    interests_manager.update_interests(sample_interests_data, datetime.now())

    assert (
        interests_manager.get_role_for_thread(1417459492093693952)
        == 1420401262658060328
    )
    assert (
        interests_manager.get_role_for_thread(1421134766488420368)
        == 1085220896005963778
    )
    assert interests_manager.get_role_for_thread(99999) is None


@pytest.mark.asyncio
async def test_try_notify_role_async_success(interests_manager):
    """Test atomic notification check and mark."""
    role_id = 12345

    # First notification should succeed
    result = await interests_manager.try_notify_role_async(role_id)
    assert result is True

    # Second immediate notification should fail (cooldown)
    result = await interests_manager.try_notify_role_async(role_id)
    assert result is False


@pytest.mark.asyncio
async def test_report_api_error():
    """Test reporting API errors to the error channel."""
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
    """Test reporting API errors when error channel is not found."""
    mock_bot = MagicMock()
    mock_bot.get_channel.return_value = None

    # Should not raise an exception
    await report_api_error(mock_bot, "Test error message")
