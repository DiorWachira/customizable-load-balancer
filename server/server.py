import os
from flask import Flask, jsonify

app = Flask(__name__)

# Fetch the Server ID from an environment variable (it defaults to 'Unknown' if not set)
SERVER_ID = os.environ.get("SERVER_ID", "Unknown")

@app.route('/home', methods=['GET'])
def home():
    response = {
        "message": f"Hello from Server: {SERVER_ID}",
        "status": "successful"
    }
    return jsonify(response), 200

@app.route('/heartbeat', methods=['GET'])
def heartbeat():
    # Return an empty response with a 200 status code as requested
    return '', 200

if __name__ == '__main__':
    # Listen on all interfaces (0.0.0.0) at port 5000
    app.run(host='0.0.0.0', port=5000)
