import re
from urllib.parse import quote, unquote


REVIEWER_ROLE_ID = 1075044541796716604

GITHUB_URL_RE = re.compile(r"github\.com/(?P<username>[\w-]+)")

LINKEDIN_URL_RE = re.compile(r"linkedin\.com/in/(?P<username>[^\s\/]+)")


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
