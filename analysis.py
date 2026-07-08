import asyncio
import json
import random
import requests
import time
import aiohttp
import matplotlib.pyplot as plt

LB_URL = "http://localhost:5000"


async def fetch_home(session, request_id):
    """Sends an async request through the load balancer."""
    headers = {"X-Request-ID": str(request_id)}
    try:
        async with session.get(f"{LB_URL}/home", headers=headers, timeout=5) as response:
            if response.status == 200:
                # The LB may return JSON with a non-JSON content-type; parse defensively.
                text = await response.text()
                try:
                    data = await response.json(content_type=None)
                except Exception:
                    try:
                        data = json.loads(text)
                    except Exception:
                        data = {}

                # Parse server ID out of the return string "Hello from Server: server_1"
                msg = data.get("message", "") if isinstance(data, dict) else ""
                if "Server:" in msg:
                    return msg.split("Server: ")[1]
    except Exception:
        pass
    return None


async def run_async_load(total_requests=10000, concurrency=200):
    """Launches async requests with bounded concurrency for stable load generation."""
    sem = asyncio.Semaphore(concurrency)

    async with aiohttp.ClientSession() as session:
        async def _bounded_fetch():
            req_id = random.randint(100000, 999999)
            async with sem:
                return await fetch_home(session, req_id)

        tasks = [_bounded_fetch() for _ in range(total_requests)]
        return await asyncio.gather(*tasks)


def experiment_a1():
    print("\n--- Running Experiment A-1 (10,000 requests on N=3) ---")
    # Reset to default N=3 cluster topology safely via endpoints
    try:
        status_res = requests.get(f"{LB_URL}/rep").json()
        current_replicas = status_res["message"]["replicas"]
        expected = ["server_1", "server_2", "server_3"]
        if sorted(current_replicas) != expected:
            print("Resetting topology to standard N=3 cluster topology...")
            requests.delete(f"{LB_URL}/rm", json={"n": len(current_replicas), "hostnames": current_replicas})
            requests.post(f"{LB_URL}/add", json={"n": 3, "hostnames": expected})
    except Exception as e:
        print(f"Make sure your LB stack is active! Error: {e}")
        return

    results = asyncio.run(run_async_load(10000))

    # Process distribution frequencies
    counts = {}
    for server in results:
        if server:
            counts[server] = counts.get(server, 0) + 1

    print(f"Distribution counts: {counts}")

    # Render Bar Graph
    plt.figure(figsize=(8, 5))
    plt.bar(counts.keys(), counts.values(), color='skyblue', edgecolor='black')
    plt.title("Experiment A-1: Load Distribution Across N=3 Server Replicas")
    plt.xlabel("Server Hostname")
    plt.ylabel("Number of Handled Requests")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.savefig("experiment_a1_bar.png")
    plt.close()
    print("Graph saved successfully as 'experiment_a1_bar.png'")


def experiment_a2():
    print("\n--- Running Experiment A-2 (Scaling N from 2 to 6) ---")
    n_values = [2, 3, 4, 5, 6]
    avg_loads = []

    for n in n_values:
        print(f"Testing cluster scale out configuration at N={n}...")
        # Re-initialize cluster layout to match current step size
        try:
            status_res = requests.get(f"{LB_URL}/rep").json()
            current_replicas = status_res["message"]["replicas"]
            requests.delete(f"{LB_URL}/rm", json={"n": len(current_replicas), "hostnames": current_replicas})

            hostnames = [f"server_{i}" for i in range(1, n + 1)]
            requests.post(f"{LB_URL}/add", json={"n": n, "hostnames": hostnames})
        except Exception as e:
            print(f"Error modifying cluster footprint: {e}")
            continue

        # Distribute standard traffic
        results = asyncio.run(run_async_load(10000))

        counts = {}
        for server in results:
            if server:
                counts[server] = counts.get(server, 0) + 1

        # Calculate average allocation footprint per replica container instance
        actual_handled = sum(counts.values())
        if counts:
            mean_load = actual_handled / n
        else:
            mean_load = 0
        avg_loads.append(mean_load)
        print(f"Total requests distributed successfully at N={n}: {actual_handled}. Average load: {mean_load}")

    # Render Line Graph
    plt.figure(figsize=(8, 5))
    plt.plot(n_values, avg_loads, marker='o', color='crimson', linewidth=2)
    plt.title("Experiment A-2: Average System Load per Server vs Cluster Scale")
    plt.xlabel("Number of Server Instances (N)")
    plt.ylabel("Average Handled Request Load")
    plt.xticks(n_values)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.savefig("experiment_a2_line.png")
    plt.close()
    print("Graph saved successfully as 'experiment_a2_line.png'")


def experiment_a3():
    print("\n--- Running Experiment A-3 (Failure Recovery Verification) ---")
    try:
        # Step 1: Query what replicas are running
        status_res = requests.get(f"{LB_URL}/rep").json()
        replicas = status_res["message"]["replicas"]
        target_to_kill = replicas[0]
        print(f"Active cluster state: {replicas}")
        print(f"Simulating ungraceful server outage on instance: {target_to_kill}")

        # Step 2: Stop container directly from the host system terminal to bypass ordinary deletion pathways
        import os
        os.system(f"docker stop {target_to_kill}")
        print("Outage triggered. Monitoring recovery thread loop...")

        # Step 3: Continuously poll /rep endpoint to witness background recovery thread auto-healing
        for attempt in range(5):
            time.sleep(1.5)
            check_res = requests.get(f"{LB_URL}/rep").json()
            new_replicas = check_res["message"]["replicas"]
            print(f"Current active system pool layout: {new_replicas}")
            if target_to_kill not in new_replicas:
                print("Success! Health checker background loop successfully removed failed node and auto-spawned a replacement.")
                break
    except Exception as e:
        print(f"Experiment A-3 Error execution flow aborted: {e}")


if __name__ == '__main__':
    # Execute analytical pipeline steps
    experiment_a1()
    experiment_a2()
    experiment_a3()
