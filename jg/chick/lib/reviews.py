import os
import re
from typing import Any, Generator
from urllib.parse import quote, unquote

from discord import Attachment, Color, Embed, ForumTag, Thread
from jg.hen.models import Status, Summary


MAINTAINER_ID = 668226181769986078

REVIEWER_ROLE_ID = 1075044541796716604

GITHUB_API_KEY = os.getenv("GITHUB_API_KEY") or None

GITHUB_URL_RE = re.compile(r"github\.com/(?P<username>[\w-]+)")

LINKEDIN_URL_RE = re.compile(r"linkedin\.com/in/(?P<username>[^\s\/]+)")

COLORS = {
    Status.ERROR: Color.red(),
    Status.WARNING: Color.orange(),
    Status.INFO: Color.blue(),
    Status.DONE: Color.green(),
}


def find_cv_url(attachments: list[Attachment]) -> str | None:
    for attachment in attachments:
        if attachment.content_type == "application/pdf":
            return attachment.url
    return None


def find_github_url(text: str) -> str | None:
    if match := GITHUB_URL_RE.search(text):
        username = match.group("username")
        return f"https://github.com/{username}/"
    return None


def find_linkedin_url(text: str) -> str | None:
    if match := LINKEDIN_URL_RE.search(text):
        username = quote(unquote(match.group("username")))
        return f"https://www.linkedin.com/in/{username}/"
    return ""


def prepare_tags(
    thread: Thread,
    cv: bool = False,
    github: bool = False,
    linkedin: bool = False,
) -> list[ForumTag]:
    available_tags = {tag.name: tag for tag in thread.parent.available_tags}
    applied_tags = set(thread.applied_tags)
    if cv:
        applied_tags.add(available_tags.pop("zpětná vazba na CV"))
    if github:
        applied_tags.add(available_tags.pop("zpětná vazba na GH"))
    if linkedin:
        applied_tags.add(available_tags.pop("zpětná vazba na LI"))
    return list(applied_tags)


def format_summary(summary: Summary) -> Generator[dict[str, Any], None, None]:
    if summary.error:
        yield dict(
            content=(
                f"🔬 Kouklo jsem na ten GitHub, ale bohužel to skončilo chybou 🤕\n"
                f"```\n{summary.error}\n```\n"
                f"<@{MAINTAINER_ID}>, mrkni na to, prosím."
            ),
            suppress=True,
        )
    else:
        yield dict(content="🔬 Tak jsem kouklo na ten GitHub.")
        for outcome in summary.outcomes:
            embed = Embed(
                color=COLORS[outcome.status],
                description=f"{outcome.message}\n\nℹ️ [Vysvětlení]({outcome.docs_url})",
            )
            yield dict(embed=embed)
