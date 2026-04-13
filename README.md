# Secure Protocol Simulation

This project simulates a client-server authentication/key exchange protocol and allows experimentation with different protocol designs.

## Project Structure

Ensure all files are placed in the same directory:

- server.py — Server-side logic
- protocol.py — Core protocol implementation (edit this to implement different protocols)
- simulation.py — Runs simulation and collects metrics
- key_manager.py — Key handling utilities
- generate_keys.py — Generates required cryptographic keys

## Setup

Install required dependencies:

pip install numpy matplotlib

## Running the Project

### Windows

Open two terminals:

Terminal 1:
python generate_keys.py
python simulation.py

Terminal 2:
python server.py

### WSL / Linux

Open two terminals:

Terminal 1:
python3 generate_keys.py
python3 simulation.py

Terminal 2:
python3 server.py

## Output

After execution, the following plots are generated:

- ake_time_ALL_TRIALS_plot.png
- ake_time_AVERAGE_plot.png

To view them:

eog ake_time_ALL_TRIALS_plot.png
eog ake_time_AVERAGE_plot.png

Note: Install Eye of GNOME (eog) if not available:
sudo apt install eog

## Customizing the Protocol

Modify the following functions in protocol.py to implement different protocols:

- client_create_initial_message()  (line ~52)
- client_verify_server_response()  (line ~95)
- server_process_client_request()  (line ~152)

## Custom Cryptographic Primitives

You may modify or replace cryptographic operations (e.g., encryption, decryption, hashing) in:

- protocol.py
- server.py

## Notes

- Ensure the server is running before or alongside the simulation.
- All scripts must be executed from the same directory.
- Python 3 is recommended.
