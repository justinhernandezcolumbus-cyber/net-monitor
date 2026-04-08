# net-monitor

A Python tool for monitoring home internet performance — measuring latency, jitter, packet loss, and speed over time, logging results to a structured CSV, and alerting when service drops below defined thresholds.

---

## Why I Built This

I switched internet providers last year chasing a better deal. The service turned out to be worse than what I had before — but I had no data to back that up beyond frustration. This tool fixes that.

It runs quietly in the background, logs every measurement to a CSV, and notifies me when something degrades below a threshold I define. The data collected was then fed into Splunk Enterprise to answer three operational questions:

- **Should I get a new provider?**
- **Is the service matching what my provider advertises?**
- **What times of day is performance worst?**

Beyond the practical value, this project was also a deliberate exercise in building something end-to-end in Python — a language I didn't have experience in. The operational patterns here mirror what I worked with professionally in Splunk and ServiceNow: scheduled data collection, structured logging, threshold-based alerting, and operational visibility.

---

## What It Does

- **Pings a target host** (default: Google DNS at `8.8.8.8`) every 5 minutes and records average latency, jitter, and packet loss
- **Runs a speed test** every 30 minutes and records download and upload throughput
- **Logs every result** to a structured CSV file with timestamps
- **Fires a desktop alert** when any metric crosses a configured threshold
- **Runs cross-platform** — tested on Windows 11 (wired) and macOS Big Sur (wireless) simultaneously

---

## Requirements

- Python 3.8 or higher
- Windows 10/11 or macOS

### Install dependencies

```bash
pip install speedtest-cli schedule plyer
```

| Package | Purpose |
|---|---|
| `speedtest-cli` | Measures download/upload speed via Speedtest.net |
| `schedule` | Runs checks on a timed interval |
| `plyer` | Sends desktop notifications (Windows/macOS) |

---

## Setup

1. Clone this repository
2. Install dependencies (see above)
3. Open `monitor.py` and review the `CONFIG` block — adjust thresholds to match your plan's advertised speeds

```python
CONFIG = {
    "ping_host":             "8.8.8.8",
    "ping_count":            10,
    "thresholds": {
        "max_latency_ms":    80,      # alert if avg latency exceeds 80ms
        "max_packet_loss":   5,       # alert if packet loss exceeds 5%
        "min_download_mbps": 50.0,    # alert if download falls below 50 Mbps
        "min_upload_mbps":   5.0,     # alert if upload falls below 5 Mbps
    },
    "ping_interval_minutes":  5,
    "speed_interval_minutes": 30,
    "alert_cooldowns":        15,
}
```

---

## Usage

### Run the full monitor (runs until you stop it with Ctrl+C)
```bash
python monitor.py
```

### macOS — prevent sleep while running
```bash
caffeinate python3 monitor.py
```

---

## Output

All results are written to `net_monitor.csv` in the same directory. Columns:

| Column | Description |
|---|---|
| `timestamp` | Date and time of the measurement |
| `check_type` | `ping` or `speed` |
| `avg_latency_ms` | Average round-trip latency in milliseconds |
| `jitter` | Difference between min and max latency — measures stability |
| `packet_loss_pct` | Percentage of packets lost |
| `download_mbps` | Download speed in Mbps (speed tests only) |
| `upload_mbps` | Upload speed in Mbps (speed tests only) |
| `alert_triggered` | `True` if a threshold was breached |
| `alert_reason` | Human-readable description of what triggered the alert |

### Why jitter?

Average latency alone can look acceptable while the connection is actually unstable. A connection with `avg=50ms` but `jitter=420ms` is far worse than one with `avg=30ms` and `jitter=8ms`. Jitter exposes instability that averages hide.

---

## Cross-Platform Testing

This tool was run simultaneously on two devices connected to the same Verizon 5G home internet connection:

| Device | OS | Connection |
|---|---|---|
| Desktop | Windows 11 | Wired (Ethernet) |
| MacBook Pro 2015 | macOS Big Sur | Wireless (Wi-Fi) |

Sample data from both devices is included in the `/splunk` directory. See `splunk/splunk_integration.md` for the full analysis workflow.

### Key finding

Jitter spikes occurred simultaneously on both devices — wired and wireless — pointing to instability in the provider's network rather than home hardware. This is the kind of data-driven conclusion that's difficult to reach without structured monitoring.

---

## Alert Behavior

When a threshold is breached the tool:

1. Fires a desktop notification
2. Logs the alert reason to the CSV
3. Prints the alert to the console

Alerts respect a **15-minute cooldown** per issue type — so if your connection stays degraded you won't get a notification every 5 minutes.

If desktop notifications are unavailable (older macOS, missing dependencies), the tool falls back to console output and continues running without interruption.

---

## Architecture

```
MAIN
  └── run_scheduler()
        ├── check_ping()  — every 5 minutes
        │     ├── run_ping()          # measure latency, jitter, packet loss
        │     ├── check_thresholds()  # evaluate against CONFIG
        │     ├── send_alert()        # notify if threshold breached
        │     └── write_log()         # append row to CSV
        └── check_speed()  — every 30 minutes
              ├── run_speedtest()     # measure download/upload
              ├── check_thresholds()  # evaluate against CONFIG
              ├── send_alert()        # notify if threshold breached
              └── write_log()         # append row to CSV
```

Each layer has one clear responsibility. `check_ping()` and `check_speed()` are orchestrator functions — they call the focused measurement functions and handle everything that needs to happen with the results. The same `check_thresholds()`, `send_alert()`, and `write_log()` functions serve both check types, keeping the codebase DRY.

---

## Splunk Integration

Data collected by this tool was ingested into a free trial of Splunk Enterprise to build an operational dashboard. See [`splunk/splunk_integration.md`](splunk/splunk_integration.md) for the full workflow including data input configuration, SPL queries, and dashboard screenshots.

