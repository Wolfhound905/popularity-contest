""" This contains stat commands """

from random import choice
from dis_snek.errors import NotFound

from dis_snek.models import Scale
from dis_snek.models.application_commands import (
    ContextMenu,
    OptionTypes,
    SlashCommandChoice,
    context_menu,
    slash_command,
    slash_option,
)
from dis_snek.models.context import InteractionContext
from dis_snek.models.discord_objects.embed import Embed
from dis_snek.models.enums import CommandTypes
from utils.database import Database
from utils.errors import NoResults
from utils.models import Star


class Popular(Scale):
    def __init__(self, bot):
        self.bot = bot
        self.db: Database = self.bot.db

    # TODO SlashCommandChoice("person (in server)", "person")
    choices = [
        SlashCommandChoice("message", "message"),
        SlashCommandChoice("person", "person"),
    ]

    @slash_command(
        "most",
        sub_cmd_name="popular",
        sub_cmd_description="Get the most popular stats of your choosing",
    )
    @slash_option(
        "choice",
        "What would you like to see the stats of",
        opt_type=OptionTypes.STRING,
        choices=choices,
        required=True,
    )
    async def most_popular(self, ctx: InteractionContext, choice):
        if choice == "message":
            try:
                guild_stars = self.db.get_stars(ctx.guild.id)
            except NoResults:
                await ctx.send(
                    "No stars have been recorded yet. Go ahead and ⭐ some messages!",
                    ephemeral=True,
                )
                return
            star: Star = max(guild_stars, key=lambda x: x.star_count)
            print(star.author_id)
            try:
                author = await self.bot.get_member(star.author_id, star.guild_id)
            except NotFound:
                author = await self.bot.get_user(star.author_id)
            embed = Embed(
                "Most Popular Message",
                f"The *Most Popular Message* award goes to **{author}**",
                color="#FFAC32",
            )
            msg = await (await self.bot.get_channel(star.msg_channel_id)).get_message(
                star.message_id
            )
            embed.add_field(
                "Info",
                f"Total stars: **{star.star_count}**\n[Starboard Post]({star.star_jump_url})\n[Original Message]({star.msg_jump_url})",
            )
            embed.add_field("Message", msg.content if msg.content != "" else "\u200b")
            if msg.attachments:
                for attachment in msg.attachments:
                    if attachment.content_type.startswith("image"):
                        embed.set_image(url=attachment.url)

        elif choice == "person":
            try:
                stars, total_count = self.db.get_most_popular(ctx.guild.id)
            except NoResults:
                await ctx.send(
                    "No stars have been recorded yet. Go ahead and ⭐ some messages!",
                    ephemeral=True,
                )
                return
            embed = Embed(
                "Most Popular Person",
                f"The *Most Popular Person* award goes to **{await self.bot.get_member(stars[0].author_id, ctx.guild.id)}**",
                color="#FFAC32",
            )
            embed.add_field("Info", f"Total stars: **{total_count}**")
            stats = ""
            for i, star in enumerate(stars):
                if i + 1 > 3:
                    break
                stats += f"\n**[Star {i + 1}]({star.star_jump_url})** - {star.star_count} stars"
            embed.add_field("Top 3", stats)

        await ctx.send(embeds=[embed])

    @context_menu("Popularity", CommandTypes.USER)
    async def stats(self, ctx: InteractionContext):
        await ctx.defer()
        print(ctx.target_id)
        target_author = list(ctx.resolved.users.values())[0]
        try:
            stars, total_count = self.db.get_user_stats(ctx.guild.id, target_author.id)
        except NoResults:
            embed = Embed(
                "⭐ Stats 💫",
                choice(
                    [
                        f"{target_author.mention} must not be too popular because they don't have any stars yet.",
                        f"Seems like {target_author.mention} isn't in the cool kids club because they don't have any stars.",
                        f"There must be some light pollution, because there are no stars for {target_author.mention}",
                        f"{target_author.mention} isn't a good Uber driver since they have 0 stars.",
                        f"I went star gazing for {target_author.mention} messages, but it seems they don't have any",
                        f"Found no stars for {target_author.mention}, they might need some new friends.",
                        f"Either my programming is wrong or {target_author.mention} has no stars.\n||And my programming is never wrong.||",
                        f"{target_author.mention} has no stars.",
                        f"I looked through the messages and found no stars for {target_author.mention}",
                        f"{target_author.mention} even Wumpus is more popular than you, 0 stars.",
                        f"{target_author.mention} is not popular enough to be a star.",
                        f"Hey look, {target_author.mention} is just as popular as me... 0 stars :(",
                        f"Yikes, {target_author.mention} has 0 stars 😬",
                        f"{target_author.mention} did not live up to their parent's expectations, which were already [middling](https://www.dictionary.com/browse/middling) at best.",
                        f"{target_author.mention} forgot that they actually needed to be popular to receive stars.",
                    ]
                ),
                color="#FFAC32",
            )
            embed.set_author(name=target_author.tag, icon_url=target_author.avatar.url)
            await ctx.send(embeds=[embed])
            return
        embed = Embed(
            "⭐ Stats 💫",
            choice(
                [
                    "Here are the stars you requested",
                    "Don't get upset if they're more popular",
                    "I wish I had that many stars.",
                    "Don't go bragging about your stats now.",
                    "Are you a star now?",
                    "You're the star!",
                    "If I were you that seems like a good amount of stars.",
                ]
            ),
            color="#FFAC32",
        )
        embed.set_author(name=target_author.tag, icon_url=target_author.avatar.url)

        embed.add_field("Info", f"Total stars: **{total_count}**")
        stats = ""
        for i, star in enumerate(stars):
            if i + 1 > 3:
                break
            stats += (
                f"\n**[Star {i + 1}]({star.star_jump_url})** - {star.star_count} stars"
            )
        embed.add_field("Top 3", stats)

        await ctx.send(embeds=[embed])

    @slash_command(
        "global",
        sub_cmd_name="stats",
        sub_cmd_description="View global ✨ stats",
    )
    async def global_stats(self, ctx: InteractionContext):
        await ctx.defer()
        message_total, star_total = self.db.get_global_stats()
        embed = Embed(
            "Global Stats 🌟",
            choice(
                [
                    "Here are the global stars you requested",
                    "Holy smokes that's a lot of stars",
                    "I didn't even know I could count that high.",
                    "People really like reacting to messages.",
                ]
            ),
            color="#FFAC32",
        )
        msg = f"Total Stars: **{star_total}**\nTotal Starboard Count: **{message_total}**\nServers: **{len(self.bot.guilds)}**"
        embed.add_field("Stats:", msg, False)
        try:
            stars = self.db.get_stars(ctx.guild.id)
            # get sum of all stars in stars
            star_count = sum(star.star_count for star in stars)

            msg = f"**{round((star_count / star_total) * 100)}%** of all stars are from this server."
            embed.add_field(f"{ctx.guild.name}'s Contributions", msg, False)
        except NoResults:
            pass
        embed.set_footer("This is not the final form.")
        await ctx.send(embeds=[embed])


def setup(bot):
    Popular(bot)
