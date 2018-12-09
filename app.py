from models import db, Rooms, Player
from flask import Flask, jsonify, request
import flask_socketio
from flask_socketio import SocketIO, join_room, close_room
import json
from bson import ObjectId
from datetime import datetime
from flask_cors import CORS

from utils import *

app = Flask(__name__)
app.config['SECRET_KEY'] = 'reuvenKing!'
socketio = SocketIO(app, logger=True)

app.config.from_object(__name__)
app.config['MONGODB_SETTINGS'] = {'DB': 'Connect4'}

db.init_app(app)

cors = CORS(app, resources={r"/*": {"origins": "*"}})

@app.route("/")
def hello():

    return 'reuven'


@app.route('/leaderboard')
def get_rooms():

    players = {}
    resultsTable = Rooms.objects.only('resultsTable')
    for results in resultsTable:
        for result in results['resultsTable']:
            name = result[0]
            if name not in players:
                players[name] = 1
            else:
                players[name] += 1
    
    players_leader = [(k, players[k]) for k in sorted(players, key=players.get, reverse=True)]

    return jsonify(players_leader), 200

@app.route('/games-list')
def get_games_list():
    rooms = Rooms.objects.exclude('board','turn').all()
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

    # TODO: send results table in getViewRoom
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


@app.route('/updateResults/<string:room_id>', methods = ['PUT', 'OPTIONS', 'POST'])
def method_name(room_id):

    if str(request.method) != 'POST':
        return 'NOT OPTIONS', 400

    data = json.loads(request.get_data().decode())

    if 'newBoard' not in data:
        return 'Missing data parameter', 401
    
    is_valid = ObjectId.is_valid(room_id)
    if not is_valid:
        return 'Room id is not valid omer', 402

    room = Rooms.objects(id=room_id)[0]
    if not room:
        return 'No such room', 404
    
    # All good:
    room.resultsTable = data['newBoard']
    room.save()

    return 'goods', 200

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
        room_json['resultsTable'] = room.resultsTable
        room_json['gameEnded'] = room.gameEnded

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
            socketio.emit('startGame', {'data': 'Game in progress', "status": 410}, room=request.sid)
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
def do_turn(room_id, player_id, new_board, game_ended):

    is_valid = ObjectId.is_valid(room_id)
    if not is_valid:
        socketio.emit("gameUpdate", {"data": 'This is not a valid room id bobo', 'status': 400}, room=request.sid)
        return 


    room = Rooms.objects(id=room_id)[0]
    if not room:
        socketio.emit('gameUpdate', {'data': 'No room', 'status': 404}, room=request.sid)


    room.board = new_board
    room.turn = not room.turn
    room.gameEnded = game_ended

    room.save()

    room_json = {
        "id": room_id,
        "board": new_board,
        "turn": room.turn,
        "resultsTable": room.resultsTable,
        "gameEnded": game_ended
    }

    socketio.emit("gameUpdate", {'data': room_json, 'status': 200}, room=room_id)
    
        

@socketio.on('offerNewGame')
def offer_name_game(room_id):

    is_valid = ObjectId.is_valid(room_id)
    if not is_valid:
        socketio.emit("newGameOffer", {"data": 'This is not a valid room id bobo', 'status': 400}, room=request.sid)
        return

    room = Rooms.objects(id=room_id)[0]
    if not room:
        socketio.emit('newGameOffer', {'data': 'No room', 'status': 404}, room=request.sid)

    if not room.gameEnded:
        socketio.emit('newGameOffer', {'data': 'Game didnt end yet', 'status': 401}, room=request.sid)


    # default
    sid_target = room.players[0].sid
    # check if the first player is the asker, if he is, set the other player as target
    if request.sid == room.players[0].sid:
        sid_target = room.players[1].sid

    socketio.emit('newGameOffer', {'status': 200} ,room=sid_target)

@socketio.on('newGameOfferResponse')
def new_offer_response(room_id, response):

    is_valid = ObjectId.is_valid(room_id)
    if not is_valid:
        socketio.emit("offerResult", {"data": 'This is not a valid room id bobo', 'status': 400}, room=request.sid)
        return

    room = Rooms.objects(id=room_id)[0]
    if not room:
        socketio.emit('offerResult', {'data': 'No room', 'status': 404}, room=request.sid)

    if response:
        room.gameEnded = False

    socketio.emit('offerResult', {'data': response, 'status': 200}, room=room_id)
    

@socketio.on('closeRoom')
def close_the_room(room_id, reason):

    is_valid = ObjectId.is_valid(room_id)
    if not is_valid:
        socketio.emit("roomClosed", {"data": 'This is not a valid room id bobo', "status": 404}, room=request.sid)
        return

    room = Rooms.objects(id=room_id)[0]
    if not room:
        socketio.emit("roomClosed", {"data": 'No such room', "status": 404}, room=request.sid)

    socketio.emit("roomClosed", {"data": reason, "status": 200}, room=room_id)

    # This is not my function, its a function of Socketio that implements rooms of sid
    close_room(room_id)

    # Delete room from data base
    room.delete()

@socketio.on('disconnect')
def handle_disconnect():
    room_to_close = Rooms.objects(players__match={'sid': request.sid}).only('id').first()

    # player was not in a room
    if not room_to_close:
        return

    room_id = str(room_to_close['id'])

    socketio.emit("roomClosed", {"data": 'Player exits room', "status": 200}, room=room_id)

    close_room(room_id)

    room_to_close.delete()


# Handle socketio error
@socketio.on_error_default
def default_error_handler(e):
    print("Error:", e)
    print("Event: " + request.event["message"] + ": " + str(request.event["args"]))
    # TODO: Remove error message from emit when going to prod
    if request.event["message"] in EVENTS:
        socketio.emit(EVENTS[request.event["message"]], {"data": str(e), "status": 500}, room=request.sid)

# Log http request
@app.before_request
def log_request_info():
    app.logger.debug('\n' + '~'*44 +'\n%s from %s:\n%s\n' + '~'*44, request.url, request.access_route[0], request.get_data() if request.get_data() else '')


    

if __name__ == '__main__':
    app.debug = app.config['DEBUG']
    socketio.run(app, host='0.0.0.0')
