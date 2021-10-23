from sqlite3.dbapi2 import OperationalError
from dis_snek.client import Snake
from dis_snek.models.application_commands import slash_command
from dis_snek.models.listener import listen
from dotenv import load_dotenv
from os import environ
import sqlite3

bot = Snake(sync_interactions=True)
load_dotenv()

# Setup
con = sqlite3.connect("./stars.db")
db = con.cursor() # Check is there are any table
db.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = list(map(lambda x: x[0], db.fetchall()))
if ["stars", "configuration"] not in tables:  # Create the table
    if "stars" not in tables:
        db.execute("CREATE TABLE stars (message_id, author, stars)")
    if "configuration" not in tables:
        db.execute("CREATE TABLE configuration (server_id, channel, min_star_count)")
    

@listen()
async def on_ready():
    print(f"Logged in as: {bot.user}")


@listen()
async def on_message_update(event):
    print(event)

@listen()
async def on_message_reaction_add(event):
    print(event.author)


bot.start(environ["TOKEN"])



class DataBase:
    class configure:
        def set_channel(server_id:int, channel_id:int):
            db.execute(f"INSERT INTO configuration (server_id, channel) VALUES ({server_id}, {channel_id});")
            con.commit()
            return
        def set_min_stars(server_id:int, star_count:int):
            db.execute(f"INSERT INTO configuration (server_id, min_star_count) VALUES ({server_id}, {star_count});")
            con.commit()
            return
        
    

