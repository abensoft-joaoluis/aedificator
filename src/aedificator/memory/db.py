import os
from peewee import SqliteDatabase

DB_DIR = os.path.join(os.getcwd(), "data")
DB_FILE = os.path.join(DB_DIR, "aedificator.db")

def database():
    """Return a peewee SqliteDatabase instance pointing at DB_FILE."""
    os.makedirs(DB_DIR, exist_ok=True)
    return SqliteDatabase(DB_FILE)


def initialize_database(db=None):
    """Initialize database connection and create tables if they do not exist."""
    db = db or database()
    db.connect(reuse_if_open=True)
    return db
