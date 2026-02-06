import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from aiohttp import web

from jg.chick.api import (
    CheckStatus,
    extract_actions_url,
    find_summary_comment,
    parse_eggtray_url,
    parse_summary_json,
    routes,
)


@pytest_asyncio.fixture
async def cli(aiohttp_client):
    """Create a test client for the API."""
    app = web.Application()
    app["github_api_key"] = "test-key"
    app["eggtray_url"] = "https://github.com/juniorguru/eggtray"
    app["debug"] = False
    app.add_routes(routes)
    return await aiohttp_client(app)


def load_fixture(filename: str) -> dict:
    """Load a JSON fixture file."""
    fixture_path = Path(__file__).parent / "fixtures" / filename
    with open(fixture_path) as f:
        return json.load(f)


# Helper function tests


def test_parse_eggtray_url():
    """Test parsing GitHub repository URLs."""
    assert parse_eggtray_url("https://github.com/owner/repo") == ("owner", "repo")
    assert parse_eggtray_url("https://github.com/owner/repo/") == ("owner", "repo")
    assert parse_eggtray_url("https://github.com/owner/repo/issues") == (
        "owner",
        "repo",
    )
    assert parse_eggtray_url("http://github.com/owner/repo") == ("owner", "repo")


def test_parse_eggtray_url_invalid():
    """Test invalid URL raises ValueError."""
    with pytest.raises(ValueError):
        parse_eggtray_url("not-a-url")
    with pytest.raises(ValueError):
        parse_eggtray_url("https://gitlab.com/owner/repo")
    with pytest.raises(ValueError):
        parse_eggtray_url("https://github.com/owner")


def test_find_summary_comment():
    """Test finding summary comment with JSON block."""
    fixture = load_fixture("eggtray_comment_bashynx.json")

    comment1 = MagicMock()
    comment1.body = "Just a regular comment"

    comment2 = MagicMock()
    comment2.body = fixture["comment_body"]

    comments = [comment1, comment2]

    result = find_summary_comment(comments)
    assert result == fixture["comment_body"]
    assert "```json" in result


def test_find_summary_comment_not_found():
    """Test when no summary comment exists."""
    comment = MagicMock()
    comment.body = "Just a comment without JSON"

    result = find_summary_comment([comment])
    assert result is None


def test_parse_summary_json():
    """Test parsing JSON from comment body using real fixture."""
    fixture = load_fixture("eggtray_comment_bashynx.json")
    comment_body = fixture["comment_body"]

    result = parse_summary_json(comment_body)

    assert result is not None
    assert result["username"] == "bashynx"
    assert "outcomes" in result
    assert result["error"] is None


def test_parse_summary_json_no_json():
    """Test parsing when no JSON block exists."""
    result = parse_summary_json("Comment without JSON")
    assert result is None


def test_extract_actions_url():
    """Test extracting GitHub Actions URL from comment."""
    fixture = load_fixture("eggtray_comment_bashynx.json")
    comment_body = fixture["comment_body"]

    result = extract_actions_url(comment_body)
    assert result == "https://github.com/juniorguru/eggtray/actions/runs/21718685108"


def test_extract_actions_url_not_found():
    """Test when no actions URL exists."""
    result = extract_actions_url("Comment without actions URL")
    assert result is None


# API endpoint tests


@pytest.mark.asyncio
async def test_create_check_success(cli):
    """Test successful creation of a check."""
    with patch("jg.chick.api.GitHub") as mock_github_class:
        mock_client = MagicMock()
        mock_github_class.return_value = mock_client

        mock_issue_data = MagicMock()
        mock_issue_data.html_url = "https://github.com/juniorguru/eggtray/issues/123"
        mock_issue_data.number = 123

        mock_response = MagicMock()
        mock_response.parsed_data = mock_issue_data

        mock_client.rest.issues.create.return_value = mock_response

        resp = await cli.post("/checks/testuser")

        assert resp.status == 200
        data = await resp.json()
        assert data["url"] == "https://github.com/juniorguru/eggtray/issues/123"
        assert data["number"] == 123

        mock_client.rest.issues.create.assert_called_once()
        call_kwargs = mock_client.rest.issues.create.call_args.kwargs
        assert call_kwargs["owner"] == "juniorguru"
        assert call_kwargs["repo"] == "eggtray"
        assert "testuser" in call_kwargs["title"]
        assert "testuser" in call_kwargs["body"]
        assert call_kwargs["labels"] == ["check"]


