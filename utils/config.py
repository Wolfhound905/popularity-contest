from os import environ

from dotenv.main import load_dotenv
import pymysql

load_dotenv()

db_login = {
    "host": environ["HOST"],
    "user": environ["USER"],
    "password": environ["PASSWORD"],
    "database": environ["DATABASE"],
    "port": int(environ["PORT"]),
    "charset": "utf8mb4",
    "autocommit": True,
    "cursorclass": pymysql.cursors.DictCursor,
}

token = environ["TOKEN"]
