from peewee import Model, TextField, BooleanField
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

class DockerConfiguration(BaseModel):
    project_name = TextField(unique=True)  # superleme, sl_phoenix
    use_docker = BooleanField(default=False)
    postgres_version = TextField(null=True)
    compose_file = TextField(null=True)  # Path to docker-compose.yml
    languages = TextField(null=True)  # JSON string: {"erlang": "26.0", "elixir": "1.15", "node": "20"}

    class Meta:
        table_name = "docker_configurations"
