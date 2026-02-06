import hashlib
import json
import logging
import re
from datetime import UTC, datetime
from enum import StrEnum

from aiohttp.web import Application, Request, Response, RouteTableDef, json_response
from githubkit import GitHub


LAUNCH_AT = datetime.now(UTC)


logger = logging.getLogger("jg.chick.api")


class CheckStatus(StrEnum):
    PENDING = "pending"
    COMPLETE = "complete"


web = Application()
routes = RouteTableDef()


def generate_error_hash(error: Exception) -> str:
    """Generate a unique hash for an error for tracking purposes."""
    error_string = f"{datetime.now(UTC).isoformat()}-{type(error).__name__}-{str(error)}"
    return hashlib.sha256(error_string.encode()).hexdigest()[:8]


@routes.get("/")
async def index(request: Request) -> Response:
    logger.info(f"Received {request!r}")
    return json_response(
        {
            "status": "ok",
            "launch_at": LAUNCH_AT.isoformat(),
            "uptime_sec": (datetime.now(UTC) - LAUNCH_AT).seconds,
        }
    )


@routes.post("/checks/{github_username}")
async def create_check(request: Request) -> Response:
    """Create a new GitHub issue for profile review."""
    github_username = request.match_info["github_username"]
    logger.info(f"Creating check for GitHub username: {github_username}")

    github_api_key = request.app["github_api_key"]
    eggtray_owner = request.app["eggtray_owner"]
    eggtray_repo = request.app["eggtray_repo"]
    debug = request.app["debug"]

    try:
        github = GitHub(github_api_key) if github_api_key else GitHub()

        # Create issue with the specified format
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
            {"error": "Internal server error", "hash": error_hash},
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
    eggtray_owner = request.app["eggtray_owner"]
    eggtray_repo = request.app["eggtray_repo"]
    debug = request.app["debug"]

    try:
        github = GitHub(github_api_key) if github_api_key else GitHub()

        # Try to get the issue
        logger.info(
            f"Fetching issue #{issue_number} from {eggtray_owner}/{eggtray_repo}"
        )
        try:
            issue = github.rest.issues.get(
                owner=eggtray_owner,
                repo=eggtray_repo,
                issue_number=issue_number,
            )
        except Exception as e:
            if "404" in str(e) or "Not Found" in str(e):
                logger.info(f"Issue #{issue_number} not found")
                return json_response(
                    {"error": "Issue not found"},
                    status=404,
                )
            raise

        issue_data = issue.parsed_data
        logger.debug(f"Issue #{issue_number} state: {issue_data.state}")

        # Get comments to check for summary
        comments = github.rest.issues.list_comments(
            owner=eggtray_owner,
            repo=eggtray_repo,
            issue_number=issue_number,
        )

        # Find the last summary comment (from the bot)
        # Looking for comments that contain the JSON code block
        summary_comment = None
        for comment in reversed(comments.parsed_data):
            comment_body = comment.body or ""
            # Parse the comment to find the code block with JSON
            if "```json" in comment_body:
                summary_comment = comment
                break

        if summary_comment:
            # Check is complete - return 200 with the summary data
            logger.info(f"Check #{issue_number} is complete")

            # Extract JSON from the code block
            comment_body = summary_comment.body
            json_match = re.search(
                r"```json\s*\n(.*?)\n```", comment_body, re.DOTALL
            )

            summary_data = None
            if json_match:
                try:
                    summary_data = json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    logger.warning(
                        f"Failed to parse JSON from comment {summary_comment.id}"
                    )

            # Extract GitHub Actions URL
            actions_url = None
            actions_match = re.search(
                r"https://github\.com/juniorguru/eggtray/actions/runs/(\d+)",
                comment_body,
            )
            if actions_match:
                actions_url = actions_match.group(0)

            response_data = {
                "status": CheckStatus.COMPLETE,
            }

            if summary_data:
                response_data["data"] = summary_data

            if actions_url:
                response_data["actions_url"] = actions_url

            return json_response(response_data, status=200)
        else:
            # Check is still in progress - return 202
            logger.info(f"Check #{issue_number} is still in progress")
            return json_response(
                {
                    "status": CheckStatus.PENDING,
                },
                status=202,
            )

    except Exception as e:
        error_hash = generate_error_hash(e)
        logger.error(f"Error getting check status [{error_hash}]: {e}")
        if debug:
            raise
        return json_response(
            {"error": "Internal server error", "hash": error_hash},
            status=500,
        )


web.add_routes(routes)
