from dis_snek.models import Scale
from dis_snek.models.application_commands import (
    OptionTypes,
    slash_command,
    slash_option,
)
from dis_snek.models.context import InteractionContext
from utils.database import Database
from utils.config import db_login
import pymysql


class Extra(Scale):
    def __init__(self, bot):
        self.bot = bot
        self.db: Database = self.bot.db

    @slash_command(
        "status", "General information about the bot.", scopes=[902005056872775760]
    )
    async def status(self, ctx: InteractionContext):
        await ctx.send(str(self.bot.latency))


def setup(bot):
    Extra(bot)
