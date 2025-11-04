# generate_keys.py
import key_manager
import sys

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python generate_keys.py <max_n_clients>")
        print("Example: python generate_keys.py 1000")
        sys.exit(1)
        
    try:
        MAX_N_CLIENTS = int(sys.argv[1])
    except ValueError:
        print("Error: <max_n_clients> must be an integer.")
        sys.exit(1)

    print(f"--- Generating {MAX_N_CLIENTS} client keys ---")
    key_manager.generate_and_save_keys(MAX_N_CLIENTS)
    print("--- Key generation complete ---")
