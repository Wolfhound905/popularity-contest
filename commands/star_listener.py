from os import remove
import re
from typing import List


from dis_snek.api.events import (
    MessageReactionRemove,
    MessageDelete,
    MessageReactionAdd,
    MessageUpdate,
)

from dis_snek.models import (
    Embed,
    Message,
    StickerFormatTypes,
    Scale,
    File,
    listen,
)


from utils.database import Database
from utils.models import Star
import aiohttp
import aiofiles
import pyrlottie
from asyncio.exceptions import TimeoutError


class ReactionListener(Scale):
    def __init__(self, bot):
        self.bot = bot
        self.db: Database = self.bot.db

    @listen()
    async def on_message_reaction_remove(self, event: MessageReactionRemove):
        # print("Reaction removed")
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
            elif star and star.type == 1:
                await self.update_star_count(
                    "remove", event.author.id, star, emoji.count, msg
                )

    @listen()
    async def on_message_reaction_add(self, event: MessageReactionAdd):
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
            # lprint("Updating star count")
            await self.update_star_count("add", event.author.id, star, emoji.count, msg)

        elif emoji.count >= min_stars and msg.author.id != self.bot.user.id:
            # print("Creating star")
            star_channel = await self.bot.get_channel(
                self.db.get_star_channel(msg.guild.id)
            )

            embeds = await self.embed_maker(msg)
            star_id = await star_channel.send(
                content=f"⭐ **{emoji.count}**", embeds=embeds
            )
            star = self.db.add_star(
                star_id.id,
                msg.id,
                msg.channel.id,
                msg.guild.id,
                star_channel.id,
                msg.author.id,
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
            # print(x)
            if x:
                channel = await self.bot.get_channel(star.star_channel_id)
                msg = await channel.get_message(star.star_id)
                embeds = await self.embed_maker(event.after)
                await msg.edit(content=f"⭐ **{star.star_count}**", embeds=embeds)

    async def embed_maker(self, msg) -> List[Embed]:
        msg: Message

        # Filter Stuff ----------------------

        processed_message = msg.content
        msg_filter = self.db.get_filter(msg.guild.id)
        if msg_filter and msg_filter.enabled and msg_filter.filter_words:
            if msg_filter.mode == 0:
                for word in msg_filter.filter_words:
                    processed_message.replace(word, f"||{word}||")
            else:
                for word in msg_filter.filter_words:
                    if word in processed_message:
                        processed_message = processed_message.replace(word, "#!@$%^&*")

        # ----------------------------------

        # Checking for embedable images -----------------
        link_regex = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"
        og_image_regex = r"property=\"og:image\" content=\"(.*?)\""
        links = [x.group() for x in re.finditer(link_regex, msg.content, re.MULTILINE)]
        final_image_links = []
        if msg.attachments:
            for attachment in msg.attachments:
                if attachment.content_type.startswith("image"):
                    final_image_links.append(attachment.url)
                    continue
        elif msg.sticker_items:
            sticker = msg.sticker_items[0]
            if sticker.format_type in [StickerFormatTypes.PNG, StickerFormatTypes.APNG]:
                base_url = "https://media.discordapp.net/stickers/{}.png?size=240"
                final_image_links.append(base_url.format(sticker.id))

            elif sticker.format_type == StickerFormatTypes.LOTTIE:
                link = self.db.get_lottie(sticker.id)
                async with aiohttp.ClientSession() as session:
                    if link:
                        async with session.head(link) as resp:
                            if resp.status == 200:
                                final_image_links.append(link)
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
                            final_image_links = [new_msg.attachments[0].url]
                            remove(f"{sticker.id}.json")
                            remove(f"{sticker.id}.gif")
        elif len(links) > 0:
            timeout = timeout = aiohttp.ClientTimeout(total=0.5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                for link in list(set(links)):
                    try:
                        async with session.get(link) as response:
                            if response.status == 200:
                                if response.content_type.startswith("image"):
                                    final_image_links.append(str(link))
                                elif response.content_type == "text/html":
                                    og_image = re.search(
                                        og_image_regex,
                                        await response.text(),
                                        re.MULTILINE,
                                    )
                                    if og_image:
                                        link = str(og_image.group(1))
                                        if re.match(link_regex, link):
                                            final_image_links.append(link)
                            else:
                                continue
                    except TimeoutError:
                        print(f"Took too long to respond: {link}")
                        continue
                    except Exception as e:
                        print(f"Error: {e}")
                        continue
        # -------------------------------------------------

        # embed stuff ----------------
        embeds = []

        base_embed = Embed(
            description=(msg.content if msg.content != "" else None),
            url=f"https://top.gg/bot/{self.bot.user.id}/vote",
            color="#FFAC32",
        )
        base_embed.set_author(name=msg.author.tag, icon_url=msg.author.avatar.url)

        referenced_msg = await msg.get_referenced_message()
        if referenced_msg:
            referenced_msg = f"| [Replied to..]({referenced_msg.jump_url})"
        else:
            referenced_msg = ""

        base_embed.add_field(
            name="\u200b",
            value=f"[Original Message]({msg.jump_url}) {referenced_msg}",
        )

        embeds.append(base_embed)

        if len(final_image_links) > 1:

            base_embed.set_image(url=final_image_links[0])
            image_embeds = [
                Embed(url=f"https://top.gg/bot/{self.bot.user.id}/vote")
                for i in final_image_links[1:4]
            ]
            for embed, link in zip(image_embeds, final_image_links[1:4]):
                embed.set_image(url=link)
                embeds.append(embed)

        elif len(final_image_links) == 1:
            base_embed.set_image(url=final_image_links[0])
        # -----------------------------

        return embeds

    async def update_star_count(
        self, _type: str, event_author: int, star: Star, new_count: int, msg
    ):
        """Update star count

        _type: "add" or "remove"
        """
        reactors = self.db.get_reactors(msg.id, star_type=star.type)
        # print("New count", new_count)
        # print("Star Type:", star.type)
        # print("Reactors", len(reactors))
        if len(reactors) + 1 == new_count and _type == "add":
            # print(star.type)
            self.db.add_reactor(event_author, star.message_id, star.star_id, star.type)
        elif len(reactors) - 1 == new_count or len(reactors) == 0 and _type == "remove":
            # print("Removing")
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

        total_reactors = len(self.db.get_reactors(msg.id, True))
        # print("Total reactors:", total_reactors)
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

    @listen()
    async def on_message_delete(self, event: MessageDelete):

        star = self.db.check_existing(event.message.id)
        if star:
            self.db.remove_star(star.star_id)
            if star.type == 0:
                channel = await self.bot.get_channel(star.star_channel_id)
                star_message = await channel.get_message(star.star_id)
                await star_message.delete()


def setup(bot):
    ReactionListener(bot)
