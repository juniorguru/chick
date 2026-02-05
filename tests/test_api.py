from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from aiohttp import web

from jg.chick.api import routes


@pytest_asyncio.fixture
async def cli(aiohttp_client):
    """Create a test client for the API."""
    app = web.Application()
    app.add_routes(routes)
    return await aiohttp_client(app)


@pytest.mark.asyncio
async def test_create_check_success(cli):
    """Test successful creation of a check."""
    with patch("jg.chick.api.get_github_client") as mock_github:
        # Mock GitHub client
        mock_client = MagicMock()
        mock_github.return_value = mock_client

        # Mock issue creation response
        mock_issue_data = MagicMock()
        mock_issue_data.html_url = "https://github.com/juniorguru/eggtray/issues/123"
        mock_issue_data.number = 123

        mock_response = MagicMock()
        mock_response.parsed_data = mock_issue_data

        mock_client.rest.issues.create.return_value = mock_response

        # Make request
        resp = await cli.post("/checks/testuser")

        assert resp.status == 200
        data = await resp.json()
        assert data["url"] == "https://github.com/juniorguru/eggtray/issues/123"
        assert data["number"] == 123

        # Verify GitHub API was called correctly
        mock_client.rest.issues.create.assert_called_once()
        call_kwargs = mock_client.rest.issues.create.call_args.kwargs
        assert call_kwargs["owner"] == "juniorguru"
        assert call_kwargs["repo"] == "eggtray"
        assert "testuser" in call_kwargs["title"]
        assert "testuser" in call_kwargs["body"]


@pytest.mark.asyncio
async def test_get_check_status_not_found(cli):
    """Test getting status of non-existent check."""
    with patch("jg.chick.api.get_github_client") as mock_github:
        mock_client = MagicMock()
        mock_github.return_value = mock_client

        # Mock 404 response
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
    with patch("jg.chick.api.get_github_client") as mock_github:
        mock_client = MagicMock()
        mock_github.return_value = mock_client

        # Mock issue response
        mock_issue_data = MagicMock()
        mock_issue_data.state = "open"

        mock_issue_response = MagicMock()
        mock_issue_response.parsed_data = mock_issue_data
        mock_client.rest.issues.get.return_value = mock_issue_response

        # Mock comments response (no summary comment)
        mock_comment = MagicMock()
        mock_comment.body = "Just a regular comment"

        mock_comments_response = MagicMock()
        mock_comments_response.parsed_data = [mock_comment]
        mock_client.rest.issues.list_comments.return_value = mock_comments_response

        resp = await cli.get("/checks/123")
        assert resp.status == 202
        data = await resp.json()
        assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_get_check_status_complete(cli):
    """Test getting status of completed check."""
    with patch("jg.chick.api.get_github_client") as mock_github:
        mock_client = MagicMock()
        mock_github.return_value = mock_client

        # Mock issue response
        mock_issue_data = MagicMock()
        mock_issue_data.state = "closed"

        mock_issue_response = MagicMock()
        mock_issue_response.parsed_data = mock_issue_data
        mock_client.rest.issues.get.return_value = mock_issue_response

        # Mock comments response with summary comment
        mock_summary_comment = MagicMock()
        mock_summary_comment.id = 456
        mock_summary_comment.body = (
            "Summary\n\n| Verdikt | Popis | Vysvětlení |\n|---|---|---|"
        )
        mock_summary_comment.created_at = datetime.now(UTC)
        mock_summary_comment.html_url = (
            "https://github.com/juniorguru/eggtray/issues/123#issuecomment-456"
        )

        mock_comments_response = MagicMock()
        mock_comments_response.parsed_data = [mock_summary_comment]
        mock_client.rest.issues.list_comments.return_value = mock_comments_response

        resp = await cli.get("/checks/123")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "complete"
        assert data["comment"]["id"] == 456
        assert "Verdikt" in data["comment"]["body"]


@pytest.mark.asyncio
async def test_get_check_status_invalid_number(cli):
    """Test getting status with invalid issue number."""
    resp = await cli.get("/checks/invalid")
    assert resp.status == 400
    data = await resp.json()
    assert "invalid" in data["error"].lower()
