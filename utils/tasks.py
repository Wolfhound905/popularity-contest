from dis_snek import (
    Status,
    listen,
)
from dis_snek.ext.tasks.triggers import IntervalTrigger
from dis_snek.ext.tasks.task import Task

from utils.misc import get_random_presence
from utils.config import topgg_token
from dis_snek.models import Scale
import aiohttp


class Tasks(Scale):
    def __init__(self, bot):
        self.bot = bot

    @listen()
    async def on_startup(self):
        self.ping_db.start()
        self.upload_stats.start()
        self.status_change.start()
        self.clean_db.start()
        await self.clean_db()
        await self.status_change()

    @Task.create(IntervalTrigger(minutes=1))
    async def status_change(self):
        await self.bot.change_presence(
            Status.IDLE, get_random_presence(len(self.bot.guilds), self.bot.db)
        )

    @Task.create(IntervalTrigger(minutes=30))
    async def upload_stats(self):
        payload = {
            "server_count": len(self.bot.guilds),
        }
        headers = {
            "Authorization": str(topgg_token),
            "Content-Type": "application/json",
        }
        async with aiohttp.ClientSession() as session:
            await session.post(
                f"https://top.gg/api/bots/{self.bot.user.id}/stats",
                json=payload,
                headers=headers,
            )

    @Task.create(IntervalTrigger(seconds=30))
    async def ping_db(self):
        self.bot.db.ping()

    @Task.create(IntervalTrigger(minutes=30))
    async def clean_db(self):
        db_guilds = self.bot.db.guilds_with_stars()
        in_guilds = []
        for g in self.bot.guilds:
            try:
                in_guilds.append(g.id)
            except:
                continue

        for guild in db_guilds:
            if guild not in in_guilds:
                print(f"Removing guild {guild} from db")
                self.bot.db.remove_guild_and_data(guild)


def setup(bot):
    Tasks(bot)
