# Customizable Load Balancer

An implementation of a customizable load balancer that routes client requests asynchronously across multiple server replicas using a consistent hashing data structure.

## Phase 1: Task 1 — Minimal Server Implementation
### Design Choices
- **Framework**: Python with Flask due to its simplicity and rapid prototyping capabilities.
- **Dynamic Identification**: The server reads the `SERVER_ID` environment variable at runtime to dynamically adjust its identity in responses.

### Testing
- `GET /home`: Returns JSON with server status and explicit instance ID.
- `GET /heartbeat`: Returns an empty response with a `200 OK` status for health checks.
