from os import environ
from dis_snek.errors import Forbidden
from dis_snek.models import events
from dis_snek.models.discord_objects.channel import (
    GuildPrivateThread,
    GuildPublicThread,
    GuildText,
    ThreadChannel,
)
from dis_snek.models.discord_objects.message import Message, process_allowed_mentions

import pymysql
from dis_snek.client import Snake
from dis_snek.models.application_commands import (
    OptionTypes,
    slash_command,
    slash_option,
)
from dis_snek.models.context import InteractionContext, MessageContext
from dis_snek.models.discord_objects.embed import Embed
from dis_snek.models.listener import listen
from dotenv import load_dotenv

from utils.database import Database
from utils.models import Star

load_dotenv()

db = Database(
    pymysql.connect(
        host=environ["HOST"],
        user=environ["USER"],
        password=environ["PASSWORD"],
        database=environ["DATABASE"],
        charset="utf8mb4",
        port=int(environ["PORT"]),
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor,
    )
)

bot = Snake(sync_interactions=False, delete_unused_application_cmds=False)


@listen()
async def on_ready():
    print(f"Logged in as: {bot.user}")


@slash_command("setup", "Setup the Starboard channel and minumum star count")
@slash_option(
    "channel", "The channel to starboard messages to", OptionTypes.CHANNEL, True
)
@slash_option(
    "min_star_count",
    "The minimum amount of stars to star a message",
    OptionTypes.INTEGER,
)
async def setup(ctx: InteractionContext, channel, min_star_count: int = 4):
    if type(channel) not in [GuildPrivateThread, GuildPublicThread, GuildText]:
        error = Embed(
            title="Error",
            description="Channel must be a text channel",
            color="#EB4049",
        )
        await ctx.send(embeds=[error])
        return
    if min_star_count < 1:
        error = Embed(
            title="Error",
            description="Minimum star count must be greater than 0",
            color="#EB4049",
        )
        await ctx.send(embeds=[error])
        return
    try:
        tmp_msg = await channel.send(".")
        await tmp_msg.delete()
    except Forbidden:
        error = Embed(
            title="Error",
            description="I don't have permission to send messages in this channel",
            color="#EB4049",
        )
        await ctx.send(embeds=[error])
        return

    db.setup(ctx.guild.id, channel.id, min_star_count)
    embed = Embed(
        "⭐ Setup Complete!",
        f"Posting to {channel.mention} with a minimum star count of {min_star_count}",
        color="#F9AC42",
    )
    await ctx.send(embeds=[embed])


@listen()
async def on_message_reaction_remove(event):
    min_stars = db.min_stars(event.message.guild.id)
    msg = event.message
    for emoji in msg.reactions:
        if emoji.emoji["name"] == "⭐" and emoji.count >= min_stars:
            star = db.check_existing(msg.id)
            if star:
                """Update star count"""
                await update_star_count(star, emoji.count)

        elif emoji.emoji["name"] == "⭐" and emoji.count < min_stars:
            ...
            # """Remove star"""
            # star = db.check_existing(msg.id)
            # if star:
            #     db.remove_star(star.star_id)
            #     star_channel = await bot.get_channel(

@listen()
async def on_message_reaction_add(event):
    min_stars = db.min_stars(event.message.guild.id)
    msg = event.message
    for emoji in msg.reactions:
        if emoji.emoji["name"] == "⭐" and emoji.count >= min_stars:
            star = db.check_existing(msg.id)
            if star:
                """Update star count"""
                await update_star_count(star, emoji.count)
                
            else:
                """Add star"""
                embed = Embed(description=(msg.content if msg.content != "" else None))
                author = msg.author
                embed.set_author(name=author.tag, icon_url=author.avatar.url)
                referenced_msg = await msg.get_referenced_message()
                if referenced_msg:
                    referenced_msg = f"| [Replied to..]({referenced_msg.jump_url})"
                else:
                    referenced_msg = ""
                embed.add_field(name="──────", value=f"[Original Message]({msg.jump_url}) {referenced_msg}")
                for img in msg.attachments:
                    embed.set_image(url=img.url)
                star_channel = await bot.get_channel(db.get_star_channel(msg.guild.id))
                star_id = await star_channel.send(
                    content=f"⭐ **{emoji.count}**",
                    embeds=[embed]
                )
                db.add_star(star_id.id, msg.id, msg.guild.id, author.id, emoji.count)
                break

async def update_star_count(star: Star, new_count: int):
    db.update_star(star.star_id, new_count)
    star_channel = await bot.get_channel(db.get_star_channel(star.guild_id))
    original = await star_channel.get_message(star.star_id)
    await original.edit(content=f"⭐ **{new_count}**")



bot.start(environ["TOKEN"])


