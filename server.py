import json
import os
from flask import Flask, jsonify, request

app = Flask(__name__)
DATA_FILE = "users.json"

# Active sessions: { "username": {"location": "Capital City", "activity": "In Town"} }
ACTIVE_SESSIONS = {}

# Message buffer: { "recipient": [{"from": "sender", "msg": "Hello!"}] }
CHAT_MESSAGES = {}


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
                jsonify({
                    "success": False,
                    "message": "Account is already logged in on another device!",
                }),
                401,
            )

        p_data = users[username]["player_data"]
        ACTIVE_SESSIONS[username] = {
            "class": p_data.get("char_class", "Unknown"),
            "level": p_data.get("level", 1),
            "location": p_data.get("location_name", "Aethelia"),
            "activity": "In Main Menu",
        }
        return (
            jsonify({
                "success": True,
                "message": "Login successful",
                "player_data": p_data,
            }),
            200,
        )

    return (
        jsonify({"success": False, "message": "Invalid username or password."}),
        401,
    )


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
    activity = data.get("activity", "Busy")
    location = data.get("location", "Aethelia")

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
    return jsonify({"success": True, "message": "Message sent!"}), 200


@app.route("/get-messages", methods=["POST"])
def get_messages():
    data = request.json
    username = data.get("username")
    messages = CHAT_MESSAGES.get(username, [])
    CHAT_MESSAGES[username] = []  # Clear after reading
    return jsonify({"messages": messages}), 200


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
        return (
            jsonify({"success": False, "message": "Username is already taken."}),
            400,
        )

    users[username] = {"password": password, "player_data": player_data}
    save_data(users)

    ACTIVE_SESSIONS[username] = {
        "class": player_data.get("char_class", "Unknown"),
        "level": player_data.get("level", 1),
        "location": player_data.get("location_name", "Aethelia"),
        "activity": "Newly Registered",
    }
    return jsonify({"success": True, "message": "Account created!"}), 201


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
                "location_name", "Aethelia"
            )

        return jsonify({"success": True, "message": "Saved successfully"}), 200
    return jsonify({"success": False, "message": "User not found"}), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
