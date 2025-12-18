import os
from peewee import SqliteDatabase
from aedificator.paths import get_data_dir, get_db_path


DB_DIR = get_data_dir()
DB_FILE = get_db_path()


def database():
    """Return a peewee SqliteDatabase instance pointing at DB_FILE."""
    os.makedirs(DB_DIR, exist_ok=True)
    return SqliteDatabase(DB_FILE)


def initialize_database(db=None):
    """Initialize database connection and create tables if they do not exist."""
    db = db or database()
    db.connect(reuse_if_open=True)
    return db
