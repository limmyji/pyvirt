from flask import request, jsonify
from routes_config import app
from main.server import server as Server
from main.shared import FAILURE
from main.shared import SUCCESS


from flask_socketio import SocketIO
socketio = SocketIO(app)

sessions_to_be_sent = {}

# callback func that will add created sessions
def return_session(session_details):
    if session_details[4] not in sessions_to_be_sent:
        sessions_to_be_sent[session_details[4]] = session_details

server = Server(vm_max=2, callback=return_session)


@app.route("/sessionCallback", methods=["POST"])
def session_callback():
    username = request.json.get("username")
    if not username:
        return jsonify({"message": "must include username"}), 400

    # wait for session details to be added to the above dict by callback func
    while username not in sessions_to_be_sent:
        socketio.sleep(30)
    session_details = sessions_to_be_sent[username]
    sessions_to_be_sent.pop(username)
    return jsonify({"sessionDetails": session_details}), 201


@app.route("/requestSession", methods=["POST"])
def request_session():
    username = request.json.get("username")
    if not username:
        return jsonify({"message": "must include username"}), 400

    # user Server to add user to queue
    try:
        result = server.requestVM(user=username)
        if result != SUCCESS:
            return jsonify({"message": "cant request session"}), 400
        return jsonify({"message": "requested session! will get details soon.."}), 201
    except Exception as e:
        return jsonify({"message": str(e)}), 400


@app.route("/endSession", methods=["POST"])
def end_session():
    username = request.json.get("username")
    if not username:
        return jsonify({"message": "must include username"}), 400

    # user server to force end session
    try:
        result = server.forceEndSession(user=username)
        if result != SUCCESS:
            return jsonify({"message": "cant end session"}), 400
        return jsonify({"message": "ended session!"}), 201
    except Exception as e:
        return jsonify({"message": str(e)}), 400


@app.route("/reset", methods=["GET"])
def reset():
    try:
        result = server.reset()
        if result == FAILURE:
            return jsonify({"message": "could not reset server"}), 400
        return jsonify({"message": "reset server!"}), 201
    except Exception as e:
        return jsonify({"message": str(e)}), 400


if __name__ == "__main__":
    app.run(debug=True)
