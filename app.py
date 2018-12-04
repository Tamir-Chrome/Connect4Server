from models import db, Rooms, Player
from flask import Flask, jsonify, request
from flask_socketio import SocketIO, join_room, close_room
import json
from bson import ObjectId
import bson

app = Flask(__name__)
app.config['SECRET_KEY'] = 'reuvenKing!'
socketio = SocketIO(app)

app.config.from_object(__name__)
app.config['MONGODB_SETTINGS'] = {'DB': 'Connect4'}

app.config['DEBUG'] = True
db.init_app(app)

@app.before_request
def log_request_info():
    app.logger.debug('\n~~~~~~~~~~~\n%s from %s:\n%s\n~~~~~~~~~~~', request.url, request.access_route[0], request.get_data())

@app.route("/")
def hello():

    return 'reuven'


@app.route('/rooms')
def get_rooms():

    rooms = Rooms.objects.all()
    return jsonify(rooms), 200

@app.route('/roomMode/<string:room_id>')
def room_mode(room_id):

    is_valid = ObjectId.is_valid(room_id)
    if not is_valid:
        return 'Room id is not valid omer', 404

    room = Rooms.objects(id=room_id)[0]
    
    if room:
        return '0' if room.isOpen else '1', 200
    return '2', 200

@socketio.on('getViewRoom')
def to_view_room(room_id):

    is_valid = bson.objectid.ObjectId.is_valid(room_id)
    if not is_valid:
        socketio.emit("viewRoom", {"message": 'This is not a valid room id bobo', "status": 404})
        return 

    room = Rooms.objects(id=room_id)[0]

    if room:

        join_room(room_id)

        if room.isOpen:
            socketio.emit("viewRoom", {"message": 'Wait for game to start! tembel', "status": 202})
            return 

        
        room_json = room_to_json(room)

        socketio.emit("viewRoom", {"data": room_json, "status": 200})
        return


    else:
        socketio.emit("roomData", {"message": 'No such room homed', "status": 404})
        return 


@socketio.on('createRoom')
def create_room(user_args):

    board = [[''] * 9] * 9
    player1 = Player(name=user_args['name'],
                     color=user_args['color'], sid=request.sid)

    room = Rooms(board=board, players=[player1])
    room.save()

    join_room(str(room.id))

    socketio.emit("roomOpened", {'roomId': str(room.id)}, room=str(room.id))

    return 'ok'


def player_to_json(player):
    return {
        "name": player.name,
        "color": player.color
    }  

def room_to_json(room):
    return {
        "id": str(room.id),
        "board": room.board,
        "players": [player_to_json(room.players[0]), player_to_json(room.players[1])],
        "turn": room.turn
    }

@socketio.on('joinRoom')
def join_game_room(room_id, user_args):

    is_valid = bson.objectid.ObjectId.is_valid(room_id)
    if not is_valid:
        socketio.emit("startGame", {"error": 'This is not a valid room id bobo'})
        return 

    room = Rooms.objects(id=room_id)[0]
    if room:

        if len(room.players) == 2:
            socketio.emit('startGame', {'error': 'Game in progress'})
            app.logger.info('progress')
            return 

        if user_args['color'] == room.players[0]['color']:
            socketio.emit('startGame', {"warning": 'Same color motek!'})
            app.logger.info('color')
            return

        player = Player(name=user_args['name'],
                        color=user_args['color'], sid=request.sid)
        room.players.append(player)
        room.isOpen = False
        room.save()
        join_room(room_id)
        
        room_json = room_to_json(room)

        socketio.emit("startGame", {'roomData': room_json}, room=room_id)
    else:
        socketio.emit("startGame", {'error': 'No room'})
        return


@socketio.on('doTurn')
def do_turn(room_id, player_id, new_board):

    is_valid = bson.objectid.ObjectId.is_valid(room_id)
    if not is_valid:
        socketio.emit("gameUpdate", {"error": 'This is not a valid room id bobo'})
        return 

    room = Rooms.objects(id=room_id)[0]
    if room:

        room.board = new_board
        room.turn = not room.turn
        room.save()

        room_json = {
            "id": room_id,
            "board": new_board,
            "turn": room.turn
        }

        socketio.emit("gameUpdate", {'updatedData': room_json})
    else:
        socketio.emit('gameUpdate', {'error': 'No room'})
        return



if __name__ == '__main__':
    app.debug = app.config['DEBUG']
    socketio.run(app, host='0.0.0.0')
