"""Tests for interests management functionality."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from jg.chick.lib.interests import (
    NOTIFICATION_COOLDOWN,
    InterestsManager,
    report_api_error,
)


@pytest.fixture
def interests_manager():
    """Creates a fresh InterestsManager instance for each test."""
    return InterestsManager()


@pytest.fixture
def sample_interests_data():
    """Sample interests data as returned from the API."""
    return [
        {
            "role_id": 1420401262658060328,
            "guild_id": 769966886598737931,
            "channel_id": 1417459492093693952,
        },
        {
            "role_id": 1420401262658060328,
            "guild_id": 769966886598737931,
            "channel_id": 1303022608148594808,
        },
        {
            "role_id": 1085220896005963778,
            "guild_id": 769966886598737931,
            "channel_id": 1421134766488420368,
        },
    ]


@pytest.mark.asyncio
async def test_fetch_interests_success(interests_manager, sample_interests_data):
    """Test successful fetch of interests data."""
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=sample_interests_data)
        mock_get.return_value.__aenter__.return_value = mock_response

        result = await interests_manager.fetch_interests()

        assert result is True
        assert len(interests_manager.interests) == 3
        assert interests_manager.last_fetch is not None
        assert (
            interests_manager.thread_to_role[1417459492093693952] == 1420401262658060328
        )
        assert (
            interests_manager.thread_to_role[1303022608148594808] == 1420401262658060328
        )
        assert (
            interests_manager.thread_to_role[1421134766488420368] == 1085220896005963778
        )


@pytest.mark.asyncio
async def test_fetch_interests_http_error(interests_manager):
    """Test handling of HTTP errors when fetching interests."""
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_get.return_value.__aenter__.return_value = mock_response

        result = await interests_manager.fetch_interests()

        assert result is False
        assert len(interests_manager.interests) == 0
        assert interests_manager.last_fetch is None


@pytest.mark.asyncio
async def test_fetch_interests_exception(interests_manager):
    """Test handling of exceptions when fetching interests."""
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.side_effect = Exception("Network error")

        result = await interests_manager.fetch_interests()

        assert result is False
        assert len(interests_manager.interests) == 0


def test_should_refresh_never_fetched(interests_manager):
    """Test should_refresh returns True when never fetched."""
    assert interests_manager.should_refresh() is True


def test_should_refresh_recently_fetched(interests_manager):
    """Test should_refresh returns False when recently fetched."""
    interests_manager.last_fetch = datetime.now()
    assert interests_manager.should_refresh() is False


def test_should_refresh_old_fetch(interests_manager):
    """Test should_refresh returns True when fetch is old."""
    interests_manager.last_fetch = datetime.now() - timedelta(days=2)
    assert interests_manager.should_refresh() is True


def test_can_notify_role_never_notified(interests_manager):
    """Test can_notify_role returns True for a role that was never notified."""
    assert interests_manager.can_notify_role(12345) is True


def test_can_notify_role_recently_notified(interests_manager):
    """Test can_notify_role returns False for a recently notified role."""
    role_id = 12345
    interests_manager.last_notification[role_id] = datetime.now()
    assert interests_manager.can_notify_role(role_id) is False


def test_can_notify_role_cooldown_expired(interests_manager):
    """Test can_notify_role returns True when cooldown has expired."""
    role_id = 12345
    interests_manager.last_notification[role_id] = (
        datetime.now() - NOTIFICATION_COOLDOWN - timedelta(seconds=1)
    )
    assert interests_manager.can_notify_role(role_id) is True


def test_mark_role_notified(interests_manager):
    """Test marking a role as notified."""
    role_id = 12345
    before = datetime.now()
    interests_manager.mark_role_notified(role_id)
    after = datetime.now()

    assert role_id in interests_manager.last_notification
    assert before <= interests_manager.last_notification[role_id] <= after


def test_get_role_for_thread(interests_manager, sample_interests_data):
    """Test getting role ID for a thread."""
    interests_manager.interests = sample_interests_data
    interests_manager._rebuild_mappings()

    assert (
        interests_manager.get_role_for_thread(1417459492093693952)
        == 1420401262658060328
    )
    assert (
        interests_manager.get_role_for_thread(1421134766488420368)
        == 1085220896005963778
    )
    assert interests_manager.get_role_for_thread(99999) is None


def test_is_tracking_thread(interests_manager, sample_interests_data):
    """Test checking if a thread is being tracked."""
    interests_manager.interests = sample_interests_data
    interests_manager._rebuild_mappings()

    assert interests_manager.is_tracking_thread(1417459492093693952) is True
    assert interests_manager.is_tracking_thread(99999) is False


@pytest.mark.asyncio
async def test_report_api_error():
    """Test reporting API errors to the error channel."""
    mock_bot = MagicMock()
    mock_channel = AsyncMock(spec=discord.TextChannel)
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
