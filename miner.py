import hashlib
import requests
import time
import threading
import random

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
    while True:
        try:
            # Trigger mining manually
            input(f"[{miner_id}] Press Enter to fetch a block to mine...")

            response = requests.post(f"{server_url}/start")
            if response.status_code != 200:
                print(f"[{miner_id}] Failed to fetch block: {response.json().get('error')}")
                continue

            block_data = response.json()
            block = block_data.get("block")

            print(f"[{miner_id}] Mining block {block['index']}...")
            nonce, hash_value, time_taken = mine_block(block, difficulty=5)

            submission_response = requests.post(
                f"{server_url}/mine", json={"miner_id": miner_id, "nonce": nonce}
            )
            if submission_response.status_code == 200:
                print(f"[{miner_id}] Block mined successfully in {time_taken:.2f}s!")
            else:
                print(f"[{miner_id}] Failed to submit block: {submission_response.json().get('error')}")

        except requests.RequestException as e:
            print(f"[{miner_id}] Error communicating with server: {e}")

if __name__ == "__main__":
    server_url = "http://127.0.0.1:5000"
    miner_id = f"Miner-{random.randint(1, 1000)}"

    thread = threading.Thread(target=miner_thread, args=(server_url, miner_id))
    thread.start()
