
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

EVENTS = {
    'startGame': 'roomOpened',
    'joinRoom': 'startGame',
    'doTurn': 'gameUpdate',
    'closeRoom': 'closedRoom',
    'getViewRoom': 'viewRoom'
}