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
    log.write("Timestamp - Status - Latency - Speed - Band\n")

# Function to check the internet connection via socket
def check_internet(host="8.8.8.8", port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False

# Function to determine if the Wi-Fi is on 2.4 GHz or 5 GHz
def get_wifi_band():
    try:
        # Run the netsh command to get Wi-Fi interface details
        result = subprocess.run(["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True)
        output = result.stdout

        # Check for expected lines and parse frequency
        if "Radio type" in output or "Frequency" in output:
            # Check for indications of 2.4 GHz or 5 GHz in the output
            if "5 GHz" in output or "802.11a" in output or "802.11ac" in output:
                return "5 GHz"
            elif "2.4 GHz" in output or "802.11b" in output or "802.11g" in output or "802.11n" in output:
                return "2.4 GHz"
        return "Unknown"  # Return "Unknown" if frequency details aren't found
    except Exception as e:
        print(f"Error detecting Wi-Fi band: {e}")
        return "Error"

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
    # Connection status
    status_text = "Connected" if status else "Disconnected"

    # Format latency
    latency_str = f"Latency: {latency} ms" if latency is not None else "Latency: N/A"

    # Format speed
    if speed:
        speed_str = f"Ping: {speed[0]} ms, Download: {speed[1]} Mbps, Upload: {speed[2]} Mbps"
    else:
        speed_str = "Speed: N/A"

    # Get Wi-Fi band information
    wifi_band = get_wifi_band()

    # Timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Print the log to console
    print(f"{timestamp} - {status_text} - {latency_str} - {speed_str} - Band: {wifi_band}")

    # Log to file
    with open(log_file, "a") as log:
        log.write(f"{timestamp} - {status_text} - {latency_str} - {speed_str} - Band: {wifi_band}\n")

# Main function to monitor connection
def monitor_connection():
    last_status = check_internet()
    last_latency = get_ping() if last_status else None
    last_speed = get_speed() if last_status else None
    log_status(last_status, last_latency, last_speed)

    ping_interval = 30
    speed_test_interval = 600
    last_ping_time = time.time()
    last_speed_test_time = time.time()

    while True:
        try:
            current_status = check_internet()
            current_time = time.time()

            if current_time - last_ping_time >= (1 if last_latency and last_latency > 80 else ping_interval):
                current_latency = get_ping() if current_status else None
                last_ping_time = current_time

                if current_latency and current_latency > 80:
                    print(f"High latency detected: {current_latency} ms")

            else:
                current_latency = None

            if current_time - last_speed_test_time >= speed_test_interval:
                current_speed = get_speed() if current_status else None
                last_speed_test_time = current_time
            else:
                current_speed = None

            if current_status != last_status or current_latency is not None or current_speed is not None:
                log_status(current_status, current_latency, current_speed)
                last_status = current_status
                last_latency = current_latency

            time.sleep(1)
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")
            break

if __name__ == "__main__":
    monitor_connection()
