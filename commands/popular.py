from dis_snek.models import Scale
from dis_snek.models.application_commands import OptionTypes, SlashCommandChoice, slash_command, slash_option
from dis_snek.models.context import InteractionContext
from dis_snek.models.discord_objects.embed import Embed
import pymysql

from utils.database import Database
from utils.config import db_login
from utils.models import Star


class Popular(Scale):
    def __init__(self, bot):
        self.db = Database(pymysql.connect(**db_login))
        self.bot = bot

    # TODO SlashCommandChoice("person (in server)", "person")
    choices = [SlashCommandChoice("message (in server)", "message")]

    @slash_command("most", sub_cmd_name="popular", sub_cmd_description="Get the most popular stats of your choosing", scopes=[870046872864165888])
    @slash_option("choice", "What would you like to see the stats of", opt_type=OptionTypes.STRING, choices=choices, required=True)
    async def most_popular(self, ctx: InteractionContext, choice):
        if choice == "message":
            guild_stars = self.db.get_stars(ctx.guild.id)
            star: Star = max(guild_stars, key=lambda x: x.star_count)
            
            star_link = f"https://discordapp.com/channels/{star.guild_id}/{self.db.get_star_channel(star.guild_id)}/{star.star_id}"
            embed = Embed("Most Popular Message", f"The most popular message award goes to **{await self.bot.get_member(star.author_id, star.guild_id)}**")
            embed.add_field("Info", f"[Starboard Post]({star_link})")
            
            await ctx.send(embeds=[embed])


def setup(bot):
    Popular(bot)