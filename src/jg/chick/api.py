import logging
import os

from aiohttp.web import Request, Response, RouteTableDef, json_response
from githubkit import GitHub
from githubkit.exception import RequestFailed


GITHUB_API_KEY = os.getenv("GITHUB_API_KEY") or None
DEBUG = os.getenv("DEBUG", "").lower() in ("1", "true", "yes")

EGGTRAY_OWNER = "juniorguru"
EGGTRAY_REPO = "eggtray"

logger = logging.getLogger("jg.chick.api")

routes = RouteTableDef()


def get_github_client() -> GitHub:
    """Create and return a GitHub client instance."""
    if GITHUB_API_KEY:
        return GitHub(GITHUB_API_KEY)
    return GitHub()


@routes.post("/checks/{github_username}")
async def create_check(request: Request) -> Response:
    """Create a new GitHub issue for profile review."""
    github_username = request.match_info["github_username"]
    logger.info(f"Creating check for GitHub username: {github_username}")

    try:
        github = get_github_client()

        # Create issue with the specified format
        title = f"Zpětná vazba na profil @{github_username}"
        body = f"Z webu junior.guru přišel požadavek na zpětnou vazbu k profilu @{github_username}."

        logger.debug(f"Creating issue in {EGGTRAY_OWNER}/{EGGTRAY_REPO}")
        issue = github.rest.issues.create(
            owner=EGGTRAY_OWNER,
            repo=EGGTRAY_REPO,
            title=title,
            body=body,
        )

        issue_data = issue.parsed_data
        logger.info(f"Created issue #{issue_data.number}: {issue_data.html_url}")

        return json_response(
            {
                "url": issue_data.html_url,
                "number": issue_data.number,
            }
        )

    except RequestFailed as e:
        logger.error(f"GitHub API error creating issue: {e}")
        if DEBUG:
            raise
        return json_response(
            {"error": "Failed to create GitHub issue"},
            status=500,
        )
    except Exception as e:
        logger.error(f"Unexpected error creating check: {e}")
        if DEBUG:
            raise
        return json_response(
            {"error": "Internal server error"},
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

    try:
        github = get_github_client()

        # Try to get the issue
        logger.debug(
            f"Fetching issue #{issue_number} from {EGGTRAY_OWNER}/{EGGTRAY_REPO}"
        )
        try:
            issue = github.rest.issues.get(
                owner=EGGTRAY_OWNER,
                repo=EGGTRAY_REPO,
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
        logger.debug(f"Issue #{issue_number} state: {issue_data.state}")

        # Get comments to check for summary
        comments = github.rest.issues.list_comments(
            owner=EGGTRAY_OWNER,
            repo=EGGTRAY_REPO,
            issue_number=issue_number,
        )

        # Find the last summary comment (from the bot)
        # Looking for comments that contain the summary table
        summary_comment = None
        for comment in reversed(comments.parsed_data):
            comment_body = comment.body or ""
            # Check if this is a summary comment (contains the table with verdicts)
            if "| Verdikt | Popis | Vysvětlení |" in comment_body:
                summary_comment = comment
                break

        if summary_comment:
            # Check is complete - return 200 with the summary data
            logger.info(f"Check #{issue_number} is complete")

            # Parse the summary comment to extract structured data
            # For now, we'll return the raw comment body
            # In the future, this could be parsed into structured JSON
            return json_response(
                {
                    "status": "complete",
                    "comment": {
                        "id": summary_comment.id,
                        "body": summary_comment.body,
                        "created_at": summary_comment.created_at.isoformat()
                        if summary_comment.created_at
                        else None,
                        "html_url": summary_comment.html_url,
                    },
                },
                status=200,
            )
        else:
            # Check is still in progress - return 202
            logger.info(f"Check #{issue_number} is still in progress")
            return json_response(
                {
                    "status": "pending",
                    "message": "Check is still in progress",
                },
                status=202,
            )

    except RequestFailed as e:
        logger.error(f"GitHub API error getting check status: {e}")
        if DEBUG:
            raise
        return json_response(
            {"error": "Failed to get check status from GitHub"},
            status=500,
        )
    except Exception as e:
        logger.error(f"Unexpected error getting check status: {e}")
        if DEBUG:
            raise
        return json_response(
            {"error": "Internal server error"},
            status=500,
        )
