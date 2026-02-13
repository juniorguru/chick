from pathlib import Path
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from aiohttp import web
from githubkit.exception import RequestFailed

from jg.chick.api import (
    CheckStatus,
    extract_actions_url,
    find_summary_comment,
    parse_eggtray_url,
    parse_summary_json,
    routes,
)


@pytest_asyncio.fixture
async def api(aiohttp_client):
    app = web.Application()
    app["github_client"] = MagicMock()
    app["eggtray_url"] = "https://github.com/juniorguru/eggtray"
    app["debug"] = False
    app.add_routes(routes)
    return await aiohttp_client(app)


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://github.com/owner/repo", ("owner", "repo")),
        ("https://github.com/owner/repo/", ("owner", "repo")),
        ("https://github.com/owner/repo/issues", ("owner", "repo")),
        ("http://github.com/owner/repo", ("owner", "repo")),
    ],
)
def test_parse_eggtray_url(url, expected):
    assert parse_eggtray_url(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "not-a-url",
        "https://gitlab.com/owner/repo",
        "https://github.com/owner",
    ],
)
def test_parse_eggtray_url_invalid(url):
    with pytest.raises(ValueError):
        parse_eggtray_url(url)


def test_find_summary_comment():
    fixture_content = Path(__file__).parent / "fixtures" / "eggtray_comment.md"
    comment1 = MagicMock(body="Just a regular comment")
    comment2 = MagicMock(body=fixture_content.read_text())

    result = find_summary_comment([comment1, comment2])

    assert result == fixture_content.read_text()
    assert "```json" in result


def test_find_summary_comment_not_found():
    comment = MagicMock(body="Just a comment without JSON")

    result = find_summary_comment([comment])

    assert result is None


def test_parse_summary_json():
    fixture_content = Path(__file__).parent / "fixtures" / "eggtray_comment.md"
    comment_body = fixture_content.read_text()

    result = parse_summary_json(comment_body)

    assert result["username"] == "bashynx"


def test_parse_summary_json_no_json():
    result = parse_summary_json("Comment without JSON")

    assert result is None


def test_parse_summary_json_invalid_json():
    comment_body = "```json\n{invalid json}\n```"

    with pytest.raises(Exception):
        parse_summary_json(comment_body)


def test_extract_actions_url():
    fixture_content = Path(__file__).parent / "fixtures" / "eggtray_comment.md"
    comment_body = fixture_content.read_text()

    result = extract_actions_url(comment_body)

    assert result == "https://github.com/juniorguru/eggtray/actions/runs/21718685108"


def test_extract_actions_url_not_found():
    result = extract_actions_url("Comment without actions URL")

    assert result is None


@pytest.mark.asyncio
async def test_create_check_success(api):
    github_client = api.app["github_client"]
    issue_data = MagicMock(
        html_url="https://github.com/juniorguru/eggtray/issues/123", number=123
    )
    github_client.rest.issues.create.return_value = MagicMock(parsed_data=issue_data)

    resp = await api.post("/checks/testuser")
    data = await resp.json()

    assert resp.status == 200
    assert data == {
        "url": "https://github.com/juniorguru/eggtray/issues/123",
        "number": 123,
    }

    call_kwargs = github_client.rest.issues.create.call_args.kwargs
    assert call_kwargs["owner"] == "juniorguru"
    assert call_kwargs["repo"] == "eggtray"
    assert "testuser" in call_kwargs["title"]
    assert "testuser" in call_kwargs["body"]
    assert call_kwargs["labels"] == ["check"]


@pytest.mark.asyncio
async def test_get_check_status_not_found(api):
    github_client = api.app["github_client"]
    github_client.rest.issues.get.side_effect = RequestFailed(
        MagicMock(status_code=404)
    )

    resp = await api.get("/checks/999")
    data = await resp.json()

    assert resp.status == 404
    assert "not found" in data["error"].lower()


@pytest.mark.asyncio
async def test_get_check_status_pending(api):
    github_client = api.app["github_client"]
    issue_data = MagicMock(state="open")
    github_client.rest.issues.get.return_value = MagicMock(parsed_data=issue_data)
    github_client.rest.issues.list_comments.return_value = MagicMock(
        parsed_data=[MagicMock(body="Just a regular comment")]
    )

    resp = await api.get("/checks/123")
    data = await resp.json()

    assert resp.status == 202
    assert data == {"status": CheckStatus.PENDING}


@pytest.mark.asyncio
async def test_get_check_status_complete_with_fixture(api):
    fixture_content = Path(__file__).parent / "fixtures" / "eggtray_comment.md"
    github_client = api.app["github_client"]
    issue_data = MagicMock(state="closed")
    github_client.rest.issues.get.return_value = MagicMock(parsed_data=issue_data)
    github_client.rest.issues.list_comments.return_value = MagicMock(
        parsed_data=[MagicMock(body=fixture_content.read_text())]
    )

    resp = await api.get("/checks/123")
    data = await resp.json()

    assert resp.status == 200
    assert data["status"] == CheckStatus.COMPLETE
    assert data["data"]["username"] == "bashynx"
    assert (
        data["actions_url"]
        == "https://github.com/juniorguru/eggtray/actions/runs/21718685108"
    )


@pytest.mark.asyncio
async def test_get_check_status_invalid_number(api):
    resp = await api.get("/checks/invalid")
    data = await resp.json()

    assert resp.status == 400
    assert "invalid" in data["error"].lower()


@pytest.mark.asyncio
async def test_create_check_with_error(api):
    github_client = api.app["github_client"]
    github_client.rest.issues.create.side_effect = Exception("API Error")

    resp = await api.post("/checks/testuser")
    data = await resp.json()

    assert resp.status == 500
    assert "error" in data
    assert "debug_id" in data
