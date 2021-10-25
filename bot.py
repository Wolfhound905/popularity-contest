from dis_snek.client import Snake
from dis_snek.models.application_commands import slash_command
from dis_snek.models.context import InteractionContext
from dis_snek.models.discord_objects.embed import Embed
from dis_snek.models.listener import listen

from utils.config import token

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
