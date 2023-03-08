import os
from datetime import datetime

import discord
from discord.ext import commands


DAYS = ["Pondělní", "Úterní", "Středeční",
        "Čtvrteční", "Páteční", "Sobotní", "Nedělní"]

DISCORD_API_KEY = os.getenv('DISCORD_API_KEY')


bot = commands.Bot()


def is_thread(message: discord.Message) -> bool:
    """Checks if a message is thread"""
    return message.type == discord.MessageType.thread_created


# TODO let's start with less important channels first
# async def create_ahoj_thread(message: discord.Message) -> None:
#     """Creates a thread for a message in #ahoj, ahoj_thread_handler will catch the creation"""
#     thread_name = "Ahoj {}!".format(message.author.display_name)
#
#     if is_thread(message):
#         return
#
#     if message.is_system():
#         return
#
#     await message.create_thread(name=thread_name)


# TODO let's start with less important channels first
# async def ahoj_thread_handler(thread: discord.Thread) -> None:
#     """Called when a thread is created in #ahoj. Kuře-made threads included"""
#     message = thread.starting_message
#     member_name = message.author.display_name
#     thread_name = "Ahoj {}!".format(member_name)
#
#     await thread.edit(name=thread_name)
#     await message.add_reaction("👋")
#     await message.add_reaction("🐣")
#     # The thread message has to be sent last, or the API will process it before the actual users message. The reactions above work as a delay
#     await thread.send("Nazdar {}, vítej v klubu!".format(member_name))


async def create_pvp_thread(message: discord.Message) -> None:
    """Creates a thread for a message in #past-vedle-pasti"""
    if is_thread(message):
        return

    weekday = datetime.now().weekday()

    await message.create_thread(name="{} past na {}".format(DAYS[weekday], message.author.display_name))


async def create_mdo_thread(message: discord.Message) -> None:
    """Creates a thread for a message in #můj-dnešní-objev"""
    if is_thread(message):
        return

    weekday = datetime.now().weekday()

    await message.create_thread(name="{} objev od {}".format(DAYS[weekday], message.author.display_name))


@bot.event
async def on_ready():
    print('Ready!')


@bot.event
async def on_message(message: discord.Message) -> None: # Message was sent
    print('Processing message')

    if message.author == bot.user: # The bot caught his own message
        return

    if message.guild is None: # DMs block
        return

    channel_name = message.channel.name

    # TODO let's start with less important channels first
    # if channel_name == "ahoj":
    #     await create_ahoj_thread(message)
    # elif
    if channel_name == "past-vedle-pasti":
        await create_pvp_thread(message)
    elif channel_name == "můj-dnešní-objev":
        await create_mdo_thread(message)


# TODO let's start with less important channels first
# @bot.event
# async def on_thread_create(thread: discord.Thread) -> None:
#     channel_name = thread.starting_message.channel.name
#     if channel_name == "ahoj":
#         await ahoj_thread_handler(thread)


def main():
    bot.run(DISCORD_API_KEY)
