from dis_snek.models import Scale
from dis_snek.models.application_commands import OptionTypes, slash_command, slash_option
from dis_snek.models.context import InteractionContext
from dis_snek.models.snowflake import Snowflake_Type
from utils.database import Database
from utils.models import Star
from utils.config import db_login
import pymysql
from dis_snek.models.snowflake import to_snowflake



class ManageStars(Scale):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database(pymysql.connect(**db_login))

    @slash_command("remove", "Remove a star")
    @slash_option("star_id", "The star on the Starboard", OptionTypes.INTEGER, True)    
    @slash_option("blacklist", "Prevent this message from being on the again?", OptionTypes.BOOLEAN, False)
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