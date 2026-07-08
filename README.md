# Customizable Load Balancer

An implementation of a customizable load balancer that routes client requests asynchronously across multiple server replicas using a consistent hashing data structure.

## Phase 1: Task 1 — Minimal Server Implementation
### Design Choices
- **Framework**: Python with Flask due to its simplicity and rapid prototyping capabilities.
- **Dynamic Identification**: The server reads the `SERVER_ID` environment variable at runtime to dynamically adjust its identity in responses.

### Testing
- `GET /home`: Returns JSON with server status and explicit instance ID.
- `GET /heartbeat`: Returns an empty response with a `200 OK` status for health checks.

## Phase 2: Task 2 — Consistent Hashing
### Design Choices
- **Standalone Hash Ring Module**: Implemented in `load_balancer/consistent_hash.py` using a circular array of 512 slots.
- **Virtual Servers**: Each physical server is mapped to `log2(512)=9` virtual nodes.
- **Collision Handling**: Linear probing is used when virtual nodes map to occupied slots.

### Load Balancer API (Minimal Wrapper)
- `GET /servers`: List registered physical servers.
- `POST /servers`: Add a server using JSON body like `{"hostname": "Server 1"}`.
- `DELETE /servers/<hostname>`: Remove a server.
- `GET /route?request_id=<int>`: Route a request ID to the nearest clockwise server.
- `GET /heartbeat`: Health-check endpoint.

### Testing
- Run from repo root:
	- `py load_balancer/app.py`
- Add servers:
	- `curl -X POST http://localhost:5001/servers -H "Content-Type: application/json" -d "{\"hostname\":\"Server 1\"}"`
	- `curl -X POST http://localhost:5001/servers -H "Content-Type: application/json" -d "{\"hostname\":\"Server 2\"}"`
- Route a request:
	- `curl "http://localhost:5001/route?request_id=123456"`

## Phase 2: Task 2 — Consistent Hashing Data Structure
### Design Choices
- **Ring Implementation**: An array-based ring structure of fixed size 512 is utilized to emulate the circular layout.
- **Collision Management**: Linear probing is built directly into the server insertion logic (`add_server`) to guarantee robust collision handling if multiple virtual mappings land on an identical index slot.
- **ID Extraction parsing**: A custom numeric string filter converts container identifiers dynamically (like `Server 1` or `S5`) into standard clean integers for mathematical calculation.
