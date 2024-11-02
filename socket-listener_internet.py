import socket
import subprocess
import time
from datetime import datetime
import os
import re

# Define the logs folder and ensure it exists
log_folder = "logs"
os.makedirs(log_folder, exist_ok=True)

# Define the timestamped log file name
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file = os.path.join(log_folder, f"internet_connection_log_{timestamp}.txt")

# Create the log file with a header
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

# Function to get ping latency
def get_ping(host="8.8.8.8"):
    result = subprocess.run(["ping", "-n", "1", host], capture_output=True, text=True)
    if "time=" in result.stdout:
        latency = result.stdout.split("time=")[-1].split("ms")[0].strip()
        return float(latency)
    else:
        return None

# Function to get internet speed
def get_speed():
    temp_file = "temp_speedtest_output.txt"
    command = f'start /wait cmd /c "node C:/Users/Keith/AppData/Roaming/npm/node_modules/speedtest-net/bin/index.js > {temp_file}"'
    
    try:
        subprocess.run(command, shell=True)
        time.sleep(1)

        with open(temp_file, "r", encoding="utf-8") as file:
            output = file.read()

        ansi_escape = re.compile(r'(?:\x1B[@-_][0-?]*[ -/]*[@-~])')
        clean_output = ansi_escape.sub('', output)

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
    
def monitor_connection():
    # Initial checks at the start
    last_status = check_internet()
    last_latency = get_ping() if last_status else None
    last_speed = get_speed() if last_status else None
    log_status(last_status, last_latency, last_speed)

    # Set timers for intermittent checks
    ping_interval = 30            # Ping test every 30 seconds
    speed_test_interval = 600      # Speed test every 10 minutes (600 seconds)
    last_ping_time = time.time()
    last_speed_test_time = time.time()

    while True:
        try:
            current_status = check_internet()
            current_time = time.time()

            # Ping every 30 seconds normally or every second if latency > 80 ms
            if current_time - last_ping_time >= (1 if last_latency and last_latency > 80 else ping_interval):
                current_latency = get_ping() if current_status else None
                last_ping_time = current_time

                # Check if latency is above 80 ms and adjust monitoring interval
                if current_latency and current_latency > 80:
                    print(f"High latency detected: {current_latency} ms")  # Alert for high ping

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
                last_latency = current_latency  # Update last latency

            time.sleep(1)  # Loop delay for constant connectivity check
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")
            break

if __name__ == "__main__":
    monitor_connection()
