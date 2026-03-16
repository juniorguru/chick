import asyncio
import logging
from datetime import UTC, datetime
from typing import cast

import aiohttp
import discord
from discord.ext import commands, tasks
from jg.hen.core import check_profile_url

from jg.chick.lib import interests
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
    ping_members_with_role,
)


EGGTRAY_API_URL = "https://juniorguru.github.io/eggtray/profiles.json"


logger = logging.getLogger("jg.chick.bot")


intents = discord.Intents(
    guilds=True,
    members=True,
    messages=True,
    message_content=True,
)


class ChickBot(commands.Bot):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.interests: interests.Interests = {}


bot = ChickBot(intents=intents)


@bot.event
async def on_ready():
    for guild in bot.guilds:
        logger.info(f"Joined Discord {guild.name!r} as {guild.me.display_name!r}")

    async with interests.modifications(), interests.report_fetch_error(bot):
        bot.interests = interests.parse(
            await interests.fetch(),
            current_interests=bot.interests,
        )
        logger.info(f"Fetched {len(bot.interests)} interest threads")

    if not refetch_interests.is_running():
        refetch_interests.start()


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


@bot.slash_command(description="Odhlásí tě ze zájmové skupinky")
async def unfollow(context: discord.ApplicationContext):
    try:
        guild = cast(discord.Guild, context.guild)
        member = await guild.fetch_member(context.author.id)
        thread = cast(discord.Thread, context.channel)
        interest = bot.interests[thread.id]
        role = cast(discord.Role, guild.get_role(interest["role_id"]))
    except (AttributeError, KeyError):
        await context.respond(
            (
                "Píp, promiň, ale tenhle příkaz funguje jenom "
                "v zájmových vláknech uvnitř <#1075087563645263922>. "
                "Pokud už tě nebaví např. Python, jdi do jeho vlákna "
                "a tam použij `/unfollow`."
            ),
            delete_after=30,
        )
        return

    if role in member.roles:
        await member.remove_roles(role, reason="User requested /unfollow")
    await thread.remove_user(member)
    await context.respond(
        (
            "Odhlásilo jsem tě z téhle zájmové skupinky. Odebralo "
            f"jsem ti roli „{role.name}“ a vyhodilo z tohoto vlákna. "
            "Kdyby tě téma začalo zase zajímat, spusť tady `/follow`."
        ),
        delete_after=30,
    )


@bot.slash_command(description="Přihlásí tě do zájmové skupinky")
async def follow(context: discord.ApplicationContext):
    try:
        guild = cast(discord.Guild, context.guild)
        member = await guild.fetch_member(context.author.id)
        thread = cast(discord.Thread, context.channel)
        interest = bot.interests[thread.id]
        role = cast(discord.Role, guild.get_role(interest["role_id"]))
    except (AttributeError, KeyError):
        await context.respond(
            (
                "Píp, promiň, ale tenhle příkaz funguje jenom "
                "v zájmových skupinkách. Uvnitř <#1075087563645263922> "
                "si najdi vlákno např. o Pythonu a v něm použij `/follow`."
            ),
            delete_after=30,
        )
        return

    if role not in member.roles:
        await member.add_roles(role, reason="User requested /follow")
    await context.respond(
        (
            "Přihlásilo jsem tě do téhle zájmové skupinky. Dalo "
            f"jsem ti roli „{role.name}“ a přidalo tě sem do vlákna. "
            "Kdyby tě téma přestalo zajímat, spusť tady `/unfollow`."
        ),
        delete_after=30,
    )


@tasks.loop(hours=6)
async def refetch_interests():
    async with interests.modifications(), interests.report_fetch_error(bot):
        bot.interests = interests.parse(
            await interests.fetch(),
            current_interests=bot.interests,
        )
        logger.info(f"Fetched {len(bot.interests)} interest threads")


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
    now = datetime.now(UTC)

    if channel.name == "cv-github-linkedin" and bot_user.mention in message.content:
        logger.info("Noticed mention in #cv-github-linkedin, starting review")
        starting_message = (await fetch_starting_message(thread)) or message
        await handle_review_thread(starting_message, thread)

    async with interests.modifications():
        if interest := bot.interests.get(thread.id):
            logger.info(f"Noticed message in interest thread {thread.name!r}")
            if interests.should_notify(interest, now):
                logger.info(f"Adding role #{interest['role_id']}")
                await add_members_with_role(thread, interest["role_id"])
                interest["last_notified_at"] = now
            else:
                logger.info("Not adding due to cooldown")


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
    await ping_members_with_role(thread, GREETER_ROLE_ID)


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
        await ping_members_with_role(thread, REVIEWER_ROLE_ID)

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
        await ping_members_with_role(thread, REVIEWER_ROLE_ID)

    await thread.edit(
        applied_tags=prepare_tags(
            thread,
            cv=bool(cv_url),
            github=bool(github_url),
            linkedin=bool(linkedin_url),
        )
    )
