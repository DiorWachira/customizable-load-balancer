import os
import random
import string
import threading
import time
import requests
from flask import Flask, jsonify, request
from consistent_hash import ConsistentHashMap

app = Flask(__name__)

# Track status configurations
N = 3
managed_replicas = []
hash_map = ConsistentHashMap()
lock = threading.Lock()

# Environment configurations
SERVER_IMAGE = "my-server-image"
DOCKER_NETWORK = "net1"


def generate_random_name():
    """Generates a random hostname if none is preferred."""
    return "server_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))


def spawn_container(hostname):
    """Spawns a new server container instance connected to the network."""
    cmd = f"docker run -d --name {hostname} --network {DOCKER_NETWORK} --network-alias {hostname} -e SERVER_ID={hostname} {SERVER_IMAGE}"
    os.popen(cmd).read()


def remove_container(hostname):
    """Stops and removes a server container."""
    os.system(f"docker stop {hostname} && docker rm {hostname}")


def initialize_lb():
    """Initializes the starting N=3 servers."""
    global managed_replicas
    with lock:
        for i in range(1, N + 1):
            hostname = f"server_{i}"
            managed_replicas.append(hostname)
            hash_map.add_server(hostname)
            spawn_container(hostname)


def heartbeat_checker():
    """Background thread that constantly verifies server health."""
    global managed_replicas
    while True:
        time.sleep(2)  # Check every 2 seconds
        with lock:
            active_replicas = list(managed_replicas)

        for hostname in active_replicas:
            try:
                # Attempting to contact the internal endpoint of the server
                res = requests.get(f"http://{hostname}:5000/heartbeat", timeout=1)
                if res.status_code != 200:
                    raise requests.RequestException()
            except requests.RequestException:
                # If a failure occurs, handle it immediately
                with lock:
                    if hostname in managed_replicas:
                        print(f"[HEARTBEAT] Server {hostname} failed! Remediation started...")
                        hash_map.remove_server(hostname)
                        managed_replicas.remove(hostname)

                        # Spawn replacement with a randomly generated name
                        new_hostname = generate_random_name()
                        managed_replicas.append(new_hostname)
                        hash_map.add_server(new_hostname)
                        spawn_container(new_hostname)
                        print(f"[HEARTBEAT] Replaced {hostname} with new instance {new_hostname}")


@app.route('/rep', methods=['GET'])
def get_replicas():
    with lock:
        return jsonify({
            "message": {
                "N": len(managed_replicas),
                "replicas": managed_replicas
            },
            "status": "successful"
        }), 200


@app.route('/add', methods=['POST'])
def add_replicas():
    global managed_replicas
    payload = request.get_json()
    n = payload.get("n", 0)
    hostnames = payload.get("hostnames", [])

    if len(hostnames) > n:
        return jsonify({
            "message": "<Error> Length of hostname list is more than newly added instances",
            "status": "failure"
        }), 400

    with lock:
        for i in range(n):
            if i < len(hostnames):
                name = hostnames[i]
            else:
                name = generate_random_name()

            managed_replicas.append(name)
            hash_map.add_server(name)
            spawn_container(name)

        return jsonify({
            "message": {
                "N": len(managed_replicas),
                "replicas": managed_replicas
            },
            "status": "successful"
        }), 200


@app.route('/rm', methods=['DELETE'])
def remove_replicas():
    global managed_replicas
    payload = request.get_json()
    n = payload.get("n", 0)
    hostnames = payload.get("hostnames", [])

    if len(hostnames) > n:
        return jsonify({
            "message": "<Error> Length of hostname list is more than removable instances",
            "status": "failure"
        }), 400

    with lock:
        # Delete specific ones first
        for name in list(hostnames):
            if name in managed_replicas:
                managed_replicas.remove(name)
                hash_map.remove_server(name)
                remove_container(name)
                n -= 1

        # Delete remaining randomly chosen instances if n > 0
        while n > 0 and managed_replicas:
            chosen = random.choice(managed_replicas)
            managed_replicas.remove(chosen)
            hash_map.remove_server(chosen)
            remove_container(chosen)
            n -= 1

        return jsonify({
            "message": {
                "N": len(managed_replicas),
                "replicas": managed_replicas
            },
            "status": "successful"
        }), 200


@app.route('/<path:path>', methods=['GET'])
def route_request(path):
    # Route request to a container based on random 6 digit ID mapped in consistent hashing
    req_id = random.randint(100000, 999999)
    target_server = hash_map.get_server(req_id)

    if not target_server:
        return jsonify({"message": "<Error> No server instances available", "status": "failure"}), 500

    try:
        url = f"http://{target_server}:5000/{path}"
        response = requests.get(url, timeout=2)
        return response.content, response.status_code
    except requests.RequestException:
        return jsonify({
            "message": f"<Error> '/{path}' endpoint does not exist or server timed out",
            "status": "failure"
        }), 400


if __name__ == '__main__':
    # Initialize infrastructure servers and kick off heartbeat monitor thread
    initialize_lb()
    threading.Thread(target=heartbeat_checker, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
