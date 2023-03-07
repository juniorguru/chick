import discord
from discord.ext import commands
from datetime import datetime

#! API KEY, read from file "API_KEY" in the same directory as this .py file
with open("API_KEY", "r") as file:
    API_KEY = file.readline().strip()

bot = commands.Bot()

DAYS = ["Pondělní", "Úterní", "Středeční",
        "Čtvrteční", "Páteční", "Sobotní", "Nedělní"]

# Checks if a message is thread
def is_thread(message: discord.Message) -> bool:
    return message.type == discord.MessageType.thread_created

# Creates a thread for a message in #ahoj, ahoj_thread_handler will catch the creation
async def create_ahoj_thread(message: discord.Message) -> None:
    thread_name = "Ahoj {}!".format(message.author.name)

    if is_thread(message):
        return

    if message.is_system():
        return

    await message.create_thread(name=thread_name)

# Called when a thread is created in #ahoj. Kuře-made threads included
async def ahoj_thread_handler(thread: discord.Thread) -> None:
    message = thread.starting_message
    member_name = message.author.name
    thread_name = "Ahoj {}!".format(member_name)

    await thread.edit(name=thread_name)
    await message.add_reaction("👋")
    await message.add_reaction("🐣")
    # The thread message has to be sent last, or the API will process it before the actual users message. The reactions above work as a delay
    await thread.send("Nazdar {}, vítej v klubu!".format(member_name))

# Creates a thread for a message in #past-vedle-pasti
async def create_pvp_thread(message: discord.Message) -> None:
    if is_thread(message):
        return

    weekday = datetime.now().weekday()

    await message.create_thread(name="{} past na {}".format(DAYS[weekday], message.author.name))
    await message.add_reaction("🐣")

# Creates a thread for a message in #múj-dnešní-objev
async def create_mdo_thread(message: discord.Message) -> None:
    if is_thread(message):
        return

    weekday = datetime.now().weekday()

    await message.create_thread(name="{} objev od {}".format(DAYS[weekday], message.author.name))
    await message.add_reaction("🐣")

@bot.event
async def on_message(message: discord.Message) -> None: # Message was sent
    if message.author == bot.user: # The bot caught his own message
        return

    if message.guild is None: # DMs block
        return

    channel_name = message.channel.name

    if channel_name == "ahoj":
        await create_ahoj_thread(message)
    elif channel_name == "past-vedle-pasti":
        await create_pvp_thread(message)
    elif channel_name == "můj-dnešní-objev":
        await create_mdo_thread(message)


@bot.event
async def on_thread_create(thread: discord.Thread) -> None:
    channel_name = thread.starting_message.channel.name
    if channel_name == "ahoj":
        await ahoj_thread_handler(thread)

bot.run(API_KEY)
