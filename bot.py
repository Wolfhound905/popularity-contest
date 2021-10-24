from os import environ

import pymysql
from dis_snek.client import Snake
from dis_snek.models.application_commands import (
    OptionTypes,
    slash_command,
    slash_option,
    sub_command,
)
from dis_snek.models.context import InteractionContext
from dis_snek.models.discord_objects.embed import Embed
from dis_snek.models.listener import listen
from dotenv import load_dotenv

from database import Database

load_dotenv()

db = Database(
    pymysql.connect(
        host=environ["HOST"],
        user=environ["USER"],
        password=environ["PASSWORD"],
        database=environ["DATABASE"],
        charset="utf8mb4",
        port=int(environ["PORT"]),
        autocommit=True,
    )
)

bot = Snake(sync_interactions=True, delete_unused_application_cmds=True)


@listen()
async def on_ready():
    print(f"Logged in as: {bot.user}")


bot.guilds


@slash_command("setup", "Setup the Starboard channel and minumum star count")
@slash_option(
    "channel", "The channel to starboard messages to", OptionTypes.CHANNEL, True
)
@slash_option(
    "min_star_count",
    "The minimum amount of stars to star a message",
    OptionTypes.INTEGER,
)
async def setup(ctx: InteractionContext, channel, min_star_count: int = 4):
    db.setup(ctx.guild.id, channel.id, min_star_count)
    embed = Embed(
        "⭐ Setup Complete!",
        f"Posting to {channel.mention} with a minimun star count of {min_star_count}",
        color="#F9AC42",
    )
    await ctx.send(embeds=[embed])


@listen()
async def on_message_update(event):
    print(event.emoji.name)


@listen()
async def on_message_reaction_add(event):
    print(event.emoji.name)


bot.start(environ["TOKEN"])
