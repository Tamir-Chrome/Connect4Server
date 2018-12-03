from models import db, Rooms, Player
from flask import Flask, jsonify, request
from flask_socketio import SocketIO, join_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'reuvenKing!'
socketio = SocketIO(app)

app.config.from_object(__name__)
app.config['MONGODB_SETTINGS'] = {'DB': 'Connect4'}

app.config['DEBUG'] = True
db.init_app(app)


@app.route("/")
def hello():
    return 'reuven'


@app.route('/rooms')
def get_rooms():
    rooms = Rooms.objects.all()
    return jsonify(rooms), 200


@socketio.on('createRoom')
def create_room(user_args):

    board = [[''] * 4] * 4
    player1 = Player(name=user_args['name'],
                     color=user_args['color'], sid=request.sid)

    room = Rooms(board=board, players=[player1])
    room.save()

    join_room(str(room.id))

    socketio.emit("roomOpened", {'roomId': str(room.id)})

    return 'ok'


@socketio.on('joinRoom')
def join_game_room(room_id, user_args):

    room = Rooms.objects(id=room_id)
    if room:

        if len(room.players) == 2:
            return 'Game is progress'

        player = Player(name=user_args['name'],
                        color=user_args['color'], sid=request.sid)
        join_room(room_id)
        socketio.emit("startGame", {'roomData': jsonify(room)}, room=room_id)
    else:
        return 'No such room'


if __name__ == '__main__':
    app.debug = app.config['DEBUG']
    socketio.run(app, host='0.0.0.0')
