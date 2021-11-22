from types import NoneType
from typing import Any, List, Union
from pymysql.connections import Connection
from pymysql.cursors import Cursor
from utils.models import Star
from utils.errors import NoResults
from dis_snek.client import Snake




class Database:
    def __init__(self, con):
        self.__con: Connection = con
        self.__db: Cursor = self.__con.cursor()

    def ping(self) -> NoneType:
        """Pings the database and reconnects """
        self.__con.ping(True)
        return

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
        return Star(fetched, self.get_star_channel(fetched["guild_id"]), _id)

    def add_star(
        self,
        star_id: int,
        message_id: int,
        message_channel_id: int,
        guild_id: int,
        author_id: int,
        star_count: int,
    ) -> NoneType:
        """Adds a star to the starboard"""
        self.__db.execute(
            "INSERT INTO stars (star_id, message_id, message_channel_id, guild_id, author_id, star_count) VALUES (%s, %s, %s, %s, %s, %s);",
            (star_id, message_id, message_channel_id, guild_id, author_id, star_count),
        )
        return

    def update_reactors(self, reactors: list, star: Star) -> NoneType:
        """Updates the reactors for a star"""
        data = list((r, star.message_id, star.star_id, star.type) for r in reactors)
        self.__db.execute(
            """DELETE FROM star_reactors WHERE star_id = %s AND message_id = %s AND type = %s;""",
            (star.star_id, star.message_id, star.type),
        )
        self.__db.executemany(
            """INSERT INTO star_reactors (usr_id, message_id, star_id, type) VALUES (%s, %s, %s, %s);""",
            data,
        )
        return

    def add_reactor(
        self, reactor_id: int, message_id: int, star_id: int, type: int
    ) -> NoneType:
        """Adds a reactor to the starboard"""
        self.__db.execute(
            "INSERT INTO star_reactors (usr_id, message_id, star_id, type) VALUES (%s, %s, %s, %s);",
            (reactor_id, message_id, star_id, type),
        )
        return

    def remove_reactor(self, reactor_id: int, _id: int, _type: int) -> NoneType:
        """Removes a reactor from the starboard"""
        self.__db.execute(
            "DELETE FROM star_reactors WHERE usr_id = %s AND star_id = %s OR message_id = %s AND type = %s;",
            (reactor_id, _id, _id, _type),
        )
        return

    def get_reactor(self, reactor_id: int, _id: int):
        """Gets a star by its reactor ID"""
        self.__db.execute(
            "SELECT COUNT(*) FROM star_reactors WHERE usr_id = %s AND star_id = %s OR message_id = %s);",
            (reactor_id, _id, _id),
        )
        fetched = self.__db.fetchone()
        if fetched is None:
            return None
        return int(fetched["COUNT(*)"])

    def get_reactors(self, _id: int, _type: int = None) -> list:
        """Gets the reactors for a star"""
        if _type is not None:
            self.__db.execute(
                "SELECT usr_id FROM star_reactors WHERE star_id = %s OR message_id = %s AND type = %s;",
                (_id, _id, _type),
            )
        else:
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

    def get_global_stats(self) -> list:
        """Gets the global starboard stats"""
        self.__db.execute("SELECT SUM(star_count) AS star_total FROM stars")
        star_total = int(self.__db.fetchone()["star_total"])
        self.__db.execute("SELECT COUNT(*) as message_total FROM stars")
        message_total = self.__db.fetchone()["message_total"]
        return message_total, star_total

    def get_stars(self, guild_id: int) -> List["Star"]:
        """Gets all the stars for a guild

        Returns: list of Star class
        """
        self.__db.execute(
            "SELECT * FROM stars WHERE guild_id = %s ORDER BY star_count DESC;",
            (guild_id,),
        )
        stars = self.__db.fetchall()
        if len(stars) == 0:
            raise NoResults("No stars found")
        return [Star(s, self.get_star_channel(guild_id), s["star_id"]) for s in stars]

    def get_most_popular(self, guild_id: int) -> Union[list, int]:
        """Gets the most popular stars for a guild"""
        self.__db.execute(
            """SELECT * FROM popularity_contest.stars WHERE author_id = (
                    SELECT author_id
                    FROM popularity_contest.stars
                    WHERE guild_id = %s
                    GROUP BY author_id
                    ORDER BY SUM(star_count) DESC
                    LIMIT 1
                )
                AND guild_id = %s
                ORDER BY star_count DESC
            """,
            (guild_id, guild_id),
        )  # Gets all stars of author with most stars.
        fetched = self.__db.fetchall()
        if len(fetched) == 0:
            raise NoResults("No results found.")
        most_popular_user_stars = [
            Star(s, self.get_star_channel(guild_id), s["star_id"]) for s in fetched
        ]
        total_count = sum(s.star_count for s in most_popular_user_stars)
        return most_popular_user_stars, total_count

    def get_user_stats(self, guild_id: int, user_id: int) -> Union[list, int]:
        """Gets the stats for a user"""
        self.__db.execute(
            """SELECT * FROM popularity_contest.stars WHERE author_id = %s AND guild_id = %s ORDER BY star_count DESC;""",
            (user_id, guild_id),
        )
        fetched = self.__db.fetchall()
        if len(fetched) == 0:
            raise NoResults("No results found.")
        users_stars = [
            Star(s, self.get_star_channel(guild_id), s["star_id"]) for s in fetched
        ]
        total_count = sum(s.star_count for s in users_stars)
        return users_stars, total_count


# SELECT author_id
# FROM popularity_contest.stars
# WHERE guild_id = 838667622245597194
# GROUP BY author_id
# ORDER BY SUM(star_count) DESC
# LIMIT 1


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
