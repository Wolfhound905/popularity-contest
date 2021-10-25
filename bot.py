from os import environ
from dis_snek.errors import Forbidden
from dis_snek.models.discord_objects.channel import (
    GuildPrivateThread,
    GuildPublicThread,
    GuildText,
)
from dis_snek.models.enums import Permissions

import pymysql
from dis_snek.client import Snake
from dis_snek.models.application_commands import (
    OptionTypes,
    slash_command,
    slash_option,
)
from dis_snek.models.context import InteractionContext
from dis_snek.models.discord_objects.embed import Embed
from dis_snek.models.listener import listen
from dotenv import load_dotenv

from utils.database import Database
from utils.config import db_login, token
from utils.models import Star

bot = Snake(sync_interactions=True, delete_unused_application_cmds=True)


@listen()
async def on_ready():
    print(f"Logged in as: {bot.user}")


@slash_command("help", "Basic instructions and what this bot is")
async def help(ctx: InteractionContext):
    embed = Embed(
        "Starboard Help",
        "While the name of the bot is Popularity Contest, thats bassicly what a starboard is. A few of the commads I have or will be adding are listed below. 💫",
        color="#F9AC42",
    )
    embed.add_field("setup", "Sets up the starboard for the server")
    await ctx.send(embeds=[embed])


bot.grow_scale("commands.reaction_listener")
bot.grow_scale("commands.setup")

bot.start(token)
