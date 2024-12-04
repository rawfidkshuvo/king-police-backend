import random
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room

# Initialize Flask and SocketIO
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Game state
rooms = {}

# Roles
ROLES = ["King", "Police", "Robber", "Thief"]

@app.route('/')
def index():
    return render_template("index.html")

# Handle player joining the room
@socketio.on("join_room")
def join_room_event(data):
    username = data["username"]
    room_code = data["room_code"]

    if room_code not in rooms:
        rooms[room_code] = {
            "players": {},
            "scores": {},
            "turns": 0
        }

    if username in rooms[room_code]["players"]:
        emit("error", {"message": "Username already taken!"})
        return

    rooms[room_code]["players"][username] = None
    rooms[room_code]["scores"][username] = 0
    join_room(room_code)

    # Notify others that a new player has joined
    emit("player_joined", {
        "username": username, 
        "players": list(rooms[room_code]["players"].keys())
    }, to=room_code)

    print(f"Player {username} joined room {room_code}. Current players: {list(rooms[room_code]['players'].keys())}")

# Handle starting the game
@socketio.on("start_game")
def start_game(data):
    room_code = data["room_code"]
    print(f"Received 'start_game' event for room: {room_code}")

    if room_code not in rooms:
        emit("error", {"message": "Room does not exist!"})
        return

    if len(rooms[room_code]["players"]) < 4:
        emit("error", {"message": "Not enough players to start the game!"})
        return

    print(f"Starting game for room {room_code} with players: {list(rooms[room_code]['players'].keys())}")
    start_turn(room_code)

# Start a new turn (assign roles, etc.)
def start_turn(room_code):
    players = list(rooms[room_code]["players"].keys())
    random.shuffle(players)
    roles = dict(zip(players, ROLES))

    rooms[room_code]["players"] = roles
    rooms[room_code]["turns"] += 1

    print(f"Turn {rooms[room_code]['turns']} for room {room_code}: Roles - {roles}")

    # Emit the new turn data to all players in the room
    emit("new_turn", {
        "roles": roles, 
        "turns": rooms[room_code]["turns"]
    }, to=room_code)

# Run the Flask app
if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5000)
