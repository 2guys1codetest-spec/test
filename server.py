import json
import os
import random
from flask import Flask, jsonify, request

app = Flask(__name__)
DATA_FILE = "users.json"

ACTIVE_SESSIONS = {}
CHAT_MESSAGES = {}
GLOBAL_CHAT = []
DUELS = {}


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
    return jsonify({"status": "ok"}), 200


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    users = load_data()

    if username in users and users[username]["password"] == password:
        if username in ACTIVE_SESSIONS:
            return (
                jsonify(
                    {"success": False, "message": "Soul is already bound to another realm!"}
                ),
                401,
            )

        p_data = users[username]["player_data"]
        ACTIVE_SESSIONS[username] = {
            "class": p_data.get("char_class", "Unknown"),
            "level": p_data.get("level", 1),
            "location": p_data.get("location_name", "Tristram Ruins"),
            "activity": "Lurking in Darkness",
        }
        return (
            jsonify({"success": True, "message": "Login successful", "player_data": p_data}),
            200,
        )

    return jsonify({"success": False, "message": "Invalid soul credentials."}), 401


@app.route("/logout", methods=["POST"])
def logout():
    data = request.json
    username = data.get("username")
    if username in ACTIVE_SESSIONS:
        del ACTIVE_SESSIONS[username]
    return jsonify({"success": True}), 200


@app.route("/update-activity", methods=["POST"])
def update_activity():
    data = request.json
    username = data.get("username")
    activity = data.get("activity", "Wandering")
    location = data.get("location", "Tristram Ruins")

    if username in ACTIVE_SESSIONS:
        ACTIVE_SESSIONS[username]["activity"] = activity
        ACTIVE_SESSIONS[username]["location"] = location
    return jsonify({"success": True}), 200


@app.route("/online-players", methods=["GET"])
def online_players():
    return jsonify({"players": ACTIVE_SESSIONS}), 200


@app.route("/send-message", methods=["POST"])
def send_message():
    data = request.json
    sender = data.get("sender")
    recipient = data.get("recipient")
    message = data.get("message")

    if recipient not in CHAT_MESSAGES:
        CHAT_MESSAGES[recipient] = []

    CHAT_MESSAGES[recipient].append({"from": sender, "msg": message})
    return jsonify({"success": True}), 200


@app.route("/get-messages", methods=["POST"])
def get_messages():
    data = request.json
    username = data.get("username")
    messages = CHAT_MESSAGES.get(username, [])
    CHAT_MESSAGES[username] = []
    return jsonify({"messages": messages}), 200


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


@app.route("/duel-challenge", methods=["POST"])
def duel_challenge():
    data = request.json
    challenger = data.get("challenger")
    target = data.get("target")

    if target not in ACTIVE_SESSIONS:
        return jsonify({"success": False, "message": "Wanderer is not present."}), 400

    duel_id = f"{challenger}_vs_{target}"
    DUELS[duel_id] = {
        "challenger": challenger,
        "target": target,
        "status": "pending",
        "log": [],
    }

    if target not in CHAT_MESSAGES:
        CHAT_MESSAGES[target] = []
    CHAT_MESSAGES[target].append(
        {"from": "SYSTEM", "msg": f"DUEL_CHALLENGE:{challenger}:{duel_id}"}
    )

    return jsonify({"success": True, "duel_id": duel_id}), 200


@app.route("/duel-respond", methods=["POST"])
def duel_respond():
    data = request.json
    duel_id = data.get("duel_id")
    accept = data.get("accept")

    if duel_id in DUELS:
        DUELS[duel_id]["status"] = "accepted" if accept else "declined"
        return jsonify({"success": True}), 200
    return jsonify({"success": False, "message": "Trial not found"}), 404


@app.route("/duel-status", methods=["POST"])
def duel_status():
    data = request.json
    duel_id = data.get("duel_id")
    if duel_id in DUELS:
        return jsonify({"success": True, "duel": DUELS[duel_id]}), 200
    return jsonify({"success": False}), 404


@app.route("/friend-status", methods=["POST"])
def friend_status():
    data = request.json
    username = data.get("username")
    is_online = username in ACTIVE_SESSIONS
    return jsonify({"online": is_online}), 200


@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    player_data = data.get("player_data")
    users = load_data()

    if username in users:
        return jsonify({"success": False, "message": "Soul name already bound."}), 400

    users[username] = {"password": password, "player_data": player_data}
    save_data(users)

    ACTIVE_SESSIONS[username] = {
        "class": player_data.get("char_class", "Unknown"),
        "level": player_data.get("level", 1),
        "location": player_data.get("location_name", "Tristram Ruins"),
        "activity": "Newly Awakened",
    }
    return jsonify({"success": True, "message": "Soul registered!"}), 201


@app.route("/save", methods=["POST"])
def save_progress():
    data = request.json
    username = data.get("username")
    player_data = data.get("player_data")
    users = load_data()

    if username in users:
        password = users[username]["password"]
        users[username] = {"password": password, "player_data": player_data}
        save_data(users)

        if username in ACTIVE_SESSIONS:
            ACTIVE_SESSIONS[username]["level"] = player_data.get("level", 1)
            ACTIVE_SESSIONS[username]["location"] = player_data.get(
                "location_name", "Tristram Ruins"
            )

        return jsonify({"success": True}), 200
    return jsonify({"success": False}), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
