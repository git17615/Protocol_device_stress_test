# simulation.py
import socket
import time
import concurrent.futures
import random
import numpy as np
import matplotlib.pyplot as plt
import key_manager
import protocol
import base64 # Make sure this import is here

# --- Configuration ---
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 65432
CLIENT_MAX_WORKERS = 150  # Max threads for running client simulations
CLIENT_SOCKET_TIMEOUT = 5.0 # Timeout for a single client's request

# Simulation parameters
N_LIST = [100,1000 ]
ROUND_PERCENTAGES = [0.01, 0.05, 0.10, 0.25, 0.50]
NUM_TRIALS = 3 # Run 3 instances for each N

# Round Timeout
TIMEOUT_BASE_SECONDS = 10.0
TIMEOUT_PER_CLIENT_PAIR = 0.5

# --- Global Resources ---
CRYPTO = protocol.MockCrypto()
try:
    SERVER_PUBLIC_KEY = key_manager.load_server_public_key()
    CLIENT_PRIVATE_KEY_DB = key_manager.load_client_private_keys()
    print("Simulation: Loaded server public key and all client private keys.")
except FileNotFoundError:
    print("Error: Key files not found. Please run 'generate_keys.py' first.")
    exit(1)


def run_client_session(client_a_id: str, client_b_id: str) -> float | None:
    """
    Simulates a single Client A initiating an AKE with Client B.
    Returns AKE time in milliseconds, or None on failure.
    """
    try:
        client_a_private_key = CLIENT_PRIVATE_KEY_DB[client_a_id]
        
        # 1. Create message
        message = protocol.create_client_message(
            CRYPTO,
            client_a_id,
            client_b_id,
            SERVER_PUBLIC_KEY
        )
        
        # 2. Connect and send
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((SERVER_HOST, SERVER_PORT))
            sock.settimeout(CLIENT_SOCKET_TIMEOUT)
            
            start_time = time.perf_counter()
            
            sock.sendall(message.encode('utf-8'))
            
            # 3. Wait for response
            response = sock.recv(4096)
            
            end_time = time.perf_counter()
            
            if not response:
                print(f"[{client_a_id}] Error: Empty response from server.")
                return None

            # 4. Process response
            session_key, status = protocol.handle_client_protocol(
                CRYPTO,
                response.decode('utf-8'),
                client_a_private_key
            )
            
            if status == "OK":
                ake_time_ms = (end_time - start_time) * 1000
                return ake_time_ms
            else:
                print(f"[{client_a_id}] Error: Protocol failed with status {status}.")
                return None

    except socket.timeout:
        print(f"[{client_a_id}] Error: Connection to server timed out.")
        return None
    except Exception as e:
        print(f"[{client_a_id}] Error: {e}")
        return None

