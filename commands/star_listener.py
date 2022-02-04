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
    MessageTypes,
    Timestamp,
)


from utils.database import Database
from utils.models import Star
import aiohttp
import aiofiles
import pyrlottie
from asyncio.exceptions import TimeoutError
from apnggif import apnggif


class ReactionListener(Scale):
    def __init__(self, bot):
        self.bot = bot
        self.db: Database = self.bot.db

    @listen()
    async def on_message_reaction_remove(self, event: MessageReactionRemove):
        if event.emoji.name != "⭐":
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
        if event.author.id == self.bot.user.id:
            return
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
            await star_id.add_reaction("⭐")
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

    async def embed_maker(self, msg: Message) -> List[Embed]:

        # Filter Stuff ----------------------

        processed_message = msg.content
        msg_filter = self.db.get_filter(msg.guild.id)
        if msg_filter and msg_filter.enabled and msg_filter.filter_words:
            if msg_filter.mode == 0:

                processed_message = processed_message.split()
                for i, word in enumerate(processed_message):
                    for filter_word in msg_filter.filter_words:
                        if re.search(filter_word, word):
                            processed_message[i] = f"|| {word} ||"

                processed_message = " ".join(processed_message)
            else:
                processed_message = processed_message.split()
                for i, word in enumerate(processed_message):
                    for filter_word in msg_filter.filter_words:
                        if re.search(filter_word, word):
                            processed_message[i] = "#!@$%^&*"[0 : len(word)]

                processed_message = " ".join(processed_message)
            if processed_message != msg.content:
                if msg_filter.mode == 0:
                    processed_message = (
                        "*Some words hidden due to filter*\n\n" + processed_message
                    )
                else:
                    processed_message = (
                        "*Some words replaced due to filter*\n\n" + processed_message
                    )

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
            if sticker.format_type == StickerFormatTypes.PNG:
                base_url = "https://media.discordapp.net/stickers/{}.png?size=240"
                final_image_links.append(base_url.format(sticker.id))

            elif sticker.format_type == StickerFormatTypes.APNG:
                link = self.db.get_animated_sticker(sticker.id)
                async with aiohttp.ClientSession() as session:
                    if link:
                        async with session.head(link) as resp:
                            if resp.status == 200:
                                final_image_links.append(link)
                            else:
                                self.db.remove_animated_sticker(sticker.id)
                                link = None
                    if link is None:
                        async with session.get(
                            f"https://media.discordapp.net/stickers/{sticker.id}.png?size=64&passthrough=true"
                        ) as resp:
                            async with aiofiles.open(
                                f"{sticker.id}.png", mode="wb"
                            ) as f:
                                await f.write(await resp.read())
                                await f.close()
                            apnggif(f"{sticker.id}.png")
                            channel = await self.bot.get_channel(915287563009417216)
                            new_msg = await channel.send(file=File(f"{sticker.id}.gif"))
                            self.db.insert_animated_sticker(
                                sticker.id, new_msg.attachments[0].url
                            )
                            final_image_links = [new_msg.attachments[0].url]
                            remove(f"{sticker.id}.png")
                            remove(f"{sticker.id}.gif")

            elif sticker.format_type == StickerFormatTypes.LOTTIE:
                link = self.db.get_animated_sticker(sticker.id)
                async with aiohttp.ClientSession() as session:
                    if link:
                        async with session.head(link) as resp:
                            if resp.status == 200:
                                final_image_links.append(link)
                            else:
                                self.db.remove_animated_sticker(sticker.id)
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
                            self.db.insert_animated_sticker(
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

        description = None

        match msg.type:
            case MessageTypes.USER_PREMIUM_GUILD_SUBSCRIPTION:
                description = f"{msg.author.mention} just boosted the server!"
            case MessageTypes.USER_PREMIUM_GUILD_SUBSCRIPTION_TIER_1:
                description = f"{msg.author.mention} just boosted the server! {msg.guild.name} has acheived **Level 1!**"
            case MessageTypes.USER_PREMIUM_GUILD_SUBSCRIPTION_TIER_2:
                description = f"{msg.author.mention} just boosted the server! {msg.guild.name} has acheived **Level 2!**"
            case MessageTypes.USER_PREMIUM_GUILD_SUBSCRIPTION_TIER_3:
                description = f"{msg.author.mention} just boosted the server! {msg.guild.name} has acheived **Level 3!**"
            case MessageTypes.GUILD_MEMBER_JOIN:
                welcome_message_template = [
                    "{0} joined the party.",
                    "{0} is here.",
                    "Welcome, {0}. We hope you brought pizza.",
                    "A wild {0} appeared.",
                    "{0} just landed.",
                    "{0} just slid into the server.",
                    "{0} just showed up!",
                    "Welcome {0}. Say hi!",
                    "{0} hopped into the server.",
                    "Everyone welcome {0}!",
                    "Glad you're here, {0}.",
                    "Good to see you, {0}.",
                    "Yay you made it, {0}!",
                ]
                created_at = int(msg.timestamp.timestamp() * 1000)

                description = welcome_message_template[
                    created_at % len(welcome_message_template)
                ].format(msg.author.mention)

        if msg.content != "" and description is None:
            description = processed_message

        base_embed = Embed(
            description=description,
            url=f"https://top.gg/bot/{self.bot.user.id}/vote",
            color="#FFAC32",
            timestamp=Timestamp.from_snowflake(msg.id),
        )
        base_embed.set_author(name=msg.author.tag, icon_url=msg.author.avatar.url)

        if msg.embeds:
            for embed in msg.embeds:
                print(embed)
                print(len(embed))
            try:
                for embed in msg.embeds:
                    embed: Embed
                    if embed.title and embed.description:
                        print(embed.description)
                        base_embed.add_field(embed.title, embed.description[0:1024])
                    elif not embed.title and embed.description:
                        print(embed.description)
                        base_embed.add_field("\u200b", embed.description[0:1024])

                    if embed.image:
                        final_image_links.append(embed.image.url["url"])

                    for feild in embed.fields:
                        base_embed.add_field(feild.name, feild.value, feild.inline)
            except Exception as e:
                print(e)
                pass

        referenced_msg = await msg.get_referenced_message()
        if referenced_msg:
            referenced_msg = f"| [Replied to..]({referenced_msg.jump_url})"
        else:
            referenced_msg = ""

        base_embed.add_field(
            name="\u200b",
            value=f"[Original Message]({msg.jump_url}) {referenced_msg}",
        )

        base_embed.set_footer("#" + msg.channel.name)

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
        index = None
        for x, emoji in enumerate(msg.reactions):
            if emoji.emoji.name == "⭐":
                index = x
                break
        if _type == "add" and star.type == 1:
            if index is not None:
                if msg.reactions[index].me:
                    new_count -= 1
            while self.bot.user.id in reactors:
                reactors.remove(self.bot.user.id)

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
