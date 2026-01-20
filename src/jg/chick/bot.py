import asyncio
import logging
from datetime import datetime
from typing import cast

import aiohttp
import discord
from discord.ext import commands, tasks
from jg.hen.core import check_profile_url

from jg.chick.lib.interests import (
    INTERESTS_API_URL,
    InterestsManager,
    report_api_error,
)
from jg.chick.lib.intro import (
    GREETER_ROLE_ID,
    THREAD_NAME_TEMPLATE as INTRO_THREAD_NAME_TEMPLATE,
    choose_intro_emojis,
    generate_intro_message,
)
from jg.chick.lib.reviews import (
    GITHUB_API_KEY,
    REVIEWER_ROLE_ID,
    find_cv_url,
    find_github_url,
    find_linkedin_url,
    format_summary,
    prepare_tags,
)
from jg.chick.lib.threads import (
    add_members_with_role,
    ensure_thread_name,
    fetch_starting_message,
    is_thread_created,
    name_thread,
)


EGGTRAY_API_URL = "https://juniorguru.github.io/eggtray/profiles.json"


logger = logging.getLogger("jg.chick.bot")


intents = discord.Intents(
    guilds=True,
    members=True,
    messages=True,
    message_content=True,
)


bot = commands.Bot(intents=intents)

# Initialize interests manager
interests_manager = InterestsManager()


async def fetch_interests_from_api() -> bool:
    """
    Fetches interests data from the API and updates the manager.

    This is the "imperative shell" - contains I/O operations.

    Returns:
        True if successful, False otherwise.
    """
    try:
        logger.info(f"Fetching interests from {INTERESTS_API_URL}")
        async with aiohttp.ClientSession() as session:
            async with session.get(INTERESTS_API_URL) as resp:
                if resp.status == 200:
                    interests = await resp.json()
                    interests_manager.update_interests(interests, datetime.now())
                    return True
                else:
                    logger.error(f"Failed to fetch interests: HTTP {resp.status}")
                    return False
    except Exception as e:
        logger.exception(f"Error fetching interests: {e}")
        return False


@bot.event
async def on_ready():
    for guild in bot.guilds:
        logger.info(f"Joined Discord {guild.name!r} as {guild.me.display_name!r}")

    # Fetch interests on startup
    logger.info("Fetching interests on startup")
    if not await fetch_interests_from_api():
        await report_api_error(
            bot,
            "Failed to fetch interests data on startup. The bot will retry periodically.",
        )

    # Start background task for periodic refresh
    if not refresh_interests_task.is_running():
        refresh_interests_task.start()


@tasks.loop(hours=1)
async def refresh_interests_task():
    """
    Background task to periodically check and refresh interests data.

    Runs every hour but only refreshes if data is older than INTERESTS_REFRESH_INTERVAL.
    """
    if interests_manager.should_refresh_now():
        logger.info("Refreshing interests data")
        if not await fetch_interests_from_api():
            await report_api_error(
                bot, "Failed to refresh interests data. Will retry on next cycle."
            )


@bot.event
async def on_error(self, event, *args, **kwargs):
    logger.exception(f"Error while handling {event!r}")
    raise


@bot.event
async def on_message(message: discord.Message):
    if not bot.user:
        raise RuntimeError("Bot user not initialized")
    if message.author.id == bot.user.id:
        logger.info("Message sent by the bot itself, skipping")
        return
    if is_thread_created(message) or message.is_system():
        logger.info("System message, skipping")
        return
    if message.guild is None:
        logger.info("Processing DM message")
        return await on_dm_message(bot.user, message)
    if channel := getattr(message.channel, "parent", None):
        logger.info("Processing thread message")
        thread = cast(discord.Thread, message.channel)
        return await on_thread_message(bot.user, channel, thread, message)
    logger.info("Processing regular message")
    channel = cast(discord.GroupChannel, message.channel)
    return await on_regular_message(bot.user, channel, message)


@bot.slash_command(description="Nápověda k použití kuřete")
async def help(context: discord.ApplicationContext):
    await context.respond(
        "Píp píp píp! Všechno se dovíš v [dokumentaci na webu](https://junior.guru/about/bot/) 📖"
    )


@bot.slash_command(description="Jaké je tvoje Discord ID?")
async def discord_id(context: discord.ApplicationContext):
    await context.respond(
        f"Tvoje Discord ID je `{context.author.id}`. "
        "Až si budeš zakládat profil v [seznamu kandidátů](https://junior.guru/candidates/), "
        "bude se ti tahle informace hodit <a:awkward:985064290044223488>"
    )


async def on_dm_message(bot_user: discord.ClientUser, message: discord.Message):
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


async def on_thread_message(
    bot_user: discord.ClientUser,
    channel: discord.GroupChannel,
    thread: discord.Thread,
    message: discord.Message,
):
    # Check if this is an interest thread and notify if needed
    role_id = interests_manager.get_role_for_thread(thread.id)
    if role_id:
        # Atomically check and mark notification to avoid race conditions
        if await interests_manager.try_notify_role_async(role_id):
            logger.info(
                f"New message in interest thread {thread.name!r}, adding role {role_id} members"
            )
            await add_members_with_role(thread, role_id)

    if channel.name == "cv-github-linkedin" and bot_user.mention in message.content:
        logger.info("Noticed mention in #cv-github-linkedin, starting review")
        starting_message = (await fetch_starting_message(thread)) or message
        await handle_review_thread(starting_message, thread)


