from operator import imod
from dis_snek.client.errors import Forbidden

from dis_snek import (
    OptionTypes,
    slash_command,
    slash_option,
    Scale,
    InteractionContext,
    Embed,
    CommandTypes,
    Permissions,
    GuildPrivateThread,
    GuildPublicThread,
    GuildText,
    listen,
    ChannelTypes,
)
from dis_snek.api.events.discord import GuildJoin

from utils.database import Database


class Setup(Scale):
    def __init__(self, bot):
        self.bot = bot
        self.db: Database = self.bot.db

    @listen(GuildJoin)
    async def welcome_message(self, event: GuildJoin):
        if self.bot.is_ready:
            guild_in_config = self.db.get_star_channel(event.guild.id)
            if guild_in_config is None:
                for channel in event.guild.channels:
                    if channel.type == ChannelTypes.GUILD_TEXT:
                        if (
                            Permissions.SEND_MESSAGES
                            in event.guild.me.channel_permissions(channel)
                        ):
                            print("trying to send message")
                            await channel.send(
                                "Thanks for inviting me, get started by running `/setup starboard` :star:"
                            )
                            return

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
    @slash_option(
        "update_on_edit",
        "When the origin message is edited, update the starboard message (Default False)",
        OptionTypes.BOOLEAN,
    )
    async def setup(
        self,
        ctx: InteractionContext,
        channel,
        min_star_count: int = None,
        update_on_edit: bool = False,
    ):
        if ctx.author.has_permission(Permissions.MANAGE_GUILD):
            if type(channel) not in [GuildPrivateThread, GuildPublicThread, GuildText]:
                error = Embed(
                    title="Error",
                    description="Channel must be a text channel",
                    color="#EB4049",
                )
                await ctx.send(embeds=[error], ephemeral=True)
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
                await ctx.send(embeds=[error], ephemeral=True)
                return

            if Permissions.SEND_MESSAGES not in ctx.guild.me.channel_permissions(
                channel
            ):
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

            self.db.setup(ctx.guild.id, channel.id, min_star_count, update_on_edit)
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
        sub_cmd_name="update_on_edit",
        sub_cmd_description="Update starboard if message is updated",
    )
    @slash_option(
        "enable", "Enable updating on message edit", OptionTypes.BOOLEAN, True
    )
    async def update_on_edit(self, ctx: InteractionContext, enable: bool):
        if ctx.author.has_permission(Permissions.MANAGE_GUILD):
            self.db.edit_config(ctx.guild.id, "update_edited_messages", enable)
            if enable:
                embed = Embed(
                    "✅ Update on edit enabled",
                    "Starboard post will not be updated if the message is edited",
                    color="#FAD54E",
                )
            else:
                embed = Embed(
                    "✅ Update on edit disabled",
                    "Starboard post will no longer be updated if edited",
                    color="#FAD54E",
                )
            hidden = False
        else:
            embed = Embed(
                "Error",
                "You are missing `manage server` permission.",
                color="#EB4049",
            )
            hidden = True
        await ctx.send(embeds=[embed], ephemeral=hidden)


def setup(bot):
    Setup(bot)
