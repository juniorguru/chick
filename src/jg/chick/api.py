import hashlib
import json
import logging
import re
from datetime import UTC, datetime
from enum import StrEnum

from aiohttp.web import Application, Request, Response, RouteTableDef, json_response
from githubkit import GitHub
from githubkit.exception import RequestFailed


LAUNCH_AT = datetime.now(UTC)


logger = logging.getLogger("jg.chick.api")


class CheckStatus(StrEnum):
    PENDING = "pending"
    COMPLETE = "complete"


web = Application()
routes = RouteTableDef()


def parse_eggtray_url(url: str) -> tuple[str, str]:
    """Parse eggtray URL to extract owner and repo.

    Args:
        url: GitHub repository URL (e.g., https://github.com/owner/repo)

    Returns:
        tuple of (owner, repo)

    Raises:
        ValueError: if URL format is invalid
    """
    # Remove trailing slash
    url = url.rstrip("/")

    # Match github.com URLs with owner/repo pattern
    match = re.match(r"https?://github\.com/([^/]+)/([^/]+)(?:/.*)?$", url)
    if not match:
        raise ValueError(f"Invalid GitHub repository URL: {url}")

    owner, repo = match.groups()
    return owner, repo


def find_summary_comment(comments: list) -> str | None:
    """Find the last comment containing JSON summary data.

    Args:
        comments: List of comment objects from GitHub API

    Returns:
        Comment body string if found, None otherwise
    """
    for comment in reversed(comments):
        comment_body = comment.body or ""
        if "```json" in comment_body:
            return comment_body
    return None


def parse_summary_json(comment_body: str) -> dict | None:
    """Extract and parse JSON data from a comment body.

    Args:
        comment_body: The full comment text containing JSON code block

    Returns:
        Parsed JSON dict if successful, None otherwise
    """
    if json_match := re.search(r"```json\s*\n(.*?)\n```", comment_body, re.DOTALL):
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from comment: {e}")
    return None


def extract_actions_url(comment_body: str) -> str | None:
    """Extract GitHub Actions run URL from comment body.

    Args:
        comment_body: The full comment text

    Returns:
        Actions URL if found, None otherwise
    """
    if actions_match := re.search(
        r"https://github\.com/juniorguru/eggtray/actions/runs/(\d+)",
        comment_body,
    ):
        return actions_match.group(0)
    return None


def generate_error_hash(error: Exception) -> str:
    """Generate a unique hash for an error for tracking purposes."""
    error_string = (
        f"{datetime.now(UTC).isoformat()}-{type(error).__name__}-{str(error)}"
    )
    return hashlib.sha256(error_string.encode()).hexdigest()[:8]


@routes.get("/")
async def index(request: Request) -> Response:
    logger.info(f"Received {request!r}")
    return json_response(
        {
            "status": "OK",
            "launch_at": LAUNCH_AT.isoformat(),
            "uptime_sec": (datetime.now(UTC) - LAUNCH_AT).total_seconds(),
        }
    )


@routes.post("/checks/{github_username}")
async def create_check(request: Request) -> Response:
    """Create a new GitHub issue for profile review."""
    github_username = request.match_info["github_username"]
    logger.info(f"Creating check for GitHub username: {github_username}")

    github_api_key = request.app["github_api_key"]
    eggtray_url = request.app["eggtray_url"]
    debug = request.app["debug"]

    try:
        eggtray_owner, eggtray_repo = parse_eggtray_url(eggtray_url)
        github = GitHub(github_api_key) if github_api_key else GitHub()

        title = f"Zpětná vazba na profil @{github_username}"
        body = f"Z webu junior.guru přišel požadavek na zpětnou vazbu k profilu @{github_username}."

        logger.debug(f"Creating issue in {eggtray_owner}/{eggtray_repo}")
        issue = github.rest.issues.create(
            owner=eggtray_owner,
            repo=eggtray_repo,
            title=title,
            body=body,
            labels=["check"],
        )

        issue_data = issue.parsed_data
        logger.info(f"Created issue #{issue_data.number}: {issue_data.html_url}")

        return json_response(
            {
                "url": issue_data.html_url,
                "number": issue_data.number,
            }
        )

    except Exception as e:
        error_hash = generate_error_hash(e)
        logger.error(f"Error creating check [{error_hash}]: {e}")
        if debug:
            raise
        return json_response(
            {"error": "Internal server error", "debug_id": error_hash},
            status=500,
        )


@routes.get("/checks/{issue_number}")
async def get_check_status(request: Request) -> Response:
    """Get the status of a profile review check."""
    try:
        issue_number = int(request.match_info["issue_number"])
    except ValueError:
        return json_response(
            {"error": "Invalid issue number"},
            status=400,
        )

    logger.info(f"Getting check status for issue #{issue_number}")

    github_api_key = request.app["github_api_key"]
    eggtray_url = request.app["eggtray_url"]
    debug = request.app["debug"]

    try:
        eggtray_owner, eggtray_repo = parse_eggtray_url(eggtray_url)
        github = GitHub(github_api_key) if github_api_key else GitHub()

        logger.info(
            f"Fetching issue #{issue_number} from {eggtray_owner}/{eggtray_repo}"
        )
        try:
            issue = github.rest.issues.get(
                owner=eggtray_owner,
                repo=eggtray_repo,
                issue_number=issue_number,
            )
        except RequestFailed as e:
            if e.response.status_code == 404:
                logger.info(f"Issue #{issue_number} not found")
                return json_response(
                    {"error": "Issue not found"},
                    status=404,
                )
            raise

        issue_data = issue.parsed_data
        logger.info(
            f"Getting comments of issue #{issue_number} ({issue_data.state}) to check for summary"
        )

        comments = github.rest.issues.list_comments(
            owner=eggtray_owner,
            repo=eggtray_repo,
            issue_number=issue_number,
        )

        if comment_body := find_summary_comment(comments.parsed_data):
            logger.info(f"Check #{issue_number} is complete, parsing summary data")

            response_data = {"status": CheckStatus.COMPLETE}

            if summary_data := parse_summary_json(comment_body):
                response_data["data"] = summary_data

            if actions_url := extract_actions_url(comment_body):
                response_data["actions_url"] = actions_url

            return json_response(response_data, status=200)
        else:
            logger.info(
                f"Check #{issue_number} is still in progress (no summary found)"
            )
            return json_response(
                {"status": CheckStatus.PENDING},
                status=202,
            )

    except Exception as e:
        error_hash = generate_error_hash(e)
        logger.error(f"Error getting check status [{error_hash}]: {e}")
        if debug:
            raise
        return json_response(
            {"error": "Internal server error", "debug_id": error_hash},
            status=500,
        )


web.add_routes(routes)
