import dis_snek
import logging

from dis_snek import (
    Snake,
    slash_command,
    InteractionContext,
    Embed,
    Status,
    listen,
    slash_permission,
    OptionTypes,
    Permission,
    PermissionTypes,
    slash_option,
    message_command,
)


from utils.config import token, db_login
from utils.database import Database

import pymysql
from time import time


logging.basicConfig(
    filename="logs.log",
    datefmt="%Y-%m-%d %H:%M:%S",
    format="%(asctime)s %(levelname)-8s %(message)s",
)
cls_log = logging.getLogger(dis_snek.const.logger_name)
cls_log.setLevel(logging.DEBUG)

start_time = time()
bot = Snake(
    sync_interactions=True,
    delete_unused_application_cmds=False,  # never used
    status=Status.DND,
    activity="Star-ting",
)

bot.db = Database(pymysql.connect(**db_login))


@listen()
async def on_ready():
    print(f"Ready within: {round((time() - start_time), 2)} seconds")
    print(f"Logged in as: {bot.user}")
    print(f"Servers: {len(bot.guilds)}")


@slash_command("help", "Basic instructions and what this bot is")
async def help(ctx: InteractionContext):
    embed = Embed(
        "Starboard Help",
        "While the name of the bot is Popularity Contest, thats basically what a starboard is. A few of the commands I have or will be adding are listed below. 💫",
        color="#FAD54E",
    )
    embed.add_field("setup", "Sets up the starboard for the server")
    embed.add_field(
        "More Info",
        f"No feature is blocked behind a vote wall, but if you are feeling kind could you [upvote](https://top.gg/bot/{bot.user.id}/vote) \👉\👈",
    )
    await ctx.send(embeds=[embed])


@slash_command("privacy", "Privacy Policy")
async def privacy(ctx: InteractionContext):
    embed = Embed(
        "Privacy Policy",
        """Your data is important and we take your privacy seriously. This is a simple privacy policy that explains what we do with your data and how we use it. \n
        When you set up the bot we collect:
        - Guild ID
        - Starboard Channel ID

        For stared messages the following is stored:
        - The message ID
        - The message Channel ID
        - The message author ID
        - The amount of stars
        - IDs of the users who have starred the message
        - Starboard post ID
        
        We never store message content, only IDs and counts. 
        All of the code is open source and can be found [here](https://github.com/Wolfhound905/popularity-contest)
        If you are concerned please DM `Wolfhound905#1234`""",
    )
    await ctx.send(embed=embed, ephemeral=True)


bot.grow_scale("commands.star_listener")
bot.grow_scale("commands.setup")
bot.grow_scale("commands.filter")
bot.grow_scale("commands.popular")
bot.grow_scale("commands.manage")
bot.grow_scale("utils.tasks")


bot.start(token)
