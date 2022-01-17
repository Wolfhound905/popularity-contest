from random import choice
from utils.database import Database

from dis_snek import Activity, ActivityType


def get_random_presence(guilds, db: Database) -> Activity:
    """
    Get random presence
    """
    message_total, star_total = db.get_global_stats()
    activity = choice(
        [
            Activity(name=f"{star_total} stars 💫", type=ActivityType.WATCHING),
            Activity(name="with the stars 🌠"),
            Activity(name="the Popularity Contest", type=ActivityType.COMPETING),
            Activity(name=f"in {guilds} servers", type=ActivityType.WATCHING),
        ]
    )
    return activity
