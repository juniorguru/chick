"""CV, GitHub, and LinkedIn profile review functionality.

This module provides tools for reviewing and analyzing user profiles,
including CV attachments, GitHub profiles, and LinkedIn profiles.
It extracts URLs from messages, applies appropriate forum tags,
and formats review summaries for display.
"""

import re
from typing import Any, Generator
from urllib.parse import quote, unquote

from discord import Attachment, Color, Embed, ForumTag, Thread
from jg.eggtray.models import is_ready
from jg.hen.models import Status, Summary

from jg.chick.lib.config import GITHUB_API_KEY, MAINTAINER_ID, REVIEWER_ROLE_ID

GITHUB_URL_RE = re.compile(r"github\.com/(?P<username>[\w-]+)")

LINKEDIN_URL_RE = re.compile(r"linkedin\.com/in/(?P<username>[^\s\/]+)")

COLORS = {
    Status.ERROR: Color.red(),
    Status.WARNING: Color.orange(),
    Status.INFO: Color.blue(),
    Status.DONE: Color.green(),
}


def find_cv_url(attachments: list[Attachment]) -> str | None:
    """Find a CV PDF attachment URL from a list of attachments.

    Args:
        attachments: List of Discord message attachments.

    Returns:
        The URL of the first PDF attachment found, None otherwise.
    """
    for attachment in attachments:
        if attachment.content_type == "application/pdf":
            return attachment.url
    return None


def find_github_url(text: str) -> str | None:
    """Extract GitHub profile URL from text.

    Args:
        text: The text to search for GitHub URLs.

    Returns:
        The normalized GitHub profile URL if found, None otherwise.
    """
    if match := GITHUB_URL_RE.search(text):
        username = match.group("username")
        return f"https://github.com/{username}/"
    return None


def find_linkedin_url(text: str) -> str | None:
    """Extract LinkedIn profile URL from text.

    Args:
        text: The text to search for LinkedIn URLs.

    Returns:
        The normalized LinkedIn profile URL if found, None otherwise.
    """
    if match := LINKEDIN_URL_RE.search(text):
        username = quote(unquote(match.group("username")))
        return f"https://www.linkedin.com/in/{username}/"
    return None


def prepare_tags(
    thread: Thread,
    cv: bool = False,
    github: bool = False,
    linkedin: bool = False,
) -> list[ForumTag]:
    """Prepare forum tags based on the types of content found in a review thread.

    Args:
        thread: The Discord forum thread to apply tags to.
        cv: Whether a CV was found in the thread.
        github: Whether a GitHub profile was found.
        linkedin: Whether a LinkedIn profile was found.

    Returns:
        List of forum tags to apply to the thread.
    """
    available_tags = {tag.name: tag for tag in thread.parent.available_tags}
    applied_tags = set(thread.applied_tags)
    if cv:
        applied_tags.add(available_tags.pop("zpětná vazba na CV"))
    if github:
        applied_tags.add(available_tags.pop("zpětná vazba na GH"))
    if linkedin:
        applied_tags.add(available_tags.pop("zpětná vazba na LI"))
    return list(applied_tags)


def format_summary(
    summary: Summary, has_profile: bool
) -> Generator[dict[str, Any], None, None]:
    """Format a GitHub profile review summary as Discord messages.

    Args:
        summary: The review summary from the jg.hen library.
        has_profile: Whether the user already has a profile on junior.guru/candidates.

    Yields:
        Dictionary arguments for Discord thread.send() calls.
    """
    if summary.error:
        yield dict(
            content=(
                f"🔬 Kouklo jsem na ten GitHub, ale bohužel to skončilo chybou 🤕\n"
                f"```\n{summary.error}\n```\n"
                f"<@{MAINTAINER_ID}>, mrkni na to, prosím."
            ),
            suppress=True,
        )
        return

    yield dict(content="🔬 Tak jsem kouklo na ten GitHub.")
    for outcome in summary.outcomes:
        embed = Embed(
            color=COLORS[outcome.status],
            description=f"{outcome.message}\n\nℹ️ [Vysvětlení]({outcome.docs_url})",
        )
        yield dict(embed=embed)
    yield dict(content="Hotovo! ✨")
    if is_ready(summary.outcomes):
        yield dict(
            content="Nevidím žádné zásadní nedostatky! Hledej si práci v oboru! 💪"
        )
        if has_profile:
            yield dict(
                content=(
                    "Profil na [junior.guru/candidates](https://junior.guru/candidates/) už máš, výborně! 🚀"
                ),
                suppress=True,
            )
        else:
            yield dict(
                content=(
                    "Udělej Pull Request na [github.com/juniorguru/eggtray](https://github.com/juniorguru/eggtray) "
                    "a vytvoř si profil na [junior.guru/candidates](https://junior.guru/candidates/)! 🚀"
                ),
                suppress=True,
            )
    else:
        yield dict(
            content=(
                "Vidím zásadní nedostatky 🔴 Oprav si to, než si začneš hledat práci. "
                "Až uděláš změny, stačí mě označit v tomto vlákně a projedu to znova 🔬"
            ),
        )
