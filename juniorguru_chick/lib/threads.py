from datetime import datetime

import discord


DAYS = ["Pondělní", "Úterní", "Středeční",
        "Čtvrteční", "Páteční", "Sobotní", "Nedělní"]


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


async def create_thread(message: discord.Message, name_template) -> discord.Thread:
    """Creates a new thread for given message"""
    weekday = datetime.now().weekday()
    name = name_template.format(weekday=DAYS[weekday], author=message.author.display_name)
    return await message.create_thread(name=name)


async def ensure_thread_name(thread: discord.Thread, name_template) -> str | None:
    """Ensures given thread has a name"""
    starting_message = await fetch_starting_message(thread)
    if starting_message:
        weekday = datetime.now().weekday()
        name = name_template.format(weekday=DAYS[weekday], author=starting_message.author.display_name)
        if thread.name != name:
            await thread.edit(name=name)
        return name
    else:
        return None


async def add_members_with_role(thread: discord.Thread, role_id: int) -> None:
    """Adds members of given role to given thread"""
    await thread.send(f"<@&{role_id}>", delete_after=0, silent=True)
