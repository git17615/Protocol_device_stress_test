# protocol.py
import time
import re
import uuid
import base64

# --- Crypto Abstraction ---

class BaseCrypto:
    """
    Abstract base class for a cryptographic system.
    You can implement this with real crypto (like RSA+AES) 
    and plug it into the protocol functions.
    """
    def generate_keypair(self):
        """Generates a (public_key, private_key) tuple."""
        raise NotImplementedError

    def encrypt(self, data: str, public_key: str) -> str:
        """Encrypts data with a public key."""
        raise NotImplementedError

    def decrypt(self, data: str, private_key: str) -> str:
        """Decrypts data with a private key."""
        raise NotImplementedError

    def hash(self, data: str) -> str:
        """Hashes data."""
        raise NotImplementedError

    def generate_session_key(self) -> str:
        """Generates a random session key."""
        raise NotImplementedError

class MockCrypto(BaseCrypto):
    """
    A mock crypto implementation that simulates crypto operations
    with small time delays to make the simulation realistic.
    """
    def __init__(self, crypto_delay=0.005):
        self.crypto_delay = crypto_delay

    def generate_keypair(self):
        priv_key = f"priv_key__{uuid.uuid4()}"
        pub_key = f"pub_key__{priv_key[10:]}"
        return pub_key, priv_key

    # In class MockCrypto

    def encrypt(self, data: str, public_key: str) -> str:
        time.sleep(self.crypto_delay) # Simulate encryption work
        # Base64 encode to make it an opaque string that won't have delimiters
        safe_data = base64.b64encode(data.encode('utf-8')).decode('utf-8')
        return f"e({safe_data})-with-{public_key}"

    # In class MockCrypto

    def decrypt(self, data: str, private_key: str) -> str:
        time.sleep(self.crypto_delay) # Simulate decryption work
        expected_pub = f"pub_key__{private_key[10:]}"

        # Simple regex to parse the mock encrypted data
        match = re.match(r"e\((.*)\)-with-(.*)", data)
        if match:
            content, pub_key = match.groups()
            if pub_key == expected_pub:
                # Decode from base64
                return base64.b64decode(content.encode('utf-8')).decode('utf-8')
            else:
                raise ValueError("Decryption error: Key mismatch")
        raise ValueError("Decryption error: Invalid format")

    # THIS IS THE CORRECT VERSION
    # In class MockCrypto

    def hash(self, data: str) -> str:
        time.sleep(self.crypto_delay / 5.0) # Hashing is faster
        # Create a "hash" and base64 encode it so it's opaque
        hashed = f"hash_of_({data})"
        return base64.b64encode(hashed.encode('utf-8')).decode('utf-8')

    def generate_session_key(self) -> str:
        return f"session_key__{uuid.uuid4()}"

# --- Protocol Message Definitions ---

DELIMITER = "||"

# Message 1: Client A -> Server
def create_client_message(crypto: BaseCrypto, ida: str, idb: str, server_public_key: str) -> str:
    """
    A sends { IDA | IDB | h(IDA|IDB) } encrypted with server pubkey
    """
    payload = f"{ida}{DELIMITER}{idb}"
    hashed_payload = crypto.hash(payload)
    message = f"{payload}{DELIMITER}{hashed_payload}"
    return crypto.encrypt(message, server_public_key)

# Message 2: Server -> Client A
def create_server_message(crypto: BaseCrypto, ida: str, idb: str, session_key: str, 
                          client_a_public_key: str, client_b_public_key: str) -> str:
    """
    Server sends to A:
    { IDA | IDB | K_sess | e(IDA|IDB|K_sess|h(..), pubB) | h(...) } e(..., pubA)
    """
    
    # 1. Create inner message for Client B
    inner_payload = f"{ida}{DELIMITER}{idb}{DELIMITER}{session_key}"
    inner_hash = crypto.hash(inner_payload)
    inner_message = f"{inner_payload}{DELIMITER}{inner_hash}"
    encrypted_inner_message = crypto.encrypt(inner_message, client_b_public_key)
    
    # 2. Create outer message for Client A
    outer_payload = f"{ida}{DELIMITER}{idb}{DELIMITER}{session_key}{DELIMITER}{encrypted_inner_message}"
    outer_hash = crypto.hash(outer_payload)
    outer_message = f"{outer_payload}{DELIMITER}{outer_hash}"
    encrypted_outer_message = crypto.encrypt(outer_message, client_a_public_key)
    
    return encrypted_outer_message

# --- Protocol Handlers ---

def handle_server_protocol(crypto: BaseCrypto, data: str, server_private_key: str, 
                           client_public_key_db: dict) -> str:
    """
    Server logic: Decrypts Msg1, verifies, creates Msg2.
    Returns the encrypted message for Client A.
    """
    # 1. Decrypt and parse message from Client A
    try:
        decrypted_msg = crypto.decrypt(data, server_private_key)
        ida, idb, received_hash = decrypted_msg.split(DELIMITER,maxsplit=2)
    except Exception as e:
        print(f"[Protocol Error] Server failed to parse Msg1: {e}")
        raise ValueError("Invalid client message format.")

    # 2. Verify hash
    expected_hash = crypto.hash(f"{ida}{DELIMITER}{idb}")
    if received_hash != expected_hash:
        raise ValueError("Client hash mismatch.")
        
    # 3. Get client public keys from DB
    if ida not in client_public_key_db or idb not in client_public_key_db:
        raise ValueError(f"Unknown client IDs: {ida} or {idb}")
    
    client_a_public_key = client_public_key_db[ida]
    client_b_public_key = client_public_key_db[idb]

    # 4. Generate session key
    session_key = crypto.generate_session_key()
    
    # 5. Create and return response message (Msg2)
    response_message = create_server_message(
        crypto, ida, idb, session_key, 
        client_a_public_key, client_b_public_key
    )
    return response_message

def handle_client_protocol(crypto: BaseCrypto, data: str, client_a_private_key: str) -> (str, str):
    """
    Client A logic: Decrypts Msg2, verifies.
    Returns the session_key and a status.
    """
    # 1. Decrypt and parse message from Server
    try:
        decrypted_msg = crypto.decrypt(data, client_a_private_key)
        parts = decrypted_msg.split(DELIMITER,maxsplit=4)
        ida, idb, session_key, inner_msg_b, received_hash = parts
    except Exception as e:
        print(f"[Protocol Error] Client failed to parse Msg2: {e}")
        raise ValueError("Invalid server message format.")

    # 2. Verify hash
    payload_to_hash = f"{ida}{DELIMITER}{idb}{DELIMITER}{session_key}{DELIMITER}{inner_msg_b}"
    expected_hash = crypto.hash(payload_to_hash)
    
    if received_hash != expected_hash:
        raise ValueError("Server hash mismatch.")
        
    # 3. Success
    return session_key, "OK"
