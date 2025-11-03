#!/usr/bin/env python3
import os
import time
import re
import subprocess
from datetime import datetime

LOG_FILE = "/home/pi/system_monitor.log"
ERROR_FILE = "/home/pi/system_monitor_error.log"
MAX_ENTRIES = 180  # 3 hours at 1-minute intervals

def get_cpu_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return round(int(f.read()) / 1000, 1)
    except:
        return None

def get_cpu_load():
    return os.getloadavg()[0]  # 1-minute load average

def get_power_status():
    try:
        output = subprocess.check_output(["sudo", "vcgencmd", "get_throttled"], text=True)
        code = int(output.strip().split("=")[1], 16)
        return {
            "undervoltage_now": bool(code & 0x1),
            "throttled_now": bool(code & 0x2),
            "temp_limit_now": bool(code & 0x4),
            "undervoltage_occurred": bool(code & 0x10000),
            "throttled_occurred": bool(code & 0x20000),
            "temp_limit_occurred": bool(code & 0x40000)
        }
    except Exception as e:
        print("Voltage error:", e)
        return {
            "undervoltage_now": "N/A",
            "throttled_now": "N/A",
            "temp_limit_now": "N/A",
            "undervoltage_occurred": "N/A",
            "throttled_occurred": "N/A",
            "temp_limit_occurred": "N/A"
        }

def get_nvme_temp():
    try:
        output = subprocess.check_output(["sudo", "/usr/sbin/nvme", "smart-log", "/dev/nvme0"], text=True)
        for line in output.splitlines():
            if "temperature" in line.lower():
                match = re.search(r"(\d+)\s*°C", line)
                if match:
                    return float(match.group(1))
    except Exception as e:
        print("NVMe error:", e)
        return None

def ping_host(host="github.com", count=1, timeout=2):
    try:
        result = subprocess.run(
            ["ping", "-c", str(count), "-W", str(timeout), host],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return result.returncode == 0  # True if ping succeeded
    except Exception as e:
        print("Ping error:", e)
        return False

def restart_nmcli_connection(connection_name):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} Connection error")
    with open(ERROR_FILE, "a") as file:
        file.write(f"{timestamp} Connection error.\n")
    try:
        # Bring connection down
        subprocess.run(["sudo", "nmcli", "connection", "down", connection_name], check=True)
        # Optional short delay
        subprocess.run(["sleep", "2"])
        # Bring connection up
        subprocess.run(["sudo", "nmcli", "connection", "up", connection_name], check=True)
        return (f"Restarted connection: {connection_name}")
    except subprocess.CalledProcessError as e:
        return (f"Error restarting connection: {e}")

def log_status():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cpu_temp = get_cpu_temp()
    cpu_load = get_cpu_load()
    power = get_power_status()
    nvme_temp = get_nvme_temp()

    ping_text = "OK"
    ping_status_ext = ping_host("obm.one")
    ping_status_int = ping_host("192.168.1.1")
    if not ping_status_ext or not ping_status_int:
        ping_text = restart_nmcli_connection("preconfigured")

    line = (
        f"{timestamp} | "
        f"CPU Temp: {cpu_temp}°C | Load: {cpu_load:.2f} | "
        f"Undervoltage: {power['undervoltage_now']} (Occurred: {power['undervoltage_occurred']}) | "
        f"Throttled: {power['throttled_now']} (Occurred: {power['throttled_occurred']}) | "
        f"Temp Limit: {power['temp_limit_now']} (Occurred: {power['temp_limit_occurred']}) | "
        f"NVMe Temp: {nvme_temp if nvme_temp is not None else 'N/A'}°C | "
        f"Ping: {ping_text}"
    )

    # Read existing log
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE) as f:
            lines = f.readlines()
    else:
        lines = []

    # Insert new line at beginning, and trim to last 180 entries
    lines.insert(0, line + "\n")
    lines = lines[:MAX_ENTRIES:]

    with open(LOG_FILE, "w") as f:
        f.writelines(lines)

if __name__ == "__main__":
    while True:
        log_status()
        time.sleep(60)
