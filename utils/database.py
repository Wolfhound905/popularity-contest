from types import NoneType
from typing import Any, List, Optional, Union
from pymysql.connections import Connection
from pymysql.cursors import Cursor
from utils.models import Filter, Star
from utils.errors import NoResults
from dis_snek.client import Snake
from json import dumps, loads


class Database:
    def __init__(self, con):
        self.__con: Connection = con
        self.__db: Cursor = self.__con.cursor()

    def ping(self) -> NoneType:
        """Pings the database and reconnects"""
        self.__con.ping(True)
        return

    def guilds_with_stars(self) -> List[int]:
        """Get a list of guild ids"""
        self.__db.execute("SELECT DISTINCT guild_id FROM stars;")
        return [int(x["guild_id"]) for x in self.__db.fetchall()]

    def setup(
        self,
        guild_id: int,
        channel_id: int,
        star_count: int,
        update_edited_messages: bool,
    ) -> NoneType:
        self.__db.execute(
            "REPLACE INTO configuration (guild_id, star_channel, min_star_count, update_edited_messages) VALUES (%s, %s, %s, %s);",
            (guild_id, channel_id, star_count, update_edited_messages),
        )
        return

    def edit_config(self, guild_id: int, column: str, value) -> NoneType:
        """Edits the configuration of the guild"""
        self.__db.execute(
            "UPDATE configuration SET update_edited_messages = %s WHERE guild_id = %s;",
            (value, guild_id),
        )
        return

    def get_update_edited_messages(self, guild_id: int) -> Union[bool, None]:
        """Gets the update edited messages setting"""
        self.__db.execute(
            "SELECT update_edited_messages FROM configuration WHERE guild_id = %s;",
            (guild_id,),
        )
        return self.__db.fetchone()["update_edited_messages"]

    def get_config_value(self, guild_id: int, column: str) -> Union[Any, None]:
        """Gets a configuration value"""

        self.__db.execute(
            "SELECT %s FROM configuration WHERE guild_id = %s;", (column, guild_id)
        )
        fetched = self.__db.fetchone()
        if fetched is None:
            return None
        return fetched[column]

    def min_stars(self, guild_id: int) -> Union[int, None]:
        self.__db.execute(
            "SELECT min_star_count FROM configuration WHERE guild_id = %s;", (guild_id,)
        )
        fetched = self.__db.fetchone()
        if fetched is None:
            return None
        return int(fetched["min_star_count"])

    def get_star_channel(self, guild_id: int) -> Union[int, None]:
        """Gets the starboard channel ID"""
        self.__db.execute(
            "SELECT star_channel FROM configuration WHERE guild_id = %s;", (guild_id,)
        )
        x = self.__db.fetchone()
        if x is None:
            return None
        else:
            return x["star_channel"]

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
        star_channel: int,
        author_id: int,
        star_count: int,
    ) -> Star:
        """Adds a star to the starboard"""
        self.__db.execute(
            "INSERT INTO stars (star_id, message_id, message_channel_id, guild_id, author_id, star_count) VALUES (%s, %s, %s, %s, %s, %s);",
            (star_id, message_id, message_channel_id, guild_id, author_id, star_count),
        )
        return Star(
            {
                "star_id": star_id,
                "message_id": message_id,
                "guild_id": guild_id,
                "author_id": author_id,
                "star_count": star_count,
                "message_channel_id": message_channel_id,
            },
            star_channel,
            message_id,
        )

    def update_reactors(self, reactors: list, star: Star) -> NoneType:
        """Updates the reactors for a star"""
        # print("Updating Reactors")
        data = list((r, star.message_id, star.star_id, star.type) for r in reactors)
        self.__db.execute(
            """DELETE FROM star_reactors WHERE star_id = %s AND message_id = %s AND type = %s;""",
            (star.star_id, star.message_id, star.type),
        )
        self.__db.executemany(
            """REPLACE INTO star_reactors (usr_id, message_id, star_id, type) VALUES (%s, %s, %s, %s);""",
            data,
        )
        return

    def add_reactor(
        self, reactor_id: int, message_id: int, star_id: int, type: int
    ) -> NoneType:
        """Adds a reactor to the starboard"""
        # print("Adding Reactor")
        self.__db.execute(
            "INSERT INTO star_reactors (usr_id, message_id, star_id, type) VALUES (%s, %s, %s, %s);",
            (reactor_id, message_id, star_id, type),
        )
        return

    def remove_reactor(self, reactor_id: int, _id: int, _type: int) -> NoneType:
        """Removes a reactor from the starboard"""
        # print("Removing Reactor")
        self.__db.execute(
            "DELETE FROM star_reactors WHERE usr_id = %s AND (star_id = %s OR message_id = %s) AND type = %s;",
            (reactor_id, _id, _id, _type),
        )
        return

    def remove_reactor_by_id(self, _id: int) -> NoneType:
        """Removes a reactor from the starboard"""
        # print("Removing Reactor")
        self.__db.execute(
            "DELETE FROM star_reactors WHERE (star_id = %s OR message_id = %s)",
            (_id, _id),
        )
        return

    def get_reactor(self, reactor_id: int, _id: int):
        """Gets a star by its reactor ID"""
        # print("Getting Reactor")
        self.__db.execute(
            "SELECT COUNT(*) FROM star_reactors WHERE usr_id = %s AND (star_id = %s OR message_id = %s);",
            (reactor_id, _id, _id),
        )
        fetched = self.__db.fetchone()
        if fetched is None:
            return None
        return int(fetched["COUNT(*)"])

    def get_reactors(
        self, _id: int, distinct: bool = False, star_type: int = None
    ) -> list:
        """Gets the reactors for a star"""
        print("Getting Reactors", star_type)
        if star_type is not None:
            self.__db.execute(
                "SELECT usr_id FROM star_reactors WHERE (star_id = %s OR message_id = %s) AND type = %s;",
                (_id, _id, star_type),
            )
        elif distinct:
            self.__db.execute(
                "SELECT DISTINCT usr_id FROM star_reactors WHERE star_id = %s OR message_id = %s;",
                (_id, _id),
            )
        else:
            self.__db.execute(
                "SELECT usr_id FROM star_reactors WHERE star_id = %s OR message_id = %s;",
                (_id, _id),
            )
        reactors = self.__db.fetchall()
        reactors = [r["usr_id"] for r in reactors]
        while 900353078128173097 in reactors:
            reactors.remove(900353078128173097)
        return reactors

    def update_star(self, star_id: int, star_count: int) -> NoneType:
        """Updates the star count"""
        # print("Updating Star")
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

    def get_stars(
        self, guild_id: int = None, get_star_channel: bool = True
    ) -> List["Star"]:
        """Gets all the stars for a guild

        Returns: list of Star class
        """
        if guild_id is None:
            self.__db.execute("SELECT * FROM stars ORDER BY star_count DESC;")
        else:
            self.__db.execute(
                "SELECT * FROM stars WHERE guild_id = %s ORDER BY star_count DESC;",
                (guild_id,),
            )
        stars = self.__db.fetchall()
        if len(stars) == 0:
            raise NoResults("No stars found")
        if guild_id:
            star_channel = self.get_star_channel(guild_id) if get_star_channel else 0
            if star_channel is None:
                star_channel = 0
            return [Star(s, star_channel, s["star_id"]) for s in stars]
        else:
            return [
                Star(s, self.get_star_channel(s["guild_id"]), s["star_id"])
                for s in stars
            ]

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
        star_channel = self.get_star_channel(guild_id)
        users_stars = [Star(s, star_channel, s["star_id"]) for s in fetched]
        total_count = sum(s.star_count for s in users_stars)
        return users_stars, total_count

    # animated_sticker extra stuff
    def get_animated_sticker(self, sticker_id) -> str | None:
        """Gets the animated_sticker url"""
        self.__db.execute(
            "SELECT gif_link FROM animated_sticker_gifs WHERE sticker_id = %s",
            (sticker_id,),
        )
        fetched = self.__db.fetchone()
        if fetched is None:
            return None
        return fetched["gif_link"]

    def insert_animated_sticker(self, sticker_id, url) -> None:
        """Inserts a animated_sticker url"""
        self.__db.execute(
            "INSERT INTO animated_sticker_gifs (sticker_id, gif_link) VALUES (%s, %s)",
            (sticker_id, url),
        )
        return

    def remove_animated_sticker(self, sticker_id) -> None:
        """Removes a animated_sticker url"""
        self.__db.execute(
            "DELETE FROM animated_sticker_gifs WHERE sticker_id = %s", (sticker_id,)
        )
        return

    def get_filter(self, guild_id: int) -> Filter | None:
        """Gets the filter for a guild"""
        self.__db.execute("SELECT * FROM filters WHERE guild_id = %s", (guild_id,))
        fetched = self.__db.fetchone()
        if fetched and fetched.get("guild_id"):
            return Filter(fetched)
        return None

    def insert_filter(
        self,
        guild_id: int,
        filter_list: list,
        commit_mode: 1 | 2,
        filter_mode: int = None,
    ) -> Optional[Filter]:
        """Inserts a filter into the database

        Args:
            filter_list (list): The list of filters to insert
            commit_mode (int): The commit_mode of the filter
                1: Overwrite
                2: Append/Merge
        """
        if not self.get_filter(guild_id):
            self.__db.execute(
                "INSERT INTO filters (guild_id, filter_words) VALUES (%s, %s)",
                (guild_id, "[]"),
            )

        if filter_mode is not None:
            self.__db.execute(
                "UPDATE filters SET mode = %s WHERE guild_id = %s",
                (filter_mode, guild_id),
            )

        filter_list = list(set(filter_list))
        if commit_mode == 1:
            # "UPDATE configuration SET update_edited_messages = %s WHERE guild_id = %s;",
            self.__db.execute(
                "UPDATE filters SET filter_words = %s WHERE guild_id = %s",
                (dumps(filter_list), guild_id),
            )
        elif commit_mode == 2:
            filter = self.get_filter(guild_id)

            if filter:
                existing_filter_words = filter.filter_words
                new_filter = list(
                    set(
                        existing_filter_words + filter_list
                        if existing_filter_words
                        else [] + filter_list
                    )
                )
            else:
                new_filter = filter_list
            self.__db.execute(
                "UPDATE filters SET filter_words = %s WHERE guild_id = %s",
                (dumps(new_filter), guild_id),
            )

        return self.get_filter(guild_id)

    def filter_toggle(self, guild_id: int, status: bool):
        """Toggle the filter"""

        self.__db.execute(
            "UPDATE filters SET enabled = %s WHERE guild_id = %s",
            (status, guild_id),
        )
        return

    def toggle_filter_mode(self, guild_id: int, mode: 0 | 1):
        """Toggle the filter mode"""

        self.__db.execute(
            "UPDATE filters SET mode = %s WHERE guild_id = %s",
            (mode, guild_id),
        )
        return

    def remove_filter(self, guild_id: int) -> None:
        """Removes the filter for a guild"""
        self.__db.execute(
            "DELETE FROM filters WHERE guild_id = %s",
            (guild_id),
        )
        return

    def check_filter_enabled(self, guild_id: int) -> bool:
        """Checks if the filter is enabled"""
        self.__db.execute(
            "SELECT enabled FROM filters WHERE guild_id = %s", (guild_id,)
        )
        fetched = self.__db.fetchone()
        return fetched["filter_enabled"]

    def remove_guild_and_data(self, guild_id) -> NoneType:
        """Remove a guild based on ID"""
        self.__db.execute("DELETE FROM configuration WHERE guild_id = %s", (guild_id,))
        self.__db.execute("DELETE FROM filters WHERE guild_id = %s", (guild_id,))
        stars = self.get_stars(guild_id, get_star_channel=False)
        if stars:
            for star in stars:
                if star:
                    self.remove_star(star.star_id)
            # self.__db.execute(
            #     "DELETE FROM stars WHERE guild_id = %s", (guild_id,)
            # )
            # pass
        return
