from dis_snek import (
    Status,
    listen,
    Task,
)
from dis_snek.ext.tasks.triggers import IntervalTrigger

from utils.misc import get_random_presence
from utils.config import topgg_token
from dis_snek.models import Scale
import aiohttp


class Tasks(Scale):
    def __init__(self, bot):
        self.bot = bot

    @listen()
    async def on_ready(self):
        self.upload_stats.start()
        self.status_change.start()
        self.ping_db.start()
        await self.status_change()
        await self.upload_stats()

    @Task.create(IntervalTrigger(seconds=30))
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


def setup(bot):
    Tasks(bot)
