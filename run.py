import subprocess
import time

# Start the server process
server_process = subprocess.Popen(['python', 'server.py'])

# Wait for the server to initialize
time.sleep(3)

# Start the client processes
client_processes = []
for i in range(3):
    client_process = subprocess.Popen(['python', 'client.py', 'localhost', f'800{i + 1}'])
    client_processes.append(client_process)

# Wait for one minute
time.sleep(60)

# Terminate all client processes
for client_process in client_processes:
    client_process.terminate()

# Terminate the server process
server_process.terminate()
