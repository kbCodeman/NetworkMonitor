import socket
import subprocess
import time
from datetime import datetime
import os
import re

# Define the file to log the data
log_file = "internet_connection_log.txt"

# Ensure the log file exists
if not os.path.exists(log_file):
    with open(log_file, "w") as log:
        log.write("Timestamp - Status - Latency - Speed\n")

# Function to check the internet connection via socket
def check_internet(host="8.8.8.8", port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False

def get_ping(host="8.8.8.8"):
    # Adjusted command for Windows compatibility
    result = subprocess.run(["ping", "-n", "1", host], capture_output=True, text=True)
    
    # Windows ping output uses "time=" followed by the latency value
    if "time=" in result.stdout:
        latency = result.stdout.split("time=")[-1].split("ms")[0].strip()
        return float(latency)
    else:
        return None
    
def get_speed():
    temp_file = "temp_speedtest_output.txt"

    # Command to run speedtest-net in a new Command Prompt, showing live output and saving to file
    command = f'start /wait cmd /c "node C:/Users/Keith/AppData/Roaming/npm/node_modules/speedtest-net/bin/index.js > {temp_file}"'
    
    try:
        # Run the command and wait for it to complete, showing live output
        subprocess.run(command, shell=True)

        # Give it a moment to ensure output file is fully written after test completes
        time.sleep(1)

        # Read the final output from the temp file for parsing
        with open(temp_file, "r", encoding="utf-8") as file:
            output = file.read()

        # Use regex to clean ANSI escape codes
        ansi_escape = re.compile(r'(?:\x1B[@-_][0-?]*[ -/]*[@-~])')
        clean_output = ansi_escape.sub('', output)

        # Extract the final Ping, Download, and Upload results from the cleaned output
        match = re.search(r'([\d.]+)\s*ms\s+([\d.]+)\s*Mbps\s+([\d.]+)\s*Mbps', clean_output)

        if match:
            ping = float(match.group(1))
            download = float(match.group(2))
            upload = float(match.group(3))
            return ping, download, upload
        else:
            print("Could not parse the final output. Please check manually.")
            return None, None, None

    except Exception as e:
        print(f"Speed test failed: {e}")
        return None, None, None

# Function to log the connection status and other metrics
def log_status(status, latency=None, speed=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    latency_str = f"Latency: {latency} ms" if latency is not None else "Latency: N/A"
    speed_str = f"Ping: {speed[0]} ms, Download: {speed[1]} Mbps, Upload: {speed[2]} Mbps" if speed else "Speed: N/A"

    with open(log_file, "a") as log:
        log.write(f"{timestamp} - {'Connected' if status else 'Disconnected'} - {latency_str} - {speed_str}\n")
    print(f"{timestamp} - {'Connected' if status else 'Disconnected'} - {latency_str} - {speed_str}")

# Main function to monitor connection
def monitor_connection():
    # Initial checks at the start
    last_status = check_internet()            # Initial connection status
    last_latency = get_ping() if last_status else None    # Initial ping test
    last_speed = get_speed() if last_status else None     # Initial speed test
    log_status(last_status, last_latency, last_speed)     # Log the initial results

    # Set timers for intermittent checks
    ping_interval = 5            # Ping test every 5 seconds
    speed_test_interval = 600    # Speed test every 10 minutes (600 seconds)
    last_ping_time = time.time()
    last_speed_test_time = time.time()

    while True:
        try:
            # Check connection status every second for constant monitoring
            current_status = check_internet()

            # Run ping test intermittently every 5 seconds
            current_time = time.time()
            if current_time - last_ping_time >= ping_interval:
                current_latency = get_ping() if current_status else None
                last_ping_time = current_time
            else:
                current_latency = None

            # Run speed test intermittently every 10 minutes
            if current_time - last_speed_test_time >= speed_test_interval:
                current_speed = get_speed() if current_status else None
                last_speed_test_time = current_time
            else:
                current_speed = None

            # Log only if there's a change or it's a scheduled speed/ping test
            if current_status != last_status or current_latency is not None or current_speed is not None:
                log_status(current_status, current_latency, current_speed)
                last_status = current_status

            time.sleep(1)  # Loop delay for constant connectivity check
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")
            break

if __name__ == "__main__":
    monitor_connection()
