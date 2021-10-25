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
import pymysql
from utils.config import db_login

from utils.database import Database


class Setup(Scale):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database(pymysql.connect(**db_login))

    @slash_command("setup", "Setup the Starboard channel and minumum star count")
    @slash_option(
        "channel", "The channel to starboard messages to", OptionTypes.CHANNEL, True
    )
    @slash_option(
        "min_star_count",
        "The minimum amount of stars to star a message",
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
            min_stars = self.db.min_stars(ctx.guild.id)
            if min_star_count is None and min_stars:
                min_star_count = min_stars

            self.db.setup(ctx.guild.id, channel.id, min_star_count)
            embed = Embed(
                "⭐ Setup Complete!",
                f"Posting to {channel.mention} with a minimum star count of {min_star_count}",
                color="#F9AC42",
            )
        else:
            embed = Embed(
                "Error",
                "Missing `manage server` permission.",
                color="#EB4049",
            )
        await ctx.send(embeds=[embed])


def setup(bot):
    Setup(bot)
