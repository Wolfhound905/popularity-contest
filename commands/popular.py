from dis_snek.models import Scale
from dis_snek.models.application_commands import ContextMenu, OptionTypes, SlashCommandChoice, context_menu, slash_command, slash_option
from dis_snek.models.context import InteractionContext
from dis_snek.models.discord_objects.embed import Embed
from dis_snek.models.enums import CommandTypes
import pymysql

from utils.database import Database
from utils.config import db_login
from utils.models import Star


class Popular(Scale):
    def __init__(self, bot):
        self.db = Database(pymysql.connect(**db_login))
        self.bot = bot

    # TODO SlashCommandChoice("person (in server)", "person")
    choices = [SlashCommandChoice("message", "message"), SlashCommandChoice("person", "person")]

    @slash_command("most", sub_cmd_name="popular", sub_cmd_description="Get the most popular stats of your choosing", scopes=[870046872864165888, 838667622245597194])
    @slash_option("choice", "What would you like to see the stats of", opt_type=OptionTypes.STRING, choices=choices, required=True)
    async def most_popular(self, ctx: InteractionContext, choice):
        if choice == "message":
            guild_stars = self.db.get_stars(ctx.guild.id)
            star: Star = max(guild_stars, key=lambda x: x.star_count)
            
            embed = Embed("Most Popular Message", f"The *Most Popular Message* award goes to **{await self.bot.get_member(star.author_id, star.guild_id)}**", color="#FFAC32")
            msg = await (await self.bot.get_channel(star.msg_channel_id)).get_message(star.message_id)
            embed.add_field("Info", f"Total stars: **{star.star_count}**\n[Starboard Post]({star.star_jump_url})\n[Original Message]({star.msg_jump_url})")
            embed.add_field("Message", msg.content if msg.content != "" else u"\u200b")
            if msg.attachments:
                for attachment in msg.attachments:
                    if attachment.content_type.startswith("image"):
                        embed.set_image(url=attachment.url)

        elif choice == "person":
            stars, total_count = self.db.get_most_popular(ctx.guild.id)
            embed = Embed("Most Popular Person", f"The *Most Popular Person* award goes to **{await self.bot.get_member(stars[0].author_id, ctx.guild.id)}**", color="#FFAC32")
            embed.add_field("Info", f"Total stars: **{total_count}**")
            stats = ""
            for i, star in enumerate(stars):
                if i + 1 > 3:
                    break
                stats += f"\n**[Star {i + 1}]({star.star_jump_url})** - {star.star_count} stars"
            embed.add_field("Top 3 Mesages", stats)
            
        # await ctx.send(embeds=[embed])
        await ctx.send(embeds=[embed])


    @context_menu("⭐ Stats", CommandTypes.USER, scopes=[870046872864165888])
    async def stats(self, ctx: InteractionContext):
        await ctx.defer()
        x = ctx.data
        print(x)


def setup(bot):
    Popular(bot)