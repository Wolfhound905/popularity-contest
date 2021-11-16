from dis_snek.errors import Forbidden
from dis_snek.models import Scale
from dis_snek.models.application_commands import (
    OptionTypes,
    slash_command,
    slash_option,
)
from dis_snek.models.context import InteractionContext
from dis_snek.models.discord_objects.channel import (
    GuildPrivateThread,
    GuildPublicThread,
    GuildText,
)
from dis_snek.models.discord_objects.embed import Embed
from dis_snek.models.enums import Permissions

from utils.database import Database


class Setup(Scale):
    def __init__(self, bot):
        self.bot = bot
        self.db: Database = self.bot.db

    @slash_command(
        "setup",
        "Some custamization up ahead",
        sub_cmd_name="starboard",
        sub_cmd_description="Setup the Starboard channel and minumum star count",
    )
    @slash_option(
        "channel", "The channel to starboard messages to", OptionTypes.CHANNEL, True
    )
    @slash_option(
        "min_star_count",
        "The minimum amount of stars to star a message Default 3",
        OptionTypes.INTEGER,
    )
    async def setup(self, ctx: InteractionContext, channel, min_star_count: int = None):
        if await ctx.author.has_permission(Permissions.MANAGE_GUILD):
            if type(channel) not in [GuildPrivateThread, GuildPublicThread, GuildText]:
                error = Embed(
                    title="Error",
                    description="Channel must be a text channel",
                    color="#EB4049",
                )
                await ctx.send(embeds=[error])
                return

            min_stars = self.db.min_stars(ctx.guild.id)
            if min_star_count is None:
                if min_stars is None:
                    min_star_count = 3
                else:
                    min_star_count = min_stars

            if min_star_count < 1:
                error = Embed(
                    title="Error",
                    description="Minimum star count must be greater than 0",
                    color="#EB4049",
                )
                await ctx.send(embeds=[error])
                return
            try:
                tmp_msg = await channel.send(".")
                await tmp_msg.delete()
            except Forbidden:
                error = Embed(
                    title="Error",
                    description="I don't have permission to send messages in this channel",
                    color="#EB4049",
                )
                await ctx.send(embeds=[error])
                return

            self.db.setup(ctx.guild.id, channel.id, min_star_count)
            embed = Embed(
                "⭐ Setup Complete!",
                f"Posting to {channel.mention} with a minimum star count of {min_star_count}",
                color="#FAD54E",
            )
        else:
            embed = Embed(
                "Error",
                "You are missing `manage server` permission.",
                color="#EB4049",
            )
        await ctx.send(embeds=[embed])

    @setup.subcommand(
        sub_cmd_name="filter",
        sub_cmd_description="Filter certain words from going on the starboard.",
    )
    @slash_option(
        "filter_words",
        "List of blacklisted words seperated by spaces",
        OptionTypes.STRING,
        True,
    )
    async def filter(self, ctx: InteractionContext, filter_words: str):
        if await ctx.author.has_permission(Permissions.MANAGE_GUILD):
            # self.db.filter(ctx.guild.id, list)
            filter_words = filter_words.split(" ")
            if (
                len(filter_words) == 0
            ):  # this should nenver be possible if list is required
                embed = Embed(
                    "Error",
                    "You must provide a list of words to filter",
                    color="#EB4049",
                )
            filter_words = list(set(filter_words))
            embed = Embed(
                "Filter Complete!",
                "The following words have been blacklisted from the starboard:\n"
                + str(",".join([f"`{x}`" for x in filter_words])),
                color="#FAD54E",
            )
            embed.set_footer("This is not functioning for the momment.")
        else:
            embed = Embed(
                "Error",
                "You are missing `manage server` permission.",
                color="#EB4049",
            )
        await ctx.send(embeds=[embed])


def setup(bot):
    Setup(bot)