@pytest.mark.asyncio
async def test_get_check_status_not_found(cli):
    """Test getting status of non-existent check."""
    with patch("jg.chick.api.GitHub") as mock_github_class:
        mock_client = MagicMock()
        mock_github_class.return_value = mock_client

        from githubkit.exception import RequestFailed

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_client.rest.issues.get.side_effect = RequestFailed(mock_response)

        resp = await cli.get("/checks/999")
        assert resp.status == 404
        data = await resp.json()
        assert "not found" in data["error"].lower()


@pytest.mark.asyncio
async def test_get_check_status_pending(cli):
    """Test getting status of pending check."""
    with patch("jg.chick.api.GitHub") as mock_github_class:
        mock_client = MagicMock()
        mock_github_class.return_value = mock_client

        mock_issue_data = MagicMock()
        mock_issue_data.state = "open"

        mock_issue_response = MagicMock()
        mock_issue_response.parsed_data = mock_issue_data
        mock_client.rest.issues.get.return_value = mock_issue_response

        mock_comment = MagicMock()
        mock_comment.body = "Just a regular comment"

        mock_comments_response = MagicMock()
        mock_comments_response.parsed_data = [mock_comment]
        mock_client.rest.issues.list_comments.return_value = mock_comments_response

        resp = await cli.get("/checks/123")
        assert resp.status == 202
        data = await resp.json()
        assert data["status"] == CheckStatus.PENDING


@pytest.mark.asyncio
async def test_get_check_status_complete_with_fixture(cli):
    """Test getting status of completed check using real-world fixture."""
    fixture = load_fixture("eggtray_comment_bashynx.json")

    with patch("jg.chick.api.GitHub") as mock_github_class:
        mock_client = MagicMock()
        mock_github_class.return_value = mock_client

        mock_issue_data = MagicMock()
        mock_issue_data.state = "closed"

        mock_issue_response = MagicMock()
        mock_issue_response.parsed_data = mock_issue_data
        mock_client.rest.issues.get.return_value = mock_issue_response

        mock_summary_comment = MagicMock()
        mock_summary_comment.body = fixture["comment_body"]

        mock_comments_response = MagicMock()
        mock_comments_response.parsed_data = [mock_summary_comment]
        mock_client.rest.issues.list_comments.return_value = mock_comments_response

        resp = await cli.get("/checks/123")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == CheckStatus.COMPLETE
        assert "data" in data
        assert data["data"]["username"] == "bashynx"
        assert (
            data["actions_url"]
            == "https://github.com/juniorguru/eggtray/actions/runs/21718685108"
        )


@pytest.mark.asyncio
async def test_get_check_status_invalid_number(cli):
    """Test getting status with invalid issue number."""
    resp = await cli.get("/checks/invalid")
    assert resp.status == 400
    data = await resp.json()
    assert "invalid" in data["error"].lower()


@pytest.mark.asyncio
async def test_create_check_with_error(cli):
    """Test error handling in check creation."""
    with patch("jg.chick.api.GitHub") as mock_github_class:
        mock_client = MagicMock()
        mock_github_class.return_value = mock_client

        mock_client.rest.issues.create.side_effect = Exception("API Error")

        resp = await cli.post("/checks/testuser")
        assert resp.status == 500
        data = await resp.json()
        assert "error" in data
        assert "debug_id" in data
