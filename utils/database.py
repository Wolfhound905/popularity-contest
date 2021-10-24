from types import NoneType
from typing import Any, Union
from pymysql.connections import Connection
from pymysql.cursors import Cursor
from utils.models import Star


class Database:
    def __init__(self, con):
        self.__con: Connection = con
        self.__db: Cursor = self.__con.cursor()

    def setup(self, guild_id: int, channel_id: int, star_count: int) -> NoneType:
        self.__db.execute(
            "REPLACE INTO configuration (guild_id, star_channel, min_star_count) VALUES (%s, %s, %s);",
            (guild_id, channel_id, star_count),
        )
        return
    def min_stars(self, guild_id:int) -> int:
        self.__db.execute(
            "SELECT min_star_count FROM configuration WHERE guild_id = %s;", (guild_id,)
        )
        return int(self.__db.fetchone()["min_star_count"])

    def get_star_channel(self, guild_id:int) -> Union[int, NoneType]:
        """ Gets the starboard channel ID """
        self.__db.execute(
            "SELECT star_channel FROM configuration WHERE guild_id = %s;", (guild_id,)
        )
        return self.__db.fetchone()["star_channel"]

    def check_existing(self, message_id:int) -> Union[Star, None]:
        """ Checks for existing star in the starboard """
        self.__db.execute(
            "SELECT * FROM stars WHERE message_id = %s;", (message_id,)
        )
        fetched = self.__db.fetchone()
        if fetched is None:
            return None
        return Star(fetched)
    
    def add_star(self, star_id:int, message_id:int, guild_id:int, author_id:int, star_count:int) -> NoneType:
        """ Adds a star to the starboard """
        self.__db.execute(
            "INSERT INTO stars (star_id, message_id, guild_id, author_id, star_count) VALUES (%s, %s, %s, %s, %s);", (star_id, message_id, guild_id, author_id, star_count)
        )
        return

    def update_star(self, star_id:int, star_count:int) -> NoneType:
        """ Updates the star count """
        self.__db.execute(
            "UPDATE stars SET star_count = %s WHERE star_id = %s;", (star_count, star_id)
        )
        return




# here is the table structure for you self hosters

# CREATE TABLE popularity_contest.stars (
# 	star_id varchar(100) NOT NULL,
# 	message_id varchar(100) NOT NULL COMMENT 'ID of the stared message.',
# 	author_id varchar(100) NULL,
# 	star_count INT NOT NULL,
# 	CONSTRAINT stars_PK PRIMARY KEY (message_id)
# )
# ENGINE=InnoDB
# DEFAULT CHARSET=utf8mb4
# COLLATE=utf8mb4_bin
# COMMENT='Data for the stars across servers.';

# CREATE TABLE popularity_contest.configuration (
# 	guild_id varchar(100) NOT NULL,
# 	star_channel varchar(100) NOT NULL,
# 	min_star_count varchar(100) NOT NULL,
# 	CONSTRAINT configuration_PK PRIMARY KEY (guild_id)
# )
# ENGINE=InnoDB
# DEFAULT CHARSET=utf8mb4
# COLLATE=utf8mb4_0900_ai_ci
# COMMENT='guild configurations';
