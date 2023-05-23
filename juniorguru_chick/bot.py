import asyncio
from datetime import datetime
import logging

import discord
from discord.ext import commands


DAYS = ["Pondělní", "Úterní", "Středeční",
        "Čtvrteční", "Páteční", "Sobotní", "Nedělní"]


logger = logging.getLogger("chick.bot")


bot = commands.Bot()


def is_thread(message: discord.Message) -> bool:
    """Checks if given message is a system 'thread created' announcement"""
    return message.type == discord.MessageType.thread_created


async def create_thread(message: discord.Message, name_template) -> None:
    """Creates a new thread for given message"""
    weekday = datetime.now().weekday()
    name = name_template.format(weekday=DAYS[weekday], author=message.author.display_name)
    await message.create_thread(name=name)


async def ensure_thread_name(thread: discord.Thread, name_template) -> None:
    """Ensures given thread has a name"""
    weekday = datetime.now().weekday()
    name = name_template.format(weekday=DAYS[weekday], author=thread.starting_message.author.display_name)
    if thread.name != name:
        await thread.edit(name=name)


@bot.event
async def on_ready():
    if bot.user:
        logger.info("Logged into Discord as {}".format(f"{bot.user.name}#{bot.user.discriminator}"))


@bot.event
async def on_message(message: discord.Message) -> None: # Message was sent
    logger.info("Processing message")

    if message.author == bot.user:
        logger.info("Message sent by the bot itself, skipping")
        return

    if message.guild is None:
        logger.info("Message sent to DMs, skipping")
        return

    if is_thread(message) or message.is_system():
        logger.info("System message, skipping")
        return

    channel_name = message.channel.name  # type: ignore
    logger.info(f"Message sent to {channel_name!r}")

    if channel_name == "ahoj":
        await create_thread(message, "Ahoj {author}!")
    elif channel_name == "past-vedle-pasti":
        await create_thread(message, "{weekday} past na {author}")
    elif channel_name == "můj-dnešní-objev":
        await create_thread(message, "{weekday} objev od {author}")


@bot.event
async def on_thread_create(thread: discord.Thread) -> None:
    if not thread.parent:
        logger.warning(f"Thread {thread.name} has no parent, skipping")
        return

    channel_name = thread.parent.name
    logger.info(f"Thread created in {channel_name!r}")

    starting_message = thread.starting_message
    if not starting_message:
        logger.info("Thread has no starting message, skipping")
        return

    if channel_name == "ahoj":
        await asyncio.gather(ensure_thread_name(thread, "Ahoj {author}!"),
                             starting_message.add_reaction("👋"),
                             starting_message.add_reaction("🐣"),
                             starting_message.add_reaction("👍"))
    elif channel_name == "práce-inzeráty":
        await starting_message.add_reaction("<:dk:842727526736068609>")
    elif channel_name == "práce-hledám":
        await starting_message.add_reaction("👍")
