from flask_mongoengine import MongoEngine

# biggest hack in history
import mongoengine as me

db = MongoEngine()

class Player(me.EmbeddedDocument):
    name = me.StringField(max_length=50)
    color = me.StringField(max_length=7, default='#424242')
    sid = me.StringField(required=True)

class Rooms(db.Document):
    board = me.ListField(me.ListField(me.StringField(max_length=1)))
    isOpen = me.BooleanField(default=True)
    players = me.EmbeddedDocumentListField(Player)
    turn = me.BooleanField(default=True)