def plot_average_results(results: dict, percentages: list):
    """
    Uses matplotlib to plot the FINAL AVERAGED results.
    """
    print("\nGenerating average results plot...")
    plt.figure() # Create a new figure
    x_labels = [f"{int(p*100)}%" for p in percentages]
    
    for n, avg_times in results.items():
        # Plot, replacing any 'nan' (from failed rounds) with 0 for plotting
        plt.plot(x_labels, np.nan_to_num(avg_times), marker='o', label=f'N = {n} (Avg)')

    plt.xlabel("Percentage of Client Pairs Interacting")
    plt.ylabel("Average AKE Time (ms)")
    plt.title("Average AKE Time vs. Client Load (Across All Trials)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    
    filename = "ake_time_AVERAGE_concurrency_plot.png"
    plt.savefig(filename)
    print(f"Average plot saved to {filename}")

# In simulation.py

def plot_all_trials_results(results: dict, percentages: list):
    """
    Uses matplotlib to plot EVERY INDIVIDUAL TRIAL.
    """
    print("\nGenerating all-trials plot...")
    plt.figure() # Create a new figure
    x_labels = [f"{int(p*100)}%" for p in percentages]
    
    # --- NEW: Define colors ---
    # Use matplotlib's default color cycle (C0=blue, C1=orange, C2=green)
    # This will make all N=100 lines blue, N=200 orange, etc.
    colors = {
        100: 'C0',
        200: 'C1',
        300: 'C2'
    }
    # --- END NEW ---
    
    # Use different markers for each N to make it clearer
    markers = {100: 'o', 200: 's', 300: '^'}
    # Use different line styles for each trial (assuming max 3 trials)
    linestyles = {1: '-', 2: '--', 3: ':'}
    
    for label, trial_times in results.items():
        # Parse the label "N=100, Trial 1"
        n = int(label.split(',')[0].split('=')[1])
        trial_num = int(label.split(',')[1].split(' ')[2])
        
        # --- NEW: Get the color for this N ---
        color = colors.get(n, 'black') # Fallback to black
        # --- END NEW ---
        
        plt.plot(
            x_labels, 
            np.nan_to_num(trial_times), 
            marker=markers.get(n, '.'), 
            linestyle=linestyles.get(trial_num, '-'),
            color=color,  # <-- ADDED THIS
            label=label
        )

    plt.xlabel("Percentage of Client Pairs Interacting")
    plt.ylabel("Average AKE Time (ms)")
    plt.title("Individual Trial AKE Time vs. Client Load")
    # Put legend outside the plot
    plt.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
    plt.grid(True)
    plt.tight_layout(rect=[0, 0, 0.85, 1]) # Adjust layout to make room for legend
    
    filename = "ake_time_ALL_TRIALS_concurrency_plot.png"
    plt.savefig(filename)
    print(f"All-trials plot saved to {filename}")

def main():
    """
    Main simulation orchestrator.
    """
    print("--- Starting AKE Simulation ---")
    
    # This will store the *final* averaged results for plotting
    # { 100: [final_avg_r1, final_avg_r2, ...], 200: [...] }
    final_plot_results = {}
    
    # This will store every single trial for the second plot
    # { "N=100, Trial 1": [r1, r2, ...], "N=100, Trial 2": [...], ... }
    all_trial_results = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=CLIENT_MAX_WORKERS) as executor:
        
        for n in N_LIST:
            print(f"\n[N = {n}] Starting tests for {n} total clients.")
            
            # This list will store the results of all trials for this N
            # e.g., [[trial1_r1, trial1_r2,...], [trial2_r1, trial2_r2,...]]
            n_trial_results = []
            
            # --- NEW TRIAL LOOP ---
            for trial in range(NUM_TRIALS):
                print(f"  [N={n}] Starting Trial {trial + 1}/{NUM_TRIALS}...")
                
                # Get the pool of client IDs available for this N
                client_id_pool = [f"client_{i}" for i in range(n)]
                
                # This list will store the 5 round averages for *this single trial*
                trial_round_averages = []
                
                for percent in ROUND_PERCENTAGES:
                    
                    num_pairs = int(n * percent)
                    if num_pairs == 0:
                        print(f"    Skipping Round {int(percent*100)}% (0 pairs).")
                        trial_round_averages.append(np.nan)
                        continue

                    print(f"    Running Round {int(percent*100)}% ({num_pairs} pairs)...")
                    
                    # Select random, unique pairs for this round
                    try:
                        shuffled_clients = random.sample(client_id_pool, num_pairs * 2)
                    except ValueError:
                        print(f"    Error: Not enough unique clients in pool for {num_pairs} pairs.")
                        continue
                        
                    client_as = shuffled_clients[:num_pairs]
                    client_bs = shuffled_clients[num_pairs:]
                    
                    # Submit all client tasks to the thread pool
                    futures = []
                    for i in range(num_pairs):
                        futures.append(executor.submit(
                            run_client_session, 
                            client_as[i], 
                            client_bs[i]
                        ))
                    
                    round_timeout = TIMEOUT_BASE_SECONDS + (num_pairs * TIMEOUT_PER_CLIENT_PAIR)
                    
                    round_ake_times = []
                    try:
                        for future in concurrent.futures.as_completed(futures, timeout=round_timeout):
                            result_ms = future.result()
                            if result_ms is not None:
                                round_ake_times.append(result_ms)
                                
                    except concurrent.futures.TimeoutError:
                        print(f"      [Round FAILED] Round timed out after {round_timeout}s.")
                        for f in futures: f.cancel()
                    
                    # --- Report Summary for this Round ---
                    success_count = len(round_ake_times)
                    fail_count = num_pairs - success_count
                    
                    if success_count > 0:
                        avg_ake = np.mean(round_ake_times)
                        trial_round_averages.append(avg_ake) # Store avg for this round
                        print(f"      Summary (Trial {trial+1}): Success={success_count}/{num_pairs} | Avg AKE: {avg_ake:.2f} ms")
                    else:
                        trial_round_averages.append(np.nan) # Record NaN for plotting
                        print(f"      Summary (Trial {trial+1}): FAILED. {fail_count}/{num_pairs} sessions failed.")

                # After all 5 rounds, add this trial's results to the N-list
                n_trial_results.append(trial_round_averages)
                
                # Store this trial's data for the "all trials" plot
                trial_label = f"N={n}, Trial {trial+1}"
                all_trial_results[trial_label] = trial_round_averages
            
            # --- END TRIAL LOOP ---
            
            # Now, average the results across all trials for this N
            # np.nanmean vertically averages the columns, safely ignoring NaNs (failed rounds)
            final_averages_for_n = np.nanmean(n_trial_results, axis=0)
            final_plot_results[n] = final_averages_for_n

            print(f"\n[N = {n}] Final Avg AKE Times (across {NUM_TRIALS} trials):")
            for i, avg in enumerate(final_averages_for_n):
                print(f"  Round {int(ROUND_PERCENTAGES[i]*100)}%: {avg:.2f} ms")


    # --- Final Plotting ---
    # Call the plot function for the Averages
    plot_average_results(final_plot_results, ROUND_PERCENTAGES)
    
    # Call the plot function for All Individual Trials
    plot_all_trials_results(all_trial_results, ROUND_PERCENTAGES)
    
    print("--- Simulation Complete ---")


if __name__ == "__main__":
    # Ensure server is running before starting
    print("Please make sure 'server.py' is running in another terminal.")
    try:
        input("Press Enter to start the simulation...")
    except KeyboardInterrupt:
        print("\nSimulation cancelled.")
        exit(0)
        
    main()