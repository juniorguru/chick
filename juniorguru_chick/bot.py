import re
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

PATTERNS_EMOJIS_MAPPING = {
    re.compile(r'\bpython\w*\b', re.I): ['<:python:842331892091322389>'],
    re.compile(r'\bsql\b', re.I): ['<:database:900833211809136641>'],
    re.compile(r'\bphp\b', re.I): ['<:php:842331754731274240>'],
    re.compile(r'\b(nette|laravel|symfony)\w*\b', re.I): ['<:php:842331754731274240>'],
    re.compile(r'\bmysql\b', re.I): ['<:mysql:1036337592582541314>'],
    re.compile(r'\bmongo\w*\b', re.I): ['<:mongodb:976200776118583348>'],
    re.compile(r'\bpostgre\w+\b', re.I): ['<:postgresql:900831229971169350>'],
    re.compile(r'\bkubernet\w*\b', re.I): ['<:kubernetes:976200847014899742>'],
    re.compile(r'\bdocker\w*\b', re.I): ['<:docker:842465373911777290>'],
    re.compile(r'\blinux\w*\b', re.I): ['<:tux:842343455845515264>'],
    re.compile(r'\bswift\w*\b', re.I): ['<:swift:900831808814473266>'],
    re.compile(r'\bdjang\w+\b', re.I): ['<:django:844534232297504779>'],
    re.compile(r'\bflask\w*\b', re.I): ['<:flask:844534214904905748>'],
    re.compile(r'\bpandas\b', re.I): ['<:pandas:844567908688461854>'],
    re.compile(r'\bexcel\w*\b', re.I): ['<:excel:960457644504674314>'],
    re.compile(r'\bpower ?bi\b', re.I): ['<:powerbi:960457607745794119>'],
    re.compile(r'\bdatab(aá)ze\b'): ['<:database:900833211809136641>'],
    re.compile(r'\bjavascript\w*\b', re.I): ['<:javascript:842329110293381142>'],
    re.compile(r'\bJS\b'): ['<:javascript:842329110293381142>'],
    re.compile(r'\btypescript\w*\b', re.I): ['<:typescript:842332083605995541>'],
    re.compile(r'\bTS\b'): ['<:typescript:842332083605995541>'],
    re.compile(r'\bHTML\b'): ['<:html:842343387964375050>'],
    re.compile(r'\bCSS\b'): ['<:css:842343369618751519>'],
    re.compile(r'\bfront\-?end\w*\b', re.I): ['<:html:842343387964375050>', '<:css:842343369618751519>', '<:javascript:842329110293381142>'],
    re.compile(r'\bbootstrap\w*\b', re.I): ['<:bootstrap:900834695422545940>', '<:css:842343369618751519>'],
    re.compile(r'\btailwind\w*\b', re.I): ['<:tailwind:900834412248309770>', '<:css:842343369618751519>'],
    re.compile(r'\bC#\b'): ['<:csharp:842666113230045224>'],
    re.compile(r'\b\.NET\b', re.I): ['<:csharp:842666113230045224>'],
    re.compile(r'\b(java|javy|javě|javu|javou)\b', re.I): ['<:java:1036333651740327966>'],
    re.compile(r'\bkotlin\w*\b', re.I): ['<:kotlin:1001234560056578149>'],
    re.compile(r'\bC\+\+\b'): ['<:cpp:842666129071931433>'],
    re.compile(r'\breact\w*\b', re.I): ['<:react:842332165822742539>'],
    re.compile(r'\bvue\b', re.I): ['<:vue:842332056138416168>'],
    re.compile(r'\bangular\w*\b', re.I): ['<:angular:844527194730266694>'],
    re.compile(r'\bnext\.?js\b', re.I): ['<:nextjs:963799617886121994>'],
    re.compile(r'\bAPI\b'): ['<:api:900833604303732766>'],
}


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
    emojis = set()
    for pattern_re, pattern_emojis in PATTERNS_EMOJIS_MAPPING.items():
        if pattern_re.search(message_content):
            emojis.update(pattern_emojis)
    return ["👋", "🐣", "👍"] + list(emojis)
