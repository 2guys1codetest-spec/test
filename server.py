import json
import os
import random
import time
from flask import Flask, jsonify, request

app = Flask(__name__)
DATA_FILE = "users.json"

ACTIVE_SESSIONS = {}
CHAT_MESSAGES = {}
GLOBAL_CHAT = []
DUELS = {}


def cleanup_inactive_sessions():
    now = time.time()
    to_delete = [
        user
        for user, data in ACTIVE_SESSIONS.items()
        if now - data.get("last_seen", 0) > 10
    ]
    for user in to_delete:
        del ACTIVE_SESSIONS[user]


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


@app.route("/ping", methods=["GET"])
def ping():
    cleanup_inactive_sessions()
    return jsonify({"status": "ok"}), 200


@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    cleanup_inactive_sessions()
    data = request.json
    username = data.get("username")
    coords = data.get("coords", [0, 0])
    location = data.get("location", "Capital City Aethelia")

    if username in ACTIVE_SESSIONS:
        ACTIVE_SESSIONS[username]["last_seen"] = time.time()
        ACTIVE_SESSIONS[username]["coords"] = coords
        ACTIVE_SESSIONS[username]["location"] = location

        # Automatische Erkennung für Open-World Duell bei gleicher Koordinate
        for other_user, sess in ACTIVE_SESSIONS.items():
            if (
                other_user != username
                and sess.get("coords") == coords
                .get("location_name")
                == ACTIVE_SESSIONS[username]["location"]
            ):
                duel_id = f"{username}_vs_{other_user}"
                rev_duel_id = f"{other_user}_vs_{username}"
                if (
                    duel_id not in DUELS
                    and rev_duel_id not in DUELS
                    and sess.get("activity") == "Open World"
                ):
                    reward_gold = random.randint(50, 200)
                    DUELS[duel_id] = {
                        "challenger": username,
                        "target": other_user,
                        "status": "pending",
                        "turn": username,
                        "reward_gold": reward_gold,
                        "hp": {username: 100, other_user: 100},
                        "max_hp": {username: 100, other_user: 100},
                        "log": [
                            f"Encounter! {username} and {other_user} met at coords {coords}!"
                        ],
                    }
        return jsonify({"success": True}), 200
    return jsonify({"success": False}), 404


@app.route("/login", methods=["POST"])
def login():
    cleanup_inactive_sessions()
    data = request.json
    username = data.get("username")
    password = data.get("password")
    users = load_data()

    if username in users and users[username]["password"] == password:
        p_data = users[username]["player_data"]
        ACTIVE_SESSIONS[username] = {
            "class": p_data.get("char_class", "Warrior"),
            "level": p_data.get("level", 1),
            "location": p_data.get("location_name", "Capital City Aethelia"),
            "activity": "In Main Menu",
            "coords": [0, 0],
            "last_seen": time.time(),
        }
        return (
            jsonify(
                {
                    "success": True,
                    "message": "Login successful",
                    "player_data": p_data,
                }
            ),
            200,
        )
    return jsonify({"success": False, "message": "Invalid credentials."}), 401


@app.route("/logout", methods=["POST"])
def logout():
    data = request.json
    username = data.get("username")
    if username in ACTIVE_SESSIONS:
        del ACTIVE_SESSIONS[username]
    return jsonify({"success": True}), 200


@app.route("/online-players", methods=["GET"])
def online_players():
    cleanup_inactive_sessions()
    return jsonify({"players": ACTIVE_SESSIONS}), 200


@app.route("/global-chat-send", methods=["POST"])
def global_chat_send():
    data = request.json
    sender = data.get("sender")
    message = data.get("message")
    GLOBAL_CHAT.append({"from": sender, "msg": message})
    if len(GLOBAL_CHAT) > 30:
        GLOBAL_CHAT.pop(0)
    return jsonify({"success": True}), 200


@app.route("/global-chat-get", methods=["GET"])
def global_chat_get():
    return jsonify({"messages": GLOBAL_CHAT}), 200


@app.route("/check-pending-duel", methods=["POST"])
def check_pending_duel():
    data = request.json
    username = data.get("username")
    for duel_id, duel in DUELS.items():
        if (
            duel["target"] == username or duel["challenger"] == username
        ) and duel["status"] == "pending":
            return jsonify({"success": True, "duel_id": duel_id, "duel": duel}), 200
    return jsonify({"success": False}), 200


@app.route("/duel-respond", methods=["POST"])
def duel_respond():
    data = request.json
    duel_id = data.get("duel_id")
    accept = data.get("accept")

    if duel_id in DUELS:
        if accept:
            DUELS[duel_id]["status"] = "active"
            DUELS[duel_id]["log"].append("Both warriors agreed! Duel started!")
        else:
            DUELS[duel_id]["status"] = "declined"
        return jsonify({"success": True}), 200
    return jsonify({"success": False}), 404


@app.route("/duel-status", methods=["POST"])
def duel_status():
    data = request.json
    duel_id = data.get("duel_id")
    if duel_id in DUELS:
        return jsonify({"success": True, "duel": DUELS[duel_id]}), 200
    return jsonify({"success": False}), 404


@app.route("/duel-action", methods=["POST"])
def duel_action():
    data = request.json
    duel_id = data.get("duel_id")
    player = data.get("player")
    action = data.get("action")

    if duel_id not in DUELS:
        return jsonify({"success": False}), 404

    duel = DUELS[duel_id]
    if duel["status"] != "active" or duel["turn"] != player:
        return jsonify({"success": False}), 400

    opponent = duel["target"] if player == duel["challenger"] else duel["challenger"]

    if action == "attack":
        dmg = random.randint(15, 25)
        duel["hp"][opponent] -= dmg
        duel["log"].append(f"{player} strikes {opponent} for {dmg} damage!")
    elif action == "heal":
        heal = random.randint(15, 25)
        duel["hp"][player] = min(duel["max_hp"][player], duel["hp"][player] + heal)
        duel["log"].append(f"{player} recovers {heal} HP!")

    if duel["hp"][opponent] <= 0:
        duel["hp"][opponent] = 0
        duel["status"] = "finished"
        duel["winner"] = player
        duel["log"].append(f"=== {player} WON THE DUEL & REWARD ({duel['reward_gold']}G)! ===")
    else:
        duel["turn"] = opponent

    return jsonify({"success": True, "duel": duel}), 200


@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    player_data = data.get("player_data")
    users = load_data()

    if username in users:
        return jsonify({"success": False, "message": "Username taken."}), 400

    users[username] = {"password": password, "player_data": player_data}
    save_data(users)
    ACTIVE_SESSIONS[username] = {
        "class": player_data.get("char_class", "Warrior"),
        "level": player_data.get("level", 1),
        "location": "Capital City Aethelia",
        "activity": "Newly Registered",
        "coords": [0, 0],
        "last_seen": time.time(),
    }
    return jsonify({"success": True, "message": "Account created!"}), 201


@app.route("/save", methods=["POST"])
def save_progress():
    data = request.json
    username = data.get("username")
    player_data = data.get("player_data")
    users = load_data()

    if username in users:
        users[username]["player_data"] = player_data
        save_data(users)
        if username in ACTIVE_SESSIONS:
            ACTIVE_SESSIONS[username]["level"] = player_data.get("level", 1)
            ACTIVE_SESSIONS[username]["last_seen"] = time.time()
        return jsonify({"success": True}), 200
    return jsonify({"success": False}), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
