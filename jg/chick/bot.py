import asyncio
import logging

import discord
from discord.ext import commands
from jg.hen.core import check_profile_url

from jg.chick.lib.intro import (
    GREETER_ROLE_ID,
    THREAD_NAME_TEMPLATE,
    choose_intro_emojis,
    generate_intro_message,
)
from jg.chick.lib.reviews import find_github_url, find_linkedin_url, REVIEWER_ROLE_ID
from jg.chick.lib.threads import (
    add_members_with_role,
    ensure_thread_name,
    fetch_starting_message,
    is_thread_created,
    name_thread,
)


logger = logging.getLogger("jg.chick.bot")


bot = commands.Bot(
    intents=discord.Intents(
        guilds=True, members=True, messages=True, message_content=True
    )
)


@bot.event
async def on_ready() -> None:
    for guild in bot.guilds:
        logger.info(f"Joined Discord {guild.name!r} as {guild.me.display_name!r}")


@bot.event
async def on_message(message: discord.Message) -> None:
    logger.info("Processing message")
    if message.author.id == bot.user.id:  # type: ignore
        logger.info("Message sent by the bot itself, skipping")
        return
    if message.guild is None:
        logger.info("DM, responding with a canned message")
        try:
            response = (
                "Píp píp píp! Jsem jen malé kuřátko, které neumí číst soukromé zprávy a odpovídat na ně. "
                "Tvou zprávu si nikdo nepřečte. Pokud se chceš na něco zeptat, zkus kanál "
                "https://discord.com/channels/769966886598737931/806215364379148348 "
                "nebo napiš do soukromé zprávy komukoliv z moderátorů. Rádi tě nasměrují."
            )
            await message.reply(response)
        except discord.errors.Forbidden:
            logger.warning("User has DMs disabled, skipping")
        return
    if is_thread_created(message) or message.is_system():
        logger.info("System message, skipping")
        return

    channel_name = message.channel.name  # type: ignore
    logger.info(f"Message sent to {channel_name!r}")

    if channel_name == "ahoj":
        await message.create_thread(
            name=name_thread(message, intro.THREAD_NAME_TEMPLATE)
        )
    elif channel_name == "past-vedle-pasti":
        await message.create_thread(
            name=name_thread(
                message, "{weekday} past na {author}", "Past na {author}: {name}"
            )
        )
    elif channel_name == "můj-dnešní-objev":
        await message.create_thread(
            name=name_thread(
                message, "{weekday} objev od {author}", "Objev od {author}: {name}"
            )
        )


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

    if starting_message.author == bot.user:
        logger.info("Thread created by the bot itself, skipping")
        return

    if channel_name == "ahoj":
        await handle_intro_thread(starting_message, thread)
    elif channel_name == "práce-inzeráty":
        await handle_job_posting_thread(starting_message, thread)
    elif channel_name == "práce-hledám":
        await handle_candidate_thread(starting_message, thread)
    elif channel_name == "cv-github-linkedin":
        await handle_review_thread(starting_message, thread)


async def handle_intro_thread(
    starting_message: discord.Message, thread: discord.Thread
) -> None:
    emojis = choose_intro_emojis(starting_message.content)
    logger.info(
        f"Processing thread {thread.name!r} (reacting with {emojis!r} and more…)"
    )
    tasks = [
        ensure_thread_name(thread, THREAD_NAME_TEMPLATE),
        manage_intro_thread(thread, starting_message.content),
    ]
    tasks.extend([starting_message.add_reaction(emoji) for emoji in emojis])
    await asyncio.gather(*tasks)


async def manage_intro_thread(
    thread: discord.Thread, intro_message_content: str
) -> None:
    await thread.send(**generate_intro_message(intro_message_content))
    await add_members_with_role(thread, GREETER_ROLE_ID)


async def handle_job_posting_thread(
    starting_message: discord.Message, thread: discord.Thread
) -> None:
    logger.info(f"Reacting to {thread.name!r} with ĎK")
    await starting_message.add_reaction("<:dk:842727526736068609>")


async def handle_candidate_thread(
    starting_message: discord.Message, thread: discord.Thread
) -> None:
    logger.info(f"Reacting to {thread.name!r} with 👍")
    await starting_message.add_reaction("👍")


async def handle_review_thread(
    starting_message: discord.Message, thread: discord.Thread
) -> None:
    if github_url := find_github_url(starting_message.content):
        logger.info(f"Found {github_url} in {thread.name!r}, reviewing…")
        await starting_message.add_reaction("🔬")
        await thread.send(f"Vidím, že máš GitHub profil: {github_url} 🔬")
        summary = await check_profile_url(github_url)
        logger.info(f"Done reviewing {github_url}")
        await thread.send(f"Hotovo: {summary.status}")

    if linkedin_url := find_linkedin_url(starting_message.content):
        logger.info(f"Found {linkedin_url} in {thread.name!r}, reviewing…")
        await starting_message.add_reaction("🔬")
        await thread.send(f"Vidím, že máš LinkedIn profil: {linkedin_url} 🔬")
        await thread.send(
            "Na LinkedIn zatím zpětnou vazbu dávat neumím, ale třeba pomůže někdo jiný."
        )

    await add_members_with_role(thread, REVIEWER_ROLE_ID)
