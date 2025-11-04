# key_manager.py
import json
from protocol import MockCrypto # Import your crypto implementation

# Use MockCrypto, but you could swap this for a real one
crypto = MockCrypto() 

# --- File Definitions ---
SERVER_KEYS_FILE = "server_keys.json"
CLIENT_PUBLIC_KEYS_FILE = "client_public_keys.json"
CLIENT_PRIVATE_KEYS_FILE = "client_private_keys.json"

def generate_and_save_keys(max_n: int):
    """
    Generates keys for the server and max_n clients and saves them to files.
    """
    print(f"Generating keys for server and {max_n} clients...")
    
    # 1. Server keys
    server_public, server_private = crypto.generate_keypair()
    server_keys = {
        "public": server_public,
        "private": server_private
    }
    with open(SERVER_KEYS_FILE, 'w') as f:
        json.dump(server_keys, f, indent=2)
    print(f"Saved server keys to {SERVER_KEYS_FILE}")

    # 2. Client keys
    client_public_db = {}
    client_private_db = {}
    
    for i in range(max_n):
        client_id = f"client_{i}"
        pub, priv = crypto.generate_keypair()
        client_public_db[client_id] = pub
        client_private_db[client_id] = priv
        
    with open(CLIENT_PUBLIC_KEYS_FILE, 'w') as f:
        json.dump(client_public_db, f, indent=2)
    print(f"Saved client public keys to {CLIENT_PUBLIC_KEYS_FILE}")

    with open(CLIENT_PRIVATE_KEYS_FILE, 'w') as f:
        json.dump(client_private_db, f, indent=2)
    print(f"Saved client private keys to {CLIENT_PRIVATE_KEYS_FILE}")
    print("Key generation complete.")

def load_server_keys():
    """Loads server public and private keys."""
    with open(SERVER_KEYS_FILE, 'r') as f:
        keys = json.load(f)
    return keys['public'], keys['private']

def load_server_public_key():
    """Loads server public key only."""
    with open(SERVER_KEYS_FILE, 'r') as f:
        keys = json.load(f)
    return keys['public']

def load_client_public_keys():
    """Loads the database of all client public keys."""
    with open(CLIENT_PUBLIC_KEYS_FILE, 'r') as f:
        return json.load(f)

def load_client_private_keys():
    """Loads the database of all client private keys."""
    with open(CLIENT_PRIVATE_KEYS_FILE, 'r') as f:
        return json.load(f)
