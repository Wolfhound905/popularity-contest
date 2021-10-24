from pymysql.connections import Connection
from pymysql.cursors import Cursor


class Database:
    def __init__(self, con):
        self.__con: Connection = con
        self.__db: Cursor = self.__con.cursor()

    def setup(self, guild_id: int, channel_id: int, star_count: int):
        self.__db.execute(
            "REPLACE INTO configuration (guild_id, star_channel, min_star_count) VALUES (%s, %s, %s);",
            (guild_id, channel_id, star_count),
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
