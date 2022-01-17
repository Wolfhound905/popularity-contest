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
    delete_unused_application_cmds=False,
    default_prefix="⭐",  # never used
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


# @slash_command("privacy", "Privacy Policy")
# async def privacy(ctx: InteractionContext):
#     embed = Embed(
#         "Privacy Policy",


@slash_command("debug", scopes=[902005056872775760])
@slash_permission(
    Permission(324352543612469258, 902005056872775760, PermissionTypes.USER, True)
)
@slash_option("channel_id", "Channel ID", opt_type=OptionTypes.STRING, required=True)
@slash_option("message", "Message ID", opt_type=OptionTypes.STRING, required=True)
async def debug(ctx: InteractionContext, channel_id, message):
    channel = await bot.get_channel(int(channel_id))
    message = await channel.get_message(int(message))
    await ctx.send(f"{message.embeds}")


bot.grow_scale("commands.star_listener")
bot.grow_scale("commands.setup")
bot.grow_scale("commands.filter")
bot.grow_scale("commands.popular")
bot.grow_scale("utils.tasks")


bot.start(token)
