from models import db, Rooms, Player
from flask import Flask, jsonify, request
import flask_socketio
from flask_socketio import SocketIO, join_room, close_room
import json
from bson import ObjectId
from datetime import datetime

from utils import *

app = Flask(__name__)
app.config['SECRET_KEY'] = 'reuvenKing!'
socketio = SocketIO(app, logger=True)

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

@app.route('/roomMode/<string:room_id>')
def room_mode(room_id):

    is_valid = ObjectId.is_valid(room_id)
    if not is_valid:
        return 'Room id is not valid omer', 400

    room = Rooms.objects(id=room_id)[0]
    
    if room:
        return '0' if room.isOpen else '1', 200
    return '2', 404

@app.route('/lastUpdate/<string:room_id>')
def last_update(room_id):

    last_date = request.args.get('date', None)
    if not last_date:
        return 'Missing date parameter', 400

    is_valid = ObjectId.is_valid(room_id)
    if not is_valid:
        return 'Room id is not valid omer', 400

    room = Rooms.objects(id=room_id)[0]
    if room:

        resultTable = room.resultsTable

        data = {
            'result': room.resultsTable,
            'is_uptodate': False
        }
        if room.lastResultUpdate:

            # parse string to datetime
            datetime_last_date = datetime.strptime(last_date, '%d.%m.%Y %H:%M:%S')

            # check if up to date
            if datetime_last_date >= room.lastResultUpdate:
                data['results'] = None
                data['is_uptodate'] = True

        return jsonify({'data': data}), 200

    else:
        return 'No such room', 404


@app.route('/updateResults/<string:room_id>', methods = ['POST'])
def method_name(room_id):

    new_results_table = request.args.get('data', None)
    if not new_results_table:
        return 'Missing data parameter', 400

    is_valid = ObjectId.is_valid(room_id)
    if not is_valid:
        return 'Room id is not valid omer', 400

    room = Rooms.objects(id=room_id)[0]
    if not room:
        return 'No such room', 404

    # All good:
    room.resultsTable = new_results_table
    room.save()
    
    return jsonify({'data': data}), 200

@socketio.on('getViewRoom')
def to_view_room(room_id):

    is_valid = ObjectId.is_valid(room_id)
    if not is_valid:
        socketio.emit("viewRoom", {"data": 'This is not a valid room id bobo', "status": 400}, room=request.sid)
        return 

    room = Rooms.objects(id=room_id)[0]

    if room:

        join_room(room_id)

        if room.isOpen:
            socketio.emit("viewRoom", {"data": 'Wait for game to start! tembel', "status": 202}, room=request.sid)
            return 

        room_json = room_to_json(room)

        socketio.emit("viewRoom", {"data": room_json, "status": 200}, room=request.sid)
        return


    else:
        socketio.emit("viewRoom", {"data": 'No such room homed', "status": 404}, room=request.sid)


@socketio.on('createRoom')
def create_room(user_args):

    board = [[''] * 9] * 9
    player1 = Player(name=user_args['name'],
                     color=user_args['color'], sid=request.sid)

    room = Rooms(board=board, players=[player1])
    room.save()

    join_room(str(room.id))

    socketio.emit("roomOpened", {'data': str(room.id), "status": 200}, room=request.sid)


@socketio.on('joinRoom')
def join_game_room(room_id, user_args):

    is_valid = ObjectId.is_valid(room_id)
    if not is_valid:
        socketio.emit("startGame", {"data": 'This is not a valid room id bobo', "status": 400}, room=request.sid)
        return 

    room = Rooms.objects(id=room_id)[0]
    if room:

        if not room.isOpen:
            socketio.emit('startGame', {'data': 'Game in progress', "status": 409}, room=request.sid)
            app.logger.info('progress')
            return 

        if user_args['color'] == room.players[0]['color']:
            socketio.emit('startGame', {"data": 'Same color motek!', "status": 409}, room=request.sid)
            app.logger.info('color')
            return

        player = Player(name=user_args['name'],
                        color=user_args['color'], sid=request.sid)
        room.players.append(player)
        room.isOpen = False
        room.save()
        join_room(room_id)
        
        room_json = room_to_json(room)

        socketio.emit("startGame", {'data': room_json, "status": 200}, room=room_id)
    else:
        socketio.emit("startGame", {'data': 'No such room', "status": 404}, room=request.sid)


@socketio.on('doTurn')
def do_turn(room_id, player_id, new_board):

    is_valid = ObjectId.is_valid(room_id)
    if not is_valid:
        socketio.emit("gameUpdate", {"data": 'This is not a valid room id bobo', 'status': 400}, room=request.sid)
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

        socketio.emit("gameUpdate", {'data': room_json, 'status': 200}, room=room_id)
    else:
        socketio.emit('gameUpdate', {'data': 'No room', 'status': 404}, room=request.sid)


@socketio.on('closeRoom')
def close_room(room_id):

    # TODO: check if the player closing the room is the creator

    is_valid = ObjectId.is_valid(room_id)
    if not is_valid:
        socketio.emit("closedRoom", {"data": 'This is not a valid room id bobo', "status": 404}, room=request.sid)
        return

    room = Rooms.objects(id=room_id)[0]
    if room:

        # This is not my function, its a function of Socketio that implements rooms of sid
        close_room(room_id)

        # Delete room from data base
        room.delete()

        socketio.emit("closedRoom", {"data": 'Room closed', "status": 200}, room=room_id)

    else:
        socketio.emit("closedRoom", {"data": 'No such room', "status": 404}, room=request.sid)


# Handle socketio error
@socketio.on_error_default
def default_error_handler(e):
    print("Error:", e)
    print("Event: " + request.event["message"] + ": " + str(request.event["args"]))
    # TODO: Remove error message from emit when going to prod
    socketio.emit(EVENTS[request.event["message"]], {"data": str(e), "status": 500}, room=request.sid)

# Log http request
@app.before_request
def log_request_info():
    app.logger.debug('\n' + '~'*44 +'\n%s from %s:\n%s\n' + '~'*44, request.url, request.access_route[0], request.get_data())


if __name__ == '__main__':
    app.debug = app.config['DEBUG']
    socketio.run(app, host='0.0.0.0')
