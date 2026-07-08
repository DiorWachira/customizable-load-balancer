from flask import Flask, jsonify, request

from consistent_hash import ConsistentHashMap

app = Flask(__name__)
hash_map = ConsistentHashMap()


@app.route('/servers', methods=['GET'])
def list_servers():
    return jsonify({"servers": sorted(hash_map.physical_servers)}), 200


@app.route('/servers', methods=['POST'])
def add_server():
    payload = request.get_json(silent=True) or {}
    hostname = payload.get('hostname')

    if not hostname or not isinstance(hostname, str):
        return jsonify({"error": "hostname must be a non-empty string"}), 400

    before = len(hash_map.physical_servers)
    hash_map.add_server(hostname)
    after = len(hash_map.physical_servers)

    return jsonify(
        {
            "message": "server added" if after > before else "server already present",
            "hostname": hostname,
            "num_servers": after,
        }
    ), 200


@app.route('/servers/<hostname>', methods=['DELETE'])
def remove_server(hostname):
    if hostname not in hash_map.physical_servers:
        return jsonify({"error": "server not found", "hostname": hostname}), 404

    hash_map.remove_server(hostname)
    return jsonify({"message": "server removed", "hostname": hostname}), 200


@app.route('/route', methods=['GET'])
def route_request():
    request_id = request.args.get('request_id', type=int)
    if request_id is None:
        return jsonify({"error": "request_id query parameter is required and must be an integer"}), 400

    hostname = hash_map.get_server(request_id)
    if hostname is None:
        return jsonify({"error": "no servers available"}), 503

    return jsonify({"request_id": request_id, "server": hostname}), 200


@app.route('/heartbeat', methods=['GET'])
def heartbeat():
    return '', 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
