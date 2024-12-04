from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room, emit
import random
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Room and player data
rooms = {}

ROLES = ["King", "Police", "Robber", "Thief"]

@app.route("/")
def index():
    return "Server is running!"

@socketio.on("create_room")
def create_room(data):
    room_code = data["room_code"]
    if room_code in rooms:
        emit("error", {"message": "Room already exists!"})
    else:
        rooms[room_code] = {"players": {}, "scores": {}, "turns": 0}
        emit("room_created", {"room_code": room_code})

@socketio.on("join_room")
def join_room_event(data):
    username = data["username"]
    room_code = data["room_code"]

    if room_code not in rooms:
        emit("error", {"message": "Room does not exist!"})
        return

    if username in rooms[room_code]["players"]:
        emit("error", {"message": "Username already taken!"})
        return

    rooms[room_code]["players"][username] = None
    rooms[room_code]["scores"][username] = 0
    join_room(room_code)
    
    # Check if the room has 4 players to start the game automatically
    if len(rooms[room_code]["players"]) == 4:
        emit("game_starting", {"message": "Game is starting!"}, to=room_code)
        start_game({"room_code": room_code})
    
    emit("player_joined", {
        "username": username, 
        "players": list(rooms[room_code]["players"].keys())
    }, to=room_code)

@socketio.on("start_game")
def start_game(data):
    room_code = data["room_code"]
    if len(rooms[room_code]["players"]) < 4:
        emit("error", {"message": "Not enough players to start the game!"})
        return

    start_turn(room_code)

def start_turn(room_code):
    players = list(rooms[room_code]["players"].keys())
    random.shuffle(players)
    roles = dict(zip(players, ROLES))

    rooms[room_code]["players"] = roles
    rooms[room_code]["turns"] += 1

    emit("new_turn", {
        "roles": roles, 
        "turns": rooms[room_code]["turns"]
    }, to=room_code)


@socketio.on("guess_roles")
def guess_roles(data):
    room_code = data["room_code"]
    police_guess = data["police_guess"]

    roles = rooms[room_code]["players"]
    police = [player for player, role in roles.items() if role == "Police"][0]
    robber = [player for player, role in roles.items() if role == "Robber"][0]
    thief = [player for player, role in roles.items() if role == "Thief"][0]

    if police_guess == {"Robber": robber, "Thief": thief}:
        rooms[room_code]["scores"][police] += 80
    else:
        rooms[room_code]["scores"][robber] += 60
        rooms[room_code]["scores"][thief] += 40

    king = [player for player, role in roles.items() if role == "King"][0]
    rooms[room_code]["scores"][king] += 100

    emit("update_scores", {"scores": rooms[room_code]["scores"]}, to=room_code)

    if rooms[room_code]["turns"] >= 5:  # End after 5 turns
        winner = max(rooms[room_code]["scores"], key=rooms[room_code]["scores"].get)
        emit("game_over", {"winner": winner, "scores": rooms[room_code]["scores"]}, to=room_code)
    else:
        start_turn(room_code)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)
