from flask import Flask, jsonify, request

app = Flask(__name__)

# Route für die Live-Statusprüfung im Launcher
@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "online"}), 200

# Route für den Login
@app.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get("username")
    return jsonify({"success": True, "message": f"Willkommen zurück, {username}!"}), 200

# Route für die Registrierung
@app.route('/register', methods=['POST'])
def register():
    data = request.json or {}
    username = data.get("username")
    return jsonify({"success": True, "message": f"Account für {username} erfolgreich erstellt!"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)