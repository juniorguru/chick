from dis import disco
import os
import asyncio
from datetime import datetime
import logging

import discord
from discord.ext import commands


DAYS = ["Pondělní", "Úterní", "Středeční",
        "Čtvrteční", "Páteční", "Sobotní", "Nedělní"]

GUILD_ID = int(os.getenv('GUILD_ID', '769966886598737931'))

GREETER_ROLE_ID = 1062755787153358879

INTRO_THREAD_NAME_TEMPLATE = "Ahoj {author}!"


logger = logging.getLogger("chick.bot")


bot = commands.Bot(intents=discord.Intents(guilds=True,
                                           members=True,
                                           messages=True,
                                           message_content=True))


@bot.event
async def on_ready():
    if bot.user:
        logger.info(f"Logged into Discord as {bot.user.name}#{bot.user.discriminator}")


@bot.event
async def on_message(message: discord.Message) -> None:
    if message.guild and message.guild.id != GUILD_ID:
        logger.error(f"Message not in an allowed guild! #{message.guild.id}")
        return

    logger.info("Processing message")
    if message.author == bot.user:
        logger.info("Message sent by the bot itself, skipping")
        return
    if message.guild is None:
        logger.info("Message sent to DMs, skipping")
        return
    if is_thread_created(message) or message.is_system():
        logger.info("System message, skipping")
        return

    channel_name = message.channel.name  # type: ignore
    logger.info(f"Message sent to {channel_name!r}")

    if channel_name == "ahoj":
        await create_thread(message, INTRO_THREAD_NAME_TEMPLATE)
    elif channel_name == "past-vedle-pasti":
        await create_thread(message, "{weekday} past na {author}")
    elif channel_name == "můj-dnešní-objev":
        await create_thread(message, "{weekday} objev od {author}")


@bot.event
async def on_thread_create(thread: discord.Thread) -> None:
    if thread.guild.id != GUILD_ID:
        logger.error(f"Thread not in an allowed guild! Guild ID: #{thread.guild.id}")
        return

    if not thread.parent:
        logger.warning(f"Thread {thread.name!r} has no parent, skipping")
        return

    channel_name = thread.parent.name
    logger.info(f"Thread created in {channel_name!r}")

    starting_message = await fetch_starting_message(thread)
    if not starting_message:
        logger.warning(f"Thread {thread.name!r} has no starting message, skipping")
        return

    if channel_name == "ahoj":
        emojis = choose_intro_emojis(starting_message.content)
        logger.info(f"Processing thread {thread.name!r} (reacting with {emojis!r} and more…)")
        tasks = [ensure_thread_name(thread, INTRO_THREAD_NAME_TEMPLATE),
                 add_members_with_role(thread, GREETER_ROLE_ID)]
        tasks.extend([starting_message.add_reaction(emoji) for emoji in emojis])
        await asyncio.gather(*tasks)
    elif channel_name == "práce-inzeráty":
        logger.info(f"Processing thread {thread.name!r} (reacting with ĎK)")
        await starting_message.add_reaction("<:dk:842727526736068609>")
    elif channel_name == "práce-hledám":
        logger.info(f"Processing thread {thread.name!r} (reacting with 👍)")
        await starting_message.add_reaction("👍")


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


def choose_intro_emojis(message_content: str) -> list[str]:
    """Returns a list of emoji reactions suitable for given message"""
    # TODO https://github.com/juniorguru/juniorguru-chick/issues/14
    return ["👋", "🐣", "👍"]
