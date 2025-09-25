import re
from datetime import datetime

import discord


DAYS = ["Pondělní", "Úterní", "Středeční", "Čtvrteční", "Páteční", "Sobotní", "Nedělní"]

BRACKETS_RE = re.compile(
    r"""
        ^
        \[     # starts with [
            (?P<bracket_content>
                .*      # any number of any characters
                [^\s]   # not a whitespace
                [^\]]   # not a closing bracket
            )
        \]     # ends with ]
    """,
    re.VERBOSE,
)


def is_thread_created(message: discord.Message) -> bool:
    """Checks if given message is a system 'thread created' announcement"""
    return message.type == discord.MessageType.thread_created


async def fetch_starting_message(thread: discord.Thread) -> discord.Message | None:
    """Returns the starting message of given thread"""
    if thread.starting_message:
        return thread.starting_message
    try:
        # thread.starting_message is often None although the thread
        # has a starting message, so try to fetch it manually
        return await thread.fetch_message(thread.id)
    except discord.errors.NotFound:
        return None


def name_thread(
    message: discord.Message,
    name_template: str,
    bracket_name_template: str | None = None,
) -> str:
    """
    If the message includes text in square brackets, use that as name for the thread.
    Otherwise, use the provided name template.
    """
    if bracket_name_template and (match := BRACKETS_RE.match(message.content)):
        content = match.group("bracket_content")
        parts = content.split(",")
        words = []
        for part in parts:
            words.append(part.strip())
        name_from_brackets = ", ".join(words)
        return bracket_name_template.format(
            author=message.author.display_name,
            bracket_content=name_from_brackets,
        )
    weekday = datetime.now().weekday()
    return name_template.format(
        weekday=DAYS[weekday],
        author=message.author.display_name,
    )


async def ensure_thread_name(thread: discord.Thread, name_template) -> str | None:
    """Ensures given thread has a name"""
    starting_message = await fetch_starting_message(thread)
    if starting_message:
        name = name_thread(starting_message, name_template)
        if thread.name != name:
            await thread.edit(name=name)
        return name
    else:
        return None


async def add_members_with_role(thread: discord.Thread, role_id: int) -> None:
    """Adds members of given role to given thread"""
    message = await thread.send(
        f"<@&{role_id}>",
        silent=True,
        allowed_mentions=discord.AllowedMentions.none(),
    )
    await message.delete()
