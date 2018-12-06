from flask_mongoengine import MongoEngine

# biggest hack in history
import mongoengine as me

db = MongoEngine()

class Player(me.EmbeddedDocument):
    name = db.StringField(max_length=50)
    color = db.StringField(max_length=7, default='#424242')
    sid = db.StringField(required=True)


class Rooms(db.Document):
    board = db.ListField(db.ListField(db.StringField(max_length=1)))
    isOpen = db.BooleanField(default=True)
    players = db.EmbeddedDocumentListField(Player)
    turn = db.BooleanField(default=True)
    resultsTable = me.ListField(me.ListField(me.StringField(default='')))
    gameEnded = me.BooleanField(default=False)