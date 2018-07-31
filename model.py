import uuid

from peewee import *


db_name = 'polls.db'
db = SqliteDatabase(db_name)


class BaseModel(Model):
    class Meta:
        database = db


class Poll(BaseModel):
    question = TextField(index=True)
    opened = BooleanField(default=True)


class Answer(BaseModel):
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    poll = ForeignKeyField(Poll, backref='answers')
    answer = TextField(index=True)
    nb = IntegerField(default=0)


def create_db():
    db.connect()
    db.create_tables([Poll, Answer])
    print("DB successfully created")
