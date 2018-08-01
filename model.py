import uuid
import os

from peewee import *


db_name = os.getenv("DB_PATH", "polls.db")
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


class Voter(BaseModel):
    id = IntegerField(primary_key=True)
    name = TextField()


class Vote(BaseModel):
    answer = ForeignKeyField(Answer, backref='votes')
    voter = ForeignKeyField(Voter, backref='votes')


def create_db():
    db.connect()
    db.create_tables([Poll, Answer, Vote, Voter])
    print("DB successfully created")

