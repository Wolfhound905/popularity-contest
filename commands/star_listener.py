from os import remove
import re
from dis_snek.models import Scale
from dis_snek.models.discord_objects.embed import Embed
from dis_snek.models.discord_objects.message import Message
from dis_snek.models.discord_objects.sticker import StickerFormatTypes
from dis_snek.models.events.discord import MessageUpdate
from dis_snek.models.file import File
from dis_snek.models.listener import listen
from dis_snek.models.events import MessageReactionRemove
from utils.database import Database
from utils.models import Star
import aiohttp
import aiofiles
import pyrlottie


class ReactionListener(Scale):
    def __init__(self, bot):
        self.db: Database = self.bot.db
        self.bot = bot

    @listen()
    async def on_message_reaction_remove(self, event: MessageReactionRemove):
        if event.emoji.name not in ["⭐"]:
            return
        min_stars = self.db.min_stars(event.message.guild.id)
        if min_stars is None:
            return
        msg = event.message

        index = None
        for x, emoji in enumerate(msg.reactions):
            if emoji.emoji.name == "⭐":
                index = x
                break

        if index:
            emoji = msg.reactions[index]

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
            elif star and star.type == 1:
                await self.update_star_count("remove", event.author.id, star, 0, msg)

        elif emoji.count >= min_stars:
            star = self.db.check_existing(msg.id)
            if star and star.type in [0, 1]:
                """Update star count"""
                await self.update_star_count(
                    "remove", event.author.id, star, emoji.count, msg
                )

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
        if event.emoji.name not in ["⭐"]:
            return

        min_stars = self.db.min_stars(event.message.guild.id)
        if min_stars is None:
            return
        msg = event.message

        for x, emoji in enumerate(msg.reactions):
            if emoji.emoji.name == "⭐":
                index = x
                break

        emoji = msg.reactions[index]

        star = self.db.check_existing(msg.id)
        if star and star.type in [0, 1]:
            """Update star count"""
            await self.update_star_count("add", event.author.id, star, emoji.count, msg)

        elif emoji.count >= min_stars and msg.author.id != self.bot.user.id:
            star_channel = await self.bot.get_channel(
                self.db.get_star_channel(msg.guild.id)
            )

            embed = await self.embed_maker(msg)
            star_id = await star_channel.send(
                content=f"⭐ **{emoji.count}**", embeds=[embed]
            )
            star = self.db.add_star(
                star_id.id,
                msg.id,
                msg.channel.id,
                msg.guild.id,
                star_channel.id,
                event.author.id,
                emoji.count,
            )
            reactors = []
            for i in range(0, emoji.count, 100):
                thing = msg.reactions[index].users(
                    after=(reactors[-1] if reactors[-1:] else 0), limit=100
                )
                reactors.extend([user.id for user in await thing.fetch()])
            self.db.update_reactors(reactors, star)

    @listen("on_message_update")
    async def on_message_update(self, event: MessageUpdate):
        star = self.db.check_existing(event.after.id)
        if star and star.type == 0:
            x = self.db.get_update_edited_messages(event.after.guild.id)
            print(x)
            if x:
                channel = await self.bot.get_channel(star.star_channel_id)
                msg = await channel.get_message(star.star_id)
                embed = await self.embed_maker(event.after)
                await msg.edit(content=f"⭐ **{star.star_count}**", embeds=[embed])

    async def embed_maker(self, msg) -> Embed:
        # embed stuff ----------------
        embed = Embed(
            description=(msg.content if msg.content != "" else None),
            color="#FFAC32",
        )
        author = msg.author
        embed.set_author(name=author.tag, icon_url=author.avatar.url)
        referenced_msg = await msg.get_referenced_message()
        if referenced_msg:
            referenced_msg = f"| [Replied to..]({referenced_msg.jump_url})"
        else:
            referenced_msg = ""
        embed.add_field(
            name="\u200b",
            value=f"[Original Message]({msg.jump_url}) {referenced_msg}",
        )

        # Checking for embedable images
        link_regex = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"
        links = [x.group() for x in re.finditer(link_regex, msg.content, re.MULTILINE)]
        msg: Message
        if msg.attachments:
            for attachment in msg.attachments:
                if attachment.content_type.startswith("image"):
                    embed.set_image(url=attachment.url)
                    continue
        elif msg.sticker_items:
            sticker = msg.sticker_items[0]
            if sticker.format_type in [StickerFormatTypes.PNG, StickerFormatTypes.APNG]:
                base_url = "https://media.discordapp.net/stickers/{}.png?size=240"
                embed.set_image(url=base_url.format(sticker.id))

            elif sticker.format_type == StickerFormatTypes.LOTTIE:
                link = self.db.get_lottie(sticker.id)
                async with aiohttp.ClientSession() as session:
                    if link:
                        async with session.head(link) as resp:
                            if resp.status == 200:
                                embed.set_image(url=link)
                            else:
                                self.db.remove_lottie(sticker.id)
                                link = None
                    if link is None:
                        async with session.get(
                            f"https://discord.com/stickers/{sticker.id}.json"
                        ) as resp:
                            sticker_json = await resp.json()
                            async with aiofiles.open(
                                f"{sticker.id}.json", mode="wb"
                            ) as f:
                                await f.write(await resp.read())
                                await f.close()
                            lottie = pyrlottie.LottieFile(
                                f"{sticker.id}.json", sticker_json
                            )
                            await pyrlottie.convSingleLottie(
                                lottie,
                                set([f"{sticker.id}.gif"]),
                                backgroundColour="2f3136",
                                scale=0.6,
                            )
                            channel = await self.bot.get_channel(915287563009417216)
                            new_msg = await channel.send(file=File(f"{sticker.id}.gif"))
                            self.db.insert_lottie(
                                sticker.id, new_msg.attachments[0].url
                            )
                            embed.set_image(url=new_msg.attachments[0].url)
                            remove(f"{sticker.id}.json")
                            remove(f"{sticker.id}.gif")
        elif len(links) > 0:
            recieved_requests = []
            async with aiohttp.ClientSession() as session:
                for link in links:
                    async with session.head(link) as resp:
                        if resp.status == 200:
                            recieved_requests.append(resp)
            for req in recieved_requests:
                if req.content_type.startswith("image"):
                    embed.set_image(url=str(req.url))
                    break

        embed.timestamp = msg.timestamp
        return embed
        # -----------------------------

    async def update_star_count(
        self, _type: str, event_author: int, star: Star, new_count: int, msg
    ):
        """Update star count

        _type: "add" or "remove"
        """
        reactors = self.db.get_reactors(msg.id, star.type)
        # print("New count", new_count)
        # print("Star Type:", star.type)
        # print("Reactors", len(reactors))
        if len(reactors) + 1 == new_count and _type == "add":
            # print(star.type)
            self.db.add_reactor(event_author, star.message_id, star.star_id, star.type)
        elif len(reactors) - 1 == new_count or len(reactors) == 0 and _type == "remove":
            # print(star.type)
            self.db.remove_reactor(event_author, star.star_id, star.type)
        else:
            index = None
            for x, emoji in enumerate(msg.reactions):
                if emoji.emoji.name == "⭐":
                    index = x
                    break
            if index is None:
                return

            reactors = []
            print("This should not happen that much!")
            for i in range(0, new_count, 100):
                thing = msg.reactions[index].users(
                    after=(reactors[-1] if reactors[-1:] else 0), limit=100
                )
                reactors.extend([user.id for user in await thing.fetch()])

            self.db.update_reactors(reactors, star)

        total_reactors = len(self.db.get_reactors(msg.id))
        self.db.update_star(star.star_id, total_reactors)
        star_channel = await self.bot.get_channel(
            self.db.get_star_channel(star.guild_id)
        )
        original = await star_channel.get_message(star.star_id)
        if total_reactors in range(0, 7):
            await original.edit(content=f"⭐ **{total_reactors}**")
        elif total_reactors in range(7, 13):
            await original.edit(content=f"🌟 **{total_reactors}**")
        elif total_reactors in range(13, 17):
            await original.edit(content=f"✨ **{total_reactors}**")
        elif total_reactors in range(17, 24):
            await original.edit(content=f"💫 **{total_reactors}**")
        elif total_reactors > 23:
            await original.edit(content=f"🌠 **{total_reactors}**")


def setup(bot):
    ReactionListener(bot)
