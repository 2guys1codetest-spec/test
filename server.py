import json
import os
from flask import Flask, jsonify, request

app = Flask(__name__)
DATA_FILE = "users.json"
ACTIVE_SESSIONS = set()  # Hält fest, wer gerade eingeloggt ist


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
        # Prüfen, ob der Account schon von jemand anderem bespielt wird
        if username in ACTIVE_SESSIONS:
            return (
                jsonify({
                    "success": False,
                    "message": "Account ist bereits auf einem anderen Gerät eingeloggt!",
                }),
                401,
            )

        ACTIVE_SESSIONS.add(username)
        return (
            jsonify({
                "success": True,
                "message": "Login erfolgreich",
                "player_data": users[username]["player_data"],
            }),
            200,
        )
    return (
        jsonify({"success": False, "message": "Ungültiger Benutzername oder Passwort."}),
        401,
    )


@app.route("/logout", methods=["POST"])
def logout():
    data = request.json
    username = data.get("username")
    if username in ACTIVE_SESSIONS:
        ACTIVE_SESSIONS.remove(username)
    return jsonify({"success": True}), 200


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
            jsonify({"success": False, "message": "Benutzername bereits vergeben."}),
            400,
        )

    users[username] = {"password": password, "player_data": player_data}
    save_data(users)
    ACTIVE_SESSIONS.add(username)
    return jsonify({"success": True, "message": "Account erstellt!"}), 201


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
        return jsonify({"success": True, "message": "Gespeichert"}), 200
    return jsonify({"success": False, "message": "User nicht gefunden"}), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
