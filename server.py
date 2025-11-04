# server.py
import socket
import time
import concurrent.futures
import key_manager
import protocol

# --- Configuration ---
HOST = '127.0.0.1'
PORT = 65432
MAX_WORKERS = 50       # Max threads in the server's thread pool
PER_CLIENT_TIMEOUT = 10.0 # Timeout for a single socket connection

# --- Global Resources ---
CRYPTO = protocol.MockCrypto()
try:
    SERVER_PUBLIC_KEY, SERVER_PRIVATE_KEY = key_manager.load_server_keys()
    CLIENT_PUBLIC_KEY_DB = key_manager.load_client_public_keys()
    print(f"Server keys and DB for {len(CLIENT_PUBLIC_KEY_DB)} clients loaded.")
except FileNotFoundError:
    print("Error: Key files not found. Please run 'generate_keys.py' first.")
    exit(1)

def handle_connection(conn: socket.socket, addr):
    """
    Handles a single client connection.
    This function is executed by a worker thread.
    """
    client_ip, client_port = addr
    print(f"[Server] Connection from {client_ip}:{client_port}")
    
    try:
        conn.settimeout(PER_CLIENT_TIMEOUT)
        
        # 1. Receive data
        data = conn.recv(4096)
        if not data:
            print(f"[Server] No data from {addr}. Closing.")
            return

        start_time = time.perf_counter()
        
        # 2. Process in protocol.py
        response_message = protocol.handle_server_protocol(
            CRYPTO,
            data.decode('utf-8'),
            SERVER_PRIVATE_KEY,
            CLIENT_PUBLIC_KEY_DB
        )
        
        # 3. Send response
        conn.sendall(response_message.encode('utf-8'))
        
        end_time = time.perf_counter()
        
        # 4. Log AKE time (as requested)
        ake_time_ms = (end_time - start_time) * 1000
        print(f"[Server] Handled request for {addr}. AKE Time: {ake_time_ms:.2f} ms")

    except socket.timeout:
        print(f"[Server Error] Connection from {addr} timed out.")
    except Exception as e:
        print(f"[Server Error] Failed to handle {addr}: {e}")
    finally:
        conn.close()

def main():
    """
    Main server loop.
    """
    # Create a thread pool to handle clients
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((HOST, PORT))
            server_socket.listen()
            print(f"[Server] Listening on {HOST}:{PORT} with {MAX_WORKERS} workers...")
            
            while True:
                try:
                    # Wait for a connection
                    conn, addr = server_socket.accept()
                    
                    # Submit the connection to the thread pool
                    executor.submit(handle_connection, conn, addr)
                
                except KeyboardInterrupt:
                    print("\n[Server] Shutting down...")
                    break
                except Exception as e:
                    print(f"[Server] Main loop error: {e}")

if __name__ == "__main__":
    main()