async def on_regular_message(
    bot_user: discord.ClientUser,
    channel: discord.GroupChannel,
    message: discord.Message,
):
    if channel.name == "ahoj":
        logger.info("Creating thread in #ahoj")
        name = name_thread(message, INTRO_THREAD_NAME_TEMPLATE)
        await message.create_thread(name=name)
        return

    if channel.name == "past-vedle-pasti":
        logger.info("Creating thread in #past-vedle-pasti")
        name = name_thread(
            message,
            "{weekday} past na {author}",
            bracket_name_template="Past na {author}: {bracket_content}",
        )
        await message.create_thread(name=name)
        return

    if channel.name == "můj-dnešní-objev":
        logger.info("Creating thread in #můj-dnešní-objev")
        name = name_thread(
            message,
            "{weekday} objev od {author}",
            bracket_name_template="Objev od {author}: {bracket_content}",
        )
        await message.create_thread(name=name)
        return


@bot.event
async def on_thread_create(thread: discord.Thread):
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
):
    emojis = choose_intro_emojis(starting_message.content)
    logger.info(
        f"Processing thread {thread.name!r} (reacting with {emojis!r} and more…)"
    )
    tasks = [
        ensure_thread_name(thread, INTRO_THREAD_NAME_TEMPLATE),
        manage_intro_thread(thread, starting_message.content),
    ]
    tasks.extend([starting_message.add_reaction(emoji) for emoji in emojis])
    await asyncio.gather(*tasks)


async def manage_intro_thread(thread: discord.Thread, intro_message_content: str):
    await thread.send(**generate_intro_message(intro_message_content))
    await add_members_with_role(thread, GREETER_ROLE_ID)


async def handle_job_posting_thread(
    starting_message: discord.Message, thread: discord.Thread
):
    logger.info(f"Reacting to {thread.name!r} with ĎK")
    await starting_message.add_reaction("<:dk:842727526736068609>")


async def handle_candidate_thread(
    starting_message: discord.Message, thread: discord.Thread
):
    logger.info(f"Reacting to {thread.name!r} with 👍")
    await starting_message.add_reaction("👍")


async def handle_review_thread(
    starting_message: discord.Message, thread: discord.Thread
):
    if cv_url := find_cv_url(starting_message.attachments):
        logger.info(f"Found CV in {thread.name!r}, reviewing…")
        await starting_message.add_reaction("🔬")
        await starting_message.reply(
            (
                "📝 Zavětřilo jsem CV"
                "\n\n"
                "🙏 Na CV zatím zpětnou vazbu dávat neumím, ale třeba pomůže někdo jiný"
                "\n\n"
                "💡 Přečti si [návod na CV](https://junior.guru/handbook/cv/) v příručce, ušetříš spoustu času sobě i nám! "
                "Ve zpětné vazbě nebudeme muset opakovat rady z návodu a budeme se moci soustředit na to podstatné."
            ),
            suppress=True,
        )
        await add_members_with_role(thread, REVIEWER_ROLE_ID)

    if github_url := find_github_url(starting_message.content):
        logger.info(f"Found {github_url} in {thread.name!r}, reviewing…")
        await starting_message.add_reaction("🔬")
        await starting_message.reply(
            (
                f"<:github:842685206095724554> Zavětřilo jsem [GitHub profil]({github_url}), jdu se v tom pohrabat…"
                "\n\n"
                "💡 Přečti si [návod na GitHub profil](https://junior.guru/handbook/github-profile/) v příručce, pochopíš kontext mých doporučení."
            ),
            suppress=True,
        )
        logger.info("Checking profiles API…")
        profiles = []
        async with aiohttp.ClientSession() as session:
            async with session.get(EGGTRAY_API_URL) as resp:
                if resp.status == 200:
                    profiles = (await resp.json())["items"]
                    logger.info(f"Found {len(profiles)} profiles")

        async with thread.typing():
            logger.debug(f"{'Using' if GITHUB_API_KEY else 'Not using'} GitHub API key")
            summary = await check_profile_url(github_url, github_api_key=GITHUB_API_KEY)
            logger.info(
                f"Done reviewing {github_url}: {'ERROR' if summary.error else 'OK'}"
            )
            has_profile = any(
                profile["github_username"] == summary.username for profile in profiles
            )
            logger.info(f"User has profile: {has_profile}")
            for message in format_summary(summary, has_profile):
                await thread.send(**message)

    if linkedin_url := find_linkedin_url(starting_message.content):
        logger.info(f"Found {linkedin_url} in {thread.name!r}, reviewing…")
        await starting_message.add_reaction("🔬")
        await starting_message.reply(
            (
                f"<:linkedin:915267970752712734> Zavětřilo jsem [LinkedIn profil]({linkedin_url})"
                "\n\n"
                "🙏 Na LinkedIn zatím zpětnou vazbu dávat neumím, ale třeba pomůže někdo jiný"
                "\n\n"
                "💡 Přidej se do [naší LinkedIn skupiny](https://www.linkedin.com/groups/13988090/). "
                "Můžeš se pak snadno propojit s ostatními členy a oni s tebou. "
                "Zároveň se ti bude logo junior.guru zobrazovat na profilu v sekci „zájmy”. "
                "Nevíme, jestli ti to přidá nějaký kredit u recruiterů, ale vyloučeno to není!"
            ),
            suppress=True,
        )
        await add_members_with_role(thread, REVIEWER_ROLE_ID)

    await thread.edit(
        applied_tags=prepare_tags(
            thread,
            cv=bool(cv_url),
            github=bool(github_url),
            linkedin=bool(linkedin_url),
        )
    )
