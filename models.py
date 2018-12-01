from flask_mongoengine import MongoEngine

# biggest hack in history
import mongoengine as me

db = MongoEngine()

class Player(me.EmbeddedDocument):
    name = me.StringField(max_length=50)
    color = me.StringField(max_length=7, default='#424242')

class Rooms(db.Document):
    board = me.ListField(me.ListField(me.StringField(max_length=1)))
    isOpen = me.BooleanField(default=True)
    player1 = me.EmbeddedDocumentField(Player)
    player2 = me.EmbeddedDocumentField(Player)
    turn = me.BooleanField(default=True)
