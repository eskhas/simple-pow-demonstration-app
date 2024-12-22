# server.py
from flask import Flask, request, jsonify, render_template
import time
import hashlib
import threading

app = Flask(__name__)
lock = threading.Lock()

blockchain = []
difficulty = 5
mining_rewards = {}
miners = []  # Track active miners
mining_status = {}  # Track mining progress for miners

# Helper function to calculate hash
def calculate_hash(index, transactions, previous_hash, timestamp, nonce):
    block_string = f"{index}{transactions}{previous_hash}{timestamp}{nonce}"
    return hashlib.sha256(block_string.encode()).hexdigest()

# Helper function to create a new block
def create_block(transactions):
    previous_hash = blockchain[-1]["hash"] if blockchain else "0" * 64
    index = len(blockchain) + 1
    timestamp = time.time()
    block = {
        "index": index,
        "transactions": transactions,
        "previous_hash": previous_hash,
        "timestamp": timestamp,
        "nonce": 0,
        "hash": "",
    }
    return block

@app.route('/')
def index():
    with lock:
        return render_template('index.html', blockchain=blockchain, rewards=mining_rewards, miners=miners, status=mining_status, difficulty=difficulty)

@app.route('/blockchain', methods=['GET'])
def get_blockchain():
    with lock:
        return jsonify(blockchain), 200

@app.route('/start', methods=['POST'])
def start_mining():
    with lock:
        # Create a block if none exists
        if not blockchain or blockchain[-1]["hash"]:
            block = create_block(transactions=["Reward: Mining"])
            blockchain.append(block)
            notify_miners(block)  # Notify all miners
            return jsonify({"block": block}), 200
        else:
            return jsonify({"error": "Previous block not yet mined."}), 400

@app.route('/mine', methods=['POST'])
def mine_block():
    data = request.json
    miner_id = data.get("miner_id")
    nonce = data.get("nonce")
    time_taken = data.get("time_taken")

    with lock:
        if not blockchain or blockchain[-1]["hash"]:
            return jsonify({"error": "No block to mine."}), 400

        block = blockchain[-1]
        if block["hash"]:
            return jsonify({"error": "Block already mined."}), 400

        # Validate nonce
        hash_value = calculate_hash(
            block["index"], block["transactions"], block["previous_hash"], block["timestamp"], nonce
        )
        if hash_value.startswith("0" * difficulty):
            block["nonce"] = nonce
            block["hash"] = hash_value

            # Update rewards
            mining_rewards[miner_id] = mining_rewards.get(miner_id, 0) + 50
            mining_status[miner_id] = {"status": "Completed", "time": time_taken}

            return jsonify({"message": "Block mined successfully!", "hash": hash_value}), 200
        else:
            return jsonify({"error": "Invalid nonce."}), 400

@app.route('/rewards', methods=['GET'])
def get_rewards():
    with lock:
        return jsonify(mining_rewards), 200

@app.route('/register_miner', methods=['POST'])
def register_miner():
    data = request.json
    miner_id = data.get("miner_id")
    with lock:
        if miner_id not in miners:
            miners.append(miner_id)
            mining_status[miner_id] = {"status": "Idle", "time": None}
        return jsonify({"message": "Miner registered successfully."}), 200

# Notify miners about a new block
def notify_miners(block):
    for miner_id in miners:
        mining_status[miner_id] = {"status": "Mining", "time": None}
        print(f"Notifying miner {miner_id} about new block...")

if __name__ == '__main__':
    app.run(debug=True)