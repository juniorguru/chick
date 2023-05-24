import os
import asyncio
import logging

import discord
from discord.ext import commands

from juniorguru_chick.lib.intro_emojis import choose_intro_emojis
from juniorguru_chick.lib.threads import is_thread_created, fetch_starting_message, create_thread, ensure_thread_name, add_members_with_role, INTRO_THREAD_NAME_TEMPLATE, GREETER_ROLE_ID


logger = logging.getLogger("chick.bot")


bot = commands.Bot(intents=discord.Intents(guilds=True,
                                           members=True,
                                           messages=True,
                                           message_content=True))


@bot.event
async def on_ready() -> None:
    for guild in bot.guilds:
        logger.info(f"Joined Discord {guild.name!r} as {guild.me.display_name!r}")


@bot.event
async def on_message(message: discord.Message) -> None:
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
    if not thread.parent:
        logger.warning(f"Thread {thread.name!r} has no parent, skipping")
        return

    channel_name = thread.parent.name
    logger.info(f"Thread {thread.name!r} created in {channel_name!r}")

    starting_message = await fetch_starting_message(thread)
    if not starting_message:
        logger.warning(f"Thread {thread.name!r} has no starting message, skipping")
        return
    is_bot = starting_message.author == bot.user

    if channel_name == "ahoj":
        await handle_intro_thread(starting_message, thread, is_bot)
    elif channel_name == "práce-inzeráty":
        await handle_job_posting_thread(starting_message, thread, is_bot)
    elif channel_name == "práce-hledám":
        await handle_candidate_thread(starting_message, thread, is_bot)


async def handle_intro_thread(starting_message: discord.Message, thread: discord.Thread, is_bot: bool) -> None:
    emojis = choose_intro_emojis(starting_message.content)
    logger.info(f"Processing thread {thread.name!r} (reacting with {emojis!r} and more…)")
    tasks = [ensure_thread_name(thread, INTRO_THREAD_NAME_TEMPLATE),
             add_members_with_role(thread, GREETER_ROLE_ID)]
    tasks.extend([starting_message.add_reaction(emoji) for emoji in emojis])
    await asyncio.gather(*tasks)


async def handle_job_posting_thread(starting_message: discord.Message, thread: discord.Thread, is_bot: bool) -> None:
    if is_bot:
        logger.info("Message sent by the bot itself, skipping")
        return
    logger.info(f"Processing thread {thread.name!r} (reacting with ĎK)")
    await starting_message.add_reaction("<:dk:842727526736068609>")


async def handle_candidate_thread(starting_message: discord.Message, thread: discord.Thread, is_bot: bool) -> None:
    if is_bot:
        logger.info("Message sent by the bot itself, skipping")
        return
    logger.info(f"Processing thread {thread.name!r} (reacting with 👍)")
    await starting_message.add_reaction("👍")
