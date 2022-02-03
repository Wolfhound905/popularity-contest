from dis_snek.models import *
from utils.database import Database


class FilterCommands(Scale):
    def __init__(self, bot):
        self.bot = bot
        self.db: Database = self.bot.db

    @slash_command(
        "filter",
        sub_cmd_name="words",
        sub_cmd_description="Filter certain words from going on the starboard.",
    )
    @slash_option(
        "filter_words",
        "List of blacklisted words seperated by commas",
        OptionTypes.STRING,
        True,
    )
    @slash_option(
        "commit_mode",
        "Would you like to overwrite existing or add on?",
        OptionTypes.INTEGER,
        True,
        choices=[
            SlashCommandChoice(
                "Overwrite Existing Filters",
                1,
            ),
            SlashCommandChoice("Merge With Existing Filters", 2),
        ],
    )
    @slash_option(
        "mode",
        "Either prevent message or hide filtered words. (Default: Hide)",
        OptionTypes.INTEGER,
        False,
        choices=[
            SlashCommandChoice("Hide", 0),
            SlashCommandChoice("Prevent", 1),
        ],
    )
    async def filter_command(
        self,
        ctx: InteractionContext,
        filter_words: str,
        commit_mode: int,
        mode: int = 0,
    ):
        if ctx.author.has_permission(Permissions.MANAGE_GUILD):

            # This removes anny spaces and splits the words
            filter = list(
                " ".join(filter.split())
                for filter in [
                    filter_words.strip() for filter_words in filter_words.split(",")
                ]
                if filter
            )  # If you are reading this right now, I am sorry.

            if len(filter_words) == 0:
                embed = Embed(
                    "Error",
                    "You must provide a list of words to filter",
                    color="#EB4049",
                )
            new_filter = self.db.insert_filter(ctx.guild.id, filter, commit_mode, mode)
            # print(new_filter)
            embed = Embed(
                "Filter Complete!",
                f"The following words will be {'*hidden* on the ' if new_filter.mode == 0 else '*prevented* from being on the'} starboard:||\n"
                + ", ".join([f"`{filter}`" for filter in new_filter.filter_words])
                + "\n||",
                color="#FAD54E",
            )
            embed.set_footer("Work in progress feature.")
        else:
            embed = Embed(
                "Error",
                "You are missing `manage server` permission.",
                color="#EB4049",
            )
        await ctx.send(embeds=[embed])

    @filter_command.subcommand(
        sub_cmd_name="mode",
        sub_cmd_description="Change the filter mode",
    )
    @slash_option(
        "filter_mode",
        "Either prevent message or hide filtered words. (Default: Hide)",
        OptionTypes.INTEGER,
        True,
        choices=[
            SlashCommandChoice("Hide", 0),
            SlashCommandChoice("Prevent", 1),
        ],
    )
    async def filter_command_type(self, ctx: InteractionContext, filter_mode: int):
        if ctx.author.has_permission(Permissions.MANAGE_GUILD):
            filter = self.db.get_filter(ctx.guild.id)
            if not filter:
                embed = Embed(
                    "Error",
                    "Seems like there is no filter to change. Go create one with `/filter create`",
                    color="#EB4049",
                )
                await ctx.send(embed=embed)
                return
            self.db.toggle_filter_mode(ctx.guild.id, filter_mode)
            embed = Embed(
                "Filter Mode Changed",
                f"The filter mode has been changed to {'*Hidden*' if filter.mode == 0 else '*Prevent*'}",
                color="#FAD54E",
            )
        else:
            embed = Embed(
                "Error",
                "You are missing `manage server` permission.",
                color="#EB4049",
            )
        await ctx.send(embeds=[embed])

    @filter_command.subcommand(
        sub_cmd_name="remove",
        sub_cmd_description="Removes the filter",
    )
    async def remove_filter(self, ctx: InteractionContext):
        if ctx.author.has_permission(Permissions.MANAGE_GUILD):
            if not self.db.get_filter(ctx.guild.id):
                embed = Embed(
                    "Error",
                    "Uh oh, you havn't actually set up a filter yet. Go create one with `/filter create`",
                    color="#EB4049",
                )
                await ctx.send(embed=embed)
                return
            self.db.remove_filter(ctx.guild.id)
            embed = Embed(
                "Filter Removed",
                "The filter has been removed",
                color="#FAD54E",
            )
        else:
            embed = Embed(
                "Error",
                "You are missing `manage server` permission.",
                color="#EB4049",
            )
        await ctx.send(embeds=[embed])

    @filter_command.subcommand(
        sub_cmd_name="info",
        sub_cmd_description="Show existing filters",
    )
    async def list_filters(self, ctx: InteractionContext):
        if ctx.author.has_permission(Permissions.MANAGE_GUILD):
            filter = self.db.get_filter(ctx.guild.id)
            if not filter or not filter.filter_words:
                print("No filters found")
                embed = Embed(
                    "No Filters",
                    "There are no filters currently set.\nYou can add filters with `/setup filter create`",
                    color="#FAD54E",
                )
            elif filter.filter_words:
                embed = Embed(
                    "Current Filter",
                    f"{ctx.guild.name}'s current filter info.\n",
                    color="#FAD54E",
                )
                embed.add_field(
                    "Filter:",
                    f"Status: {'*Enabled*' if filter.enabled else '*Disabled*'}\n"
                    f"Mode: {'*Hidden*' if filter.mode == 0 else '*Prevent*'}\n"
                    f"Words: ⤦||\n{', '.join([f'`{word}`' for word in filter.filter_words])}\n||",
                )

        else:
            embed = Embed(
                "Error",
                "You are missing `manage server` permission.",
                color="#EB4049",
            )

        await ctx.send(embed=embed)

    @filter_command.subcommand(
        sub_cmd_name="toggle",
        sub_cmd_description="Turns off the filter",
    )
    @slash_option(
        "status",
        "Enable or Disable the filter",
        OptionTypes.STRING,
        True,
        choices=[SlashCommandChoice("On", "on"), SlashCommandChoice("Off", "off")],
    )
    async def filter_toggle(self, ctx: InteractionContext, status: str):
        if ctx.author.has_permission(Permissions.MANAGE_GUILD):
            if not self.db.get_filter(ctx.guild.id):
                embed = Embed(
                    "Error",
                    "I searched all across the database, but it seems your server doesn't have any filter. Go create one with `/filter create`",
                    color="#EB4049",
                )
                await ctx.send(embed=embed)
                return
            if status == "off":
                self.db.filter_toggle(ctx.guild.id, False)
                embed = Embed(
                    "Filter Disabled",
                    "The filter has been disabled",
                    color="#FAD54E",
                )
            elif status == "on":
                self.db.filter_toggle(ctx.guild.id, True)
                embed = Embed(
                    "Filter Enabled",
                    "The filter has been enabled",
                    color="#FAD54E",
                )
        else:
            embed = Embed(
                "Error",
                "You are missing `manage server` permission.",
                color="#EB4049",
            )
        await ctx.send(embeds=[embed])


def setup(bot):
    FilterCommands(bot)
