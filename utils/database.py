from types import NoneType
from typing import Any, Union
from pymysql.connections import Connection
from pymysql.cursors import Cursor
from utils.models import Star
from dis_snek.client import Snake


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

    def min_stars(self, guild_id: int) -> Union[int, None]:
        self.__db.execute(
            "SELECT min_star_count FROM configuration WHERE guild_id = %s;", (guild_id,)
        )
        fetched = self.__db.fetchone()
        if fetched is None:
            return None
        return int(fetched["min_star_count"])

    def get_star_channel(self, guild_id: int) -> Union[int, NoneType]:
        """Gets the starboard channel ID"""
        self.__db.execute(
            "SELECT star_channel FROM configuration WHERE guild_id = %s;", (guild_id,)
        )
        return self.__db.fetchone()["star_channel"]

    def check_existing(self, _id: int) -> Union[Star, None]:
        """Checks for existing star in the starboard"""
        self.__db.execute(
            "SELECT * FROM stars WHERE star_id = %s OR message_id = %s;", (_id, _id)
        )
        fetched = self.__db.fetchone()
        if fetched is None:
            return None
        return Star(fetched, _id)

    def add_star(
        self,
        star_id: int,
        message_id: int,
        guild_id: int,
        author_id: int,
        star_count: int,
    ) -> NoneType:
        """Adds a star to the starboard"""
        self.__db.execute(
            "INSERT INTO stars (star_id, message_id, guild_id, author_id, star_count) VALUES (%s, %s, %s, %s, %s);",
            (star_id, message_id, guild_id, author_id, star_count),
        )
        return

    def update_reactors(
        self, reactors: list, message_id: int, star_id: int
    ) -> NoneType:
        """Updates the reactors for a star"""
        data = list((r, message_id, star_id) for r in reactors)
        self.__db.execute(
            """DELETE FROM star_reactors WHERE star_id = %s AND message_id = %s;""", (star_id, message_id)
        )
        self.__db.executemany(
            """INSERT INTO star_reactors (usr_id, message_id, star_id) VALUES (%s, %s, %s);""", data
        )
        return

    def remove_reactor(self, reactor_id: int, _id: int) -> NoneType:
        """Removes a reactor from the starboard"""
        self.__db.execute(
            "DELETE FROM star_reactors WHERE usr_id = %s AND star_id = %s OR message_id = %s;", (reactor_id, _id, _id)
        )
        return

    def get_reactors(self, _id: int) -> list:
        """Gets the reactors for a star"""
        self.__db.execute(
            "SELECT usr_id FROM star_reactors WHERE star_id = %s OR message_id = %s;",
            (_id, _id),
        )
        reactors = self.__db.fetchall()
        return [r["usr_id"] for r in reactors]

    def update_star(self, star_id: int, star_count: int) -> NoneType:
        """Updates the star count"""
        self.__db.execute(
            "UPDATE stars SET star_count = %s WHERE star_id = %s;",
            (star_count, star_id),
        )
        return

    def remove_star(self, star_id: int) -> NoneType:
        """Removes a star from the starboard"""
        self.__db.execute("DELETE FROM star_reactors WHERE star_id = %s;", (star_id,))
        self.__db.execute("DELETE FROM stars WHERE star_id = %s;", (star_id,))
        return

    def get_stars(self, guild_id: int) -> list:
        """Gets all the stars for a guild"""
        self.__db.execute(
            "SELECT * FROM stars WHERE guild_id = %s ORDER BY star_count DESC;", (guild_id,)
        )
        stars = self.__db.fetchall()
        return [Star(s, s["star_id"]) for s in stars]
        


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
