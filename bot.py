import dis_snek
import logging

from dis_snek.client import Snake
from dis_snek.models.application_commands import slash_command
from dis_snek.models.context import InteractionContext
from dis_snek.models.discord_objects.embed import Embed
from dis_snek.models.listener import listen

from utils.config import token

logging.basicConfig(filename="logs.log")
cls_log = logging.getLogger(dis_snek.const.logger_name)
cls_log.setLevel(logging.DEBUG)

bot = Snake(sync_interactions=True, delete_unused_application_cmds=True, asyncio_debug=True, default_prefix="⭐")


@listen()
async def on_ready():
    print(f"Logged in as: {bot.user}")
    print(f"Servers: {len(bot.guilds)}")


@slash_command("help", "Basic instructions and what this bot is")
async def help(ctx: InteractionContext):
    embed = Embed(
        "Starboard Help",
        "While the name of the bot is Popularity Contest, thats basically what a starboard is. A few of the commands I have or will be adding are listed below. 💫",
        color="#F9AC42",
    )
    embed.add_field("setup", "Sets up the starboard for the server")
    embed.add_field("More Info", f"No feature is blocked behind a vote wall, but if you are feeling kind could you [upvote](https://top.gg/bot/{bot.user.id}/vote)")
    await ctx.send(embeds=[embed])

bot.grow_scale("commands.star_listener")
bot.grow_scale("commands.setup")
bot.grow_scale("commands.popular")

bot.start(token)
