import os
import re
from typing import Any, Generator
from urllib.parse import quote, unquote

from discord import Color, Embed
from jg.hen.core import ResultType, Summary


MAINTAINER_ID = 668226181769986078

REVIEWER_ROLE_ID = 1075044541796716604

GITHUB_API_KEY = os.getenv("GITHUB_API_KEY") or None

GITHUB_URL_RE = re.compile(r"github\.com/(?P<username>[\w-]+)")

LINKEDIN_URL_RE = re.compile(r"linkedin\.com/in/(?P<username>[^\s\/]+)")

COLORS = {
    ResultType.ERROR: Color.red(),
    ResultType.WARNING: Color.orange(),
    ResultType.INFO: Color.blue(),
    ResultType.DONE: Color.green(),
}


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


def format_summary(summary: Summary) -> Generator[dict[str, Any], None, None]:
    if summary.status == "error":
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
        for result in summary.results:
            embed = Embed(
                color=COLORS[result.type],
                description=f"{result.message}\nℹ️ [Vysvětlení]({result.docs_url})",
            )
            yield dict(embed=embed)
