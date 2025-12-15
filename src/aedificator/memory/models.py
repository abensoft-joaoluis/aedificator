from peewee import Model, TextField
from .db import database

_db = database()

class BaseModel(Model):
    class Meta:
        database = _db

class Paths(BaseModel):
    superleme_path = TextField(null=True)
    sl_phoenix_path = TextField(null=True)
    extension_path = TextField(null=True)

    class Meta:
        table_name = "paths"
