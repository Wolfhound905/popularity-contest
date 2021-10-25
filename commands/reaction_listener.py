from dis_snek.models import Scale
from dis_snek.models.discord_objects.embed import Embed
from dis_snek.models.listener import listen
from utils.database import Database
from utils.models import Star
from utils.config import db_login
import pymysql


class ReactionListener(Scale):
    def __init__(self, bot):
        self.db = Database(pymysql.connect(**db_login))
        self.bot = bot

    @listen()
    async def on_message_reaction_remove(self, event):
        min_stars = self.db.min_stars(event.message.guild.id)
        if min_stars is None:
            return
        msg = event.message
        for emoji in msg.reactions:
            if emoji.emoji.name == "⭐" and emoji.count >= min_stars:
                star = self.db.check_existing(msg.id)
                if star:
                    """Update star count"""
                    await self.update_star_count(star, emoji.count)

            elif emoji.emoji.name == "⭐" and emoji.count < min_stars:
                """Remove star"""
                star = self.db.check_existing(msg.id)
                if star:
                    self.db.remove_star(star.star_id)
                    star_channel = await self.bot.get_channel(
                        self.db.get_star_channel(star.guild_id)
                    )
                    msg = await star_channel.get_message(star.star_id)
                    await msg.delete()

    @listen()
    async def on_message_reaction_add(self, event):
        min_stars = self.db.min_stars(event.message.guild.id)
        if min_stars is None:
            return
        msg = event.message
        for emoji in msg.reactions:
            if emoji.emoji.name == "⭐" and emoji.count >= min_stars:
                star = self.db.check_existing(msg.id)
                if star:
                    """Update star count"""
                    await self.update_star_count(star, emoji.count)

                else:
                    """Add star"""
                    embed = Embed(
                        description=(msg.content if msg.content != "" else None)
                    )
                    author = msg.author
                    embed.set_author(name=author.tag, icon_url=author.avatar.url)
                    referenced_msg = await msg.get_referenced_message()
                    if referenced_msg:
                        referenced_msg = f"| [Replied to..]({referenced_msg.jump_url})"
                    else:
                        referenced_msg = ""
                    embed.add_field(
                        name="──────",
                        value=f"[Original Message]({msg.jump_url}) {referenced_msg}",
                    )
                    for img in msg.attachments:
                        embed.set_image(url=img.url)
                    star_channel = await self.bot.get_channel(
                        self.db.get_star_channel(msg.guild.id)
                    )
                    star_id = await star_channel.send(
                        content=f"⭐ **{emoji.count}**", embeds=[embed]
                    )
                    self.db.add_star(
                        star_id.id, msg.id, msg.guild.id, author.id, emoji.count
                    )
                    break

    async def update_star_count(self, star: Star, new_count: int):
        self.db.update_star(star.star_id, new_count)
        star_channel = await self.bot.get_channel(
            self.db.get_star_channel(star.guild_id)
        )
        original = await star_channel.get_message(star.star_id)
        await original.edit(content=f"⭐ **{new_count}**")


def setup(bot):
    ReactionListener(bot)
