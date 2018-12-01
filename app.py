from flask import Flask, jsonify

app = Flask(__name__)

app.config.from_object(__name__)
app.config['MONGODB_SETTINGS'] = {'DB': 'Connect4'}
app.config['SECRET_KEY'] = 'reuvenKing!'
app.config['DEBUG'] = True

from models import db, Rooms, Player
db.init_app(app)

@app.route("/")
def hello():
    return 'reuven'

@app.route('/rooms')
def get_rooms():
   rooms = Rooms.objects.all()
   return jsonify(rooms), 200

@app.route('/add_room')
def add_room():
   board = [[''] * 4] * 4
   player1 = Player(name='Omer', color='#7B7B7B')

   room = Rooms(board=board, player1=player1)
   room.save()
   return 'ok', 200

if __name__ == '__main__':
    app.debug = app.config['DEBUG']
    app.run('localhost')