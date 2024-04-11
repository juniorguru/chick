import re
from datetime import datetime

import discord


DAYS = ["Pondělní", "Úterní", "Středeční", "Čtvrteční", "Páteční", "Sobotní", "Nedělní"]


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
    message: discord.Message, name_template, alternative_name_template=None
) -> str | None:
    """If the message includes text in square brackets, use that as name for the thread. Otherwise, use the provided name template."""
    brackets_regex = re.compile(
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

    if (match := re.match(brackets_regex, message.content)) is not None:
        content = match.group("bracket_content")
        parts = content.split(",")
        words = []
        for part in parts:
            words.append(part.strip())
        name_from_brackets = ", ".join(words)

        name = alternative_name_template.format(
            author=message.author.display_name, name=name_from_brackets
        )
        return name

    else:
        weekday = datetime.now().weekday()
        name = name_template.format(
            weekday=DAYS[weekday], author=message.author.display_name
        )
        return name


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
    await thread.send(f"<@&{role_id}>", delete_after=0, silent=True)
