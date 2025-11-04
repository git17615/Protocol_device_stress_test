The repo contains
--> server.py
--> protocol.py ## edit this to c
--> simulation.py
--> key_manager.py
--> generate_keys.py

Save all the files in the same folder.

cmd 0: pip install numpy matplotlib ## in terminal 1

Windows: cmd 0--> cmd 1 --> cmd 2 -->cmd 3
cmd 1: python generate_keys.py ## in terminal 1
cmd 2: python server.py ##in terminal 2
cmd 3: python simulation.py ##in terminal 1

WSL: run cmd 0 -->cmd A-->cmd B-->cmd C
cmd A: python3 generate_keys.py ## in terminal 1
cmd B: python3 server.py ## in terminal 2
cmd C: python3 simulation.py #in terminal 1

OUTPUT:
check the images: eog ake_time_ALL_TRIALS_plot.png
                  eog ake_time_AVERAGE_plot.png

use eog {need to install eog}

functions to edit for implementing different protocols(in protocol.py file) 
server_process_client_request() #line 152
client_verify_server_response() #line 95
client_create_initial_message() #line 52
## can change the basic (encrypt, decrypt, hash) in server.py and protocol.py{depending on preference}

variables to change:




