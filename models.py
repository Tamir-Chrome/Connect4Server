from flask_mongoengine import MongoEngine

# biggest hack in history
import mongoengine as me

db = MongoEngine()

class Board(db.Document):
    board = me.ListField()
    