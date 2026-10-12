from flask import Flask, jsonify, request

app = Flask(__name__)

# Test-Route / Server-Ping für die Statusanzeige im Spiel
@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "online"}), 200

# Login-Route
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Hier deine Login-Logik einfügen
    if username == "admin" and password == "1234":
        return jsonify({"message": "Login erfolgreich!", "success": True}), 200
    return jsonify({"message": "Ungültige Anmeldedaten.", "success": False}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)