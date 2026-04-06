# ---1. IMPORTS----------------------------------------
# Standard library (no install needed)
# - subprocess: for running the ping command
# - platform:   for detecting the OS
# - csv:        for writing log files
# - datetime    for timestamps
# - time        for the scheduler loop
# - sys:        for reading command line arguments

# Third Party (these are in requirements.txt)
# - schedule   for running checks on a timer
# - speedtest for download/upload measurement
# - plyer     for desktop notification

#--2. CONFIG ------------------------------------------
#A single dictionary called CONFIG that holds:
# - ping host
# - ping count
# - thresholds (latency, packet loss, download, upload)
# - log file name
# - check intervals
# - alert cooldown

# --3. OS DETECTION -----------------------------------
# Use platform.system() to detect the OS
# It returns "Windows", "Linux", or "Darwin" (macOS)
# Store the result, and use it later when building the ping command

import csv          # reads and writes CSV files
import datetime     # timestamps
import os           # allows app to interact with OS
import platform     # detects the OS
import re           # searches for patterns in text (used to parse ping output)
import schedule     # runs checks on a timer
import speedtest    # measures download/upload speed
import subprocess   # runs system commands like ping
import sys          # reads command line arguments (like "python monitor.py ping")
import time         # sleep, timing

from plyer import notification   # sends desktop alerts

log_file_name = "net_monitor.csv"

CONFIG = {
    "ping_host": "8.8.8.8",        # string
    "ping_count": 10,              # integer
    "thresholds": {
        "max_latency_ms": 80,      # integer
        "max_packet_loss": 5,      # integer
        "min_download_mbps": 25.0, # float
        "min_upload_mbps": 5.0,    # float
    },
    "log_file_name": log_file_name,           # string
    "ping_interval_minutes": 5,    # integer
    "speed_interval_minutes": 30,  # integer
    "alert_cooldowns": 15,         # integer
}

detected_os = platform.system() # variable_name = some_function()
print(f"Detected OS: {detected_os}")

# --4. LOG INITIALIZATION ----------------------------
# Check if the log file exists
# If not, create it and write the header row
# If it does exist, leave it alone

def init_log():
    if not os.path.exists(CONFIG["log_file_name"]):
        # open the file and write the header row
        with open(CONFIG["log_file_name"], "w", newline="") as f:
            writer = csv.writer(f) # creates a CSV writer object pointed at your open file
            writer.writerow([
                "timestamp",
                "check_type",
                "avg_latency_ms",
                "jitter",
                "packet_loss_pct",
                "download_mbps",
                "upload_mbps",
                "alert_triggered",
                "alert_reason",
                ])
    else:
        pass   # file already exists, do nothing
    
def run_ping():
    # 1. build the correct ping command based on detected_os
    if detected_os == "Windows":
        command = ["ping", "-n", str(CONFIG["ping_count"]), CONFIG["ping_host"]]
    else: 
        command = ["ping", "-c", str(CONFIG["ping_count"]), CONFIG["ping_host"]]
    # 2. run it with subprocess
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        print("Ping timed out.")
        return None, None, None
    # 3. parse latency from the output using regex
    if detected_os == "Windows":
        avg_match = re.search(r"Average\s*=\s*(\d+)ms", result.stdout)
        min_match = re.search(r"Minimum\s*=\s*(\d+)ms", result.stdout)
        max_match = re.search(r"Maximum\s*=\s*(\d+)ms", result.stdout)
    else:
        avg_match = re.search(r"round-trip min/avg/max/stddev\s*=\s*[\d.]+/([\d.]+)/", result.stdout)
        min_match = re.search(r"round-trip min/avg/max/stddev\s*=\s*([\d.]+)/", result.stdout)
        max_match = re.search(r"round-trip min/avg/max/stddev\s*=\s*[\d.]+/[\d.]+/([\d.]+)/", result.stdout)
    avg_latency = int(float(avg_match.group(1))) if avg_match else None
    min_latency = int(float(min_match.group(1))) if min_match else None
    max_latency = int(float(max_match.group(1))) if max_match else None
    jitter = max_latency - min_latency if min_latency and max_latency else None
    # 4. parse packet loss from the output using regex
    if detected_os == "Windows":
        loss_match = re.search(r"\((\d+)%", result.stdout)
    else:
        loss_match = re.search(r"(\d+\.?\d*)% packet loss", result.stdout)
    packet_loss = int(float(loss_match.group(1))) if loss_match else None
    # 5. return both values
    print(f"Latency: {avg_latency}ms | Jitter: {jitter}ms | Packet Loss: {packet_loss}%")
    return avg_latency, jitter, packet_loss

def write_log(check_type, avg_latency=None, jitter=None, 
              packet_loss=None, download=None, upload=None,
              alert_triggered=False, alert_reason=""):
    
    with open(CONFIG["log_file_name"], "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            check_type,
            avg_latency,
            jitter,
            packet_loss,
            download,
            upload,
            alert_triggered,
            alert_reason
        ])

def run_speedtest():
    try:
        st = speedtest.Speedtest()
        st.get_best_server()
        download = round(st.download() / 1_000_000, 2)  # convert to Mbps
        upload = round(st.upload() / 1_000_000, 2)      # convert to Mbps
        print(f"Download: {download:.2f} Mbps | Upload: {upload:.2f} Mbps")
        return download, upload
    except Exception as e:
        print(f"Speed test failed: {e}")
        return None, None
        
def check_thresholds(avg_latency=None, packet_loss=None, download=None, upload=None):
    
    alerts = []   # empty list

    if avg_latency is not None and avg_latency > CONFIG["thresholds"]["max_latency_ms"]:
        alerts.append(f"High latency: {avg_latency}ms")

    if packet_loss is not None and packet_loss > CONFIG["thresholds"]["max_packet_loss"]:
        alerts.append(f"High packet loss: {packet_loss}%")
        
    if download is not None and download < CONFIG["thresholds"]["min_download_mbps"]:
        alerts.append(f"Low download speed: {download} Mbps")
        
    if upload is not None and upload < CONFIG["thresholds"]["min_upload_mbps"]:
        alerts.append(f"Low upload speed: {upload} Mbps")

    alert_triggered = len(alerts) > 0   # True if list has anything in it
    alert_reason = "; ".join(alerts)     # joins list into one string
    return alert_triggered, alert_reason

def send_alert(alert_triggered, alert_reason):
    if alert_triggered:
        #fire the notification
        notification.notify(
            title="Net Monitor",
            message=alert_reason,
            app_name="Net Monitor",
            timeout=10
        )

def check_ping():
    avg_latency, jitter, packet_loss = run_ping()
    alert_triggered, alert_reason = check_thresholds(avg_latency=avg_latency, packet_loss=packet_loss)
    send_alert(alert_triggered, alert_reason)
    write_log("ping", avg_latency=avg_latency, jitter=jitter, packet_loss=packet_loss,
              alert_triggered=alert_triggered, alert_reason=alert_reason)

def check_speed():
    download, upload = run_speedtest()
    alert_triggered, alert_reason = check_thresholds(download=download, upload=upload)
    send_alert(alert_triggered, alert_reason)
    write_log("speed", download=download, upload=upload,
              alert_triggered=alert_triggered, alert_reason=alert_reason)

def run_scheduler():
    schedule.every(CONFIG["ping_interval_minutes"]).minutes.do(check_ping)
    schedule.every(CONFIG["speed_interval_minutes"]).minutes.do(check_speed)
    print("Scheduler started. Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(10)

# -- MAIN ------------------------------------------------
init_log()         # set up the log file
check_ping()       # run immediately on start
run_scheduler()    # then hand off to the schedule