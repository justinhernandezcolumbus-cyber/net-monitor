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
                "latency_ms",
                "packet_loss_pct",
                "download_mbps",
                "upload_mbps",
                "alert_triggered",
                "alert_reason",
                ])
    else:
        pass   # file already exists, do nothing
# -- MAIN ------------------------------------------------
init_log()