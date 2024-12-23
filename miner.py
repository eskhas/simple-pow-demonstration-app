import hashlib
import requests
import time
import threading
import random

from server import MINER_NAMES

def calculate_hash(index, transactions, previous_hash, timestamp, nonce):
    block_string = f"{index}{transactions}{previous_hash}{timestamp}{nonce}"
    return hashlib.sha256(block_string.encode()).hexdigest()

def mine_block(block, difficulty):
    nonce = 0
    target = "0" * difficulty
    start_time = time.time()

    while True:
        hash_value = calculate_hash(
            block["index"], block["transactions"], block["previous_hash"], block["timestamp"], nonce
        )
        if hash_value.startswith(target):
            return nonce, hash_value, time.time() - start_time
        nonce += 1

def miner_thread(server_url, miner_id):
    try:
        # Register miner
        requests.post(f"{server_url}/register_miner", json={"miner_id": miner_id})
        print(f"[{miner_id}] Registered with server.")

        while True:
            # Fetch the latest difficulty from the server
            response = requests.get(f"{server_url}/difficulty")
            if response.status_code == 200:
                difficulty = response.json().get("difficulty", 5)
                print(f"[{miner_id}] Current difficulty: {difficulty}")
            else:
                print(f"[{miner_id}] Failed to fetch difficulty from server.")
                time.sleep(5)
                continue

            response = requests.get(f"{server_url}/blockchain")
            if response.status_code == 200:
                blockchain = response.json()
                if not blockchain or blockchain[-1]["hash"]:
                    print(f"[{miner_id}] Waiting for a new block...")
                    time.sleep(5)
                    continue

                block = blockchain[-1]
                print(f"[{miner_id}] Mining block {block['index']}...")

                nonce, hash_value, time_taken = mine_block(block, difficulty=difficulty)

                submission_response = requests.post(
                    f"{server_url}/mine", json={"miner_id": miner_id, "nonce": nonce, "time_taken": time_taken}
                )
                if submission_response.status_code == 200:
                    print(f"[{miner_id}] Block mined successfully in {time_taken:.2f}s!")
                else:
                    print(f"[{miner_id}] Failed to submit block: {submission_response.json().get('error')}")

    except requests.RequestException as e:
        print(f"[{miner_id}] Error communicating with server: {e}")

if __name__ == "__main__":
    server_url = "http://127.0.0.1:5000"

    for name in random.sample(MINER_NAMES, 3):  # Start 3 miners with real names
        thread = threading.Thread(target=miner_thread, args=(server_url, name))
        thread.start()
