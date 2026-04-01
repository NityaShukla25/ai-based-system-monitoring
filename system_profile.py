import platform
import socket
import subprocess
from datetime import datetime
import psutil
import psycopg2

def run_command(command):
    try:
        result = subprocess.check_output(command, shell=True, text=True).strip()
        return result
    except Exception:
        return "Not Available"

# -------------------------------
# Fetch basic system details
# -------------------------------
timestamp = datetime.now()

device_name = socket.gethostname()
hostname = socket.gethostname()
manufacturer = "Apple"
model_name = run_command("system_profiler SPHardwareDataType | awk -F': ' '/Model Name/ {print $2}'")
model_year = run_command("system_profiler SPHardwareDataType | awk -F': ' '/Model Identifier/ {print $2}'")
machine_type = "Laptop"

serial_number = run_command("system_profiler SPHardwareDataType | awk -F': ' '/Serial Number/ {print $2}'")

os_name = platform.system()
os_version = platform.mac_ver()[0]
os_build = run_command("sw_vers -buildVersion")
kernel_version = platform.release()
architecture = platform.machine()
platform_info = platform.platform()

processor_name = run_command("sysctl -n machdep.cpu.brand_string")
if processor_name == "Not Available" or processor_name == "":
    processor_name = run_command("system_profiler SPHardwareDataType | awk -F': ' '/Chip/ {print $2}'")

physical_cores = psutil.cpu_count(logical=False)
logical_cores = psutil.cpu_count(logical=True)

base_frequency_mhz = 0
max_frequency_mhz = 0

installed_memory_gb = round(psutil.virtual_memory().total / (1024 ** 3), 2)
memory_type = "Unified Memory"

disk = psutil.disk_usage('/')
total_storage_gb = round(disk.total / (1024 ** 3), 2)
drive_type = "SSD"
file_system = run_command("df -T / | tail -1 | awk '{print $2}'")
main_volume = "/"

display_type = "Built-in Display"
screen_size = "14-inch"
resolution = run_command("system_profiler SPDisplaysDataType | awk -F': ' '/Resolution/ {print $2; exit}'")
refresh_rate = "Not Available"

wifi_adapter = "Wi-Fi"
bluetooth_info = run_command("system_profiler SPBluetoothDataType | awk -F': ' '/Bluetooth Low Energy Supported/ {print $2; exit}'")
mac_address = run_command("ifconfig en0 | awk '/ether/ {print $2}'")
ip_address = socket.gethostbyname(socket.gethostname())

battery_present = True
battery_cycle_count = run_command("system_profiler SPPowerDataType | awk -F': ' '/Cycle Count/ {print $2; exit}'")
try:
    battery_cycle_count = int(battery_cycle_count)
except:
    battery_cycle_count = 0

power_source = run_command("pmset -g batt | head -1")

# -------------------------------
# Connect to PostgreSQL
# -------------------------------
conn = psycopg2.connect(
    database="system_monitoring",
    user="postgres",
    password="Nitya@123",
    host="localhost",
    port="5432"
)

cursor = conn.cursor()

# -------------------------------
# Insert into your table
# Replace system_profile with your actual table name if different
# -------------------------------
cursor.execute(
    """
    INSERT INTO system_profile (
        timestamp, device_name, hostname, manufacturer, model_name, model_year,
        machine_type, serial_number, os_name, os_version, os_build, kernel_version,
        architecture, platform_info, processor_name, physical_cores, logical_cores,
        base_frequency_mhz, max_frequency_mhz, installed_memory_gb, memory_type,
        total_storage_gb, drive_type, file_system, main_volume, display_type,
        screen_size, resolution, refresh_rate, wifi_adapter, bluetooth_info,
        mac_address, ip_address, battery_present, battery_cycle_count, power_source
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """,
    (
        timestamp, device_name, hostname, manufacturer, model_name, model_year,
        machine_type, serial_number, os_name, os_version, os_build, kernel_version,
        architecture, platform_info, processor_name, physical_cores, logical_cores,
        base_frequency_mhz, max_frequency_mhz, installed_memory_gb, memory_type,
        total_storage_gb, drive_type, file_system, main_volume, display_type,
        screen_size, resolution, refresh_rate, wifi_adapter, bluetooth_info,
        mac_address, ip_address, battery_present, battery_cycle_count, power_source
    )
)

conn.commit()
print("System profile stored successfully")

cursor.close()
conn.close()
