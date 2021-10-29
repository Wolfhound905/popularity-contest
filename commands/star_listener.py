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
        if event.emoji.name not in ["⭐"]: return
        min_stars = self.db.min_stars(event.message.guild.id)
        if min_stars is None:
            return
        msg = event.message

        index = None
        for x, emoji in enumerate(msg.reactions):
            if emoji.emoji.name == "⭐":
                index = x 
                break


        if index: emoji = msg.reactions[index]

        if index is None: 
            """Remove star"""
            star = self.db.check_existing(msg.id)
            if star and star.type == 0:
                self.db.remove_star(star.star_id)
                star_channel = await self.bot.get_channel(
                    self.db.get_star_channel(star.guild_id)
                )
                msg = await star_channel.get_message(star.star_id)
                await msg.delete()

        elif emoji.count >= min_stars:
            star = self.db.check_existing(msg.id)
            if star and star.type == 0:
                """Update star count"""
                await self.update_star_count("remove", event.author.id, star, emoji.count, msg)

        elif emoji.count < min_stars:
            """Remove star"""
            star = self.db.check_existing(msg.id)
            if star and star.type == 0:
                self.db.remove_star(star.star_id)
                star_channel = await self.bot.get_channel(
                    self.db.get_star_channel(star.guild_id)
                )
                msg = await star_channel.get_message(star.star_id)
                await msg.delete()

    @listen()
    async def on_message_reaction_add(self, event):
        if event.emoji.name not in ["⭐"]: return

        min_stars = self.db.min_stars(event.message.guild.id)
        if min_stars is None: return
        msg = event.message

        for x, emoji in enumerate(msg.reactions):
            if emoji.emoji.name == "⭐":
                index = x 
                break

        emoji = msg.reactions[index]
        
        star = self.db.check_existing(msg.id)
        if star and star.type == 0:
            """Update star count"""
            await self.update_star_count("add", event.author.id, star, emoji.count, msg)

        elif emoji.count >= min_stars and msg.author.id != self.bot.user.id:
            # embed stuff ----------------
            embed = Embed(
                description=(msg.content if msg.content != "" else None),
                color="#FFAC32"
            
            )
            author = msg.author
            embed.set_author(name=author.tag, icon_url=author.avatar.url)
            referenced_msg = await msg.get_referenced_message()
            if referenced_msg:
                referenced_msg = f"| [Replied to..]({referenced_msg.jump_url})"
            else:
                referenced_msg = ""
            embed.add_field(
                name=u"\u200b",
                value=f"[Original Message]({msg.jump_url}) {referenced_msg}",
            )
            if msg.attachments:
                for attachment in msg.attachments:
                    if attachment.content_type.startswith("image"):
                        embed.set_image(url=attachment.url)


            

            embed.timestamp = msg.timestamp
            # -----------------------------

            star_channel = await self.bot.get_channel(
                self.db.get_star_channel(msg.guild.id)
            )
            star_id = await star_channel.send(
                content=f"⭐ **{emoji.count}**", embeds=[embed]
            )
            self.db.add_star(
                star_id.id, msg.id, msg.guild.id, author.id, emoji.count
            )
            reactors = []
            for i in range(0, emoji.count, 100):
                thing = msg.reactions[index].users(after=(reactors[-1] if reactors[-1:] else 0), limit=100)
                reactors.extend([user.id for user in await thing.fetch()])
            self.db.update_reactors(reactors, msg.id, star_id.id)
                

    async def update_star_count(self, _type:str, event_author:int, star: Star, new_count: int, msg):
        """ Update star count
        
        _type: "add" or "remove"
         """
        reactors = self.db.get_reactors(msg.id)
        if len(reactors) + 1 == new_count and _type == "add":
            ...
        elif len(reactors)  == new_count and _type == "remove":
            self.db.remove_reactor(event_author, star.star_id)
        else:
            index = None
            for x, emoji in enumerate(msg.reactions):
                if emoji.emoji.name == "⭐":
                    index = x 
                    break
            if index is None: return

            reactors = []
            for i in range(0, new_count, 100):
                thing = msg.reactions[index].users(after=(reactors[-1] if reactors[-1:] else 0), limit=100)
                reactors.extend([user.id for user in await thing.fetch()])

            self.db.update_reactors(reactors, star.message_id, star.star_id)

                    
        self.db.update_star(star.star_id, new_count)
        star_channel = await self.bot.get_channel(
            self.db.get_star_channel(star.guild_id)
        )
        original = await star_channel.get_message(star.star_id)
        match new_count:
            case new_count if new_count in range(0, 7):
                await original.edit(content=f"⭐ **{new_count}**")
            case new_count if new_count in range(7, 13):
                await original.edit(content=f"🌟 **{new_count}**")
            case new_count if new_count in range(13, 17):
                await original.edit(content=f"✨ **{new_count}**")
            case new_count if new_count in range(17, 24):
                await original.edit(content=f"💫 **{new_count}**")
            case new_count if new_count > 23:
                await original.edit(content=f"🌠 **{new_count}**")       


def setup(bot):
    ReactionListener(bot)
