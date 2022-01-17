from dis_snek import OptionTypes, slash_command, slash_option, InteractionContext, Scale

from utils.database import Database


class ManageStars(Scale):
    def __init__(self, bot):
        self.bot = bot
        self.db: Database = self.bot.db

    @slash_command("remove", "Remove a star")
    @slash_option("star_id", "The star on the Starboard", OptionTypes.INTEGER, True)
    @slash_option(
        "blacklist",
        "Prevent this message from being on the again?",
        OptionTypes.BOOLEAN,
        False,
    )
    async def remove(self, ctx: InteractionContext, star_id, blacklist):
        await ctx.send("Coming soon™️", ephemeral=True)
        # try:
        #     if 64 > star_id.bit_length() < 22:
        #         raise ValueError("ID (snowflake) is not in correct discord format!")
        # except ValueError:
        #     await ctx.send("Invalid star ID", ephemeral=True)
        #     return
        # star = self.db.check_existing(star_id)
        # if star is None:
        #     await ctx.reply(f"Star `{star_id}` not found")
        #     return


def setup(bot):
    ManageStars(bot)
