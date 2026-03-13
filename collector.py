
import psutil
import psycopg2
from datetime import datetime

conn = psycopg2.connect(
    database="system_monitoring",
    user="postgres",
    password="Nitya@123",
    host="localhost",
    port="5432"
)

cursor = conn.cursor()

print("Connected to database")

timestamp = datetime.now()

cpu_percent = psutil.cpu_percent()
cpu_freq = 0

cursor.execute(
    "INSERT INTO cpu_metrics (timestamp, cpu_percent, cpu_freq) VALUES (%s, %s, %s)",
    (timestamp, cpu_percent, cpu_freq)
)

memory = psutil.virtual_memory()
cursor.execute(
    "INSERT INTO memory_metrics (timestamp, total_memory, used_memory, available_memory, memory_percent) VALUES (%s, %s, %s, %s, %s)",
    (timestamp, memory.total, memory.used, memory.available, memory.percent)
)

disk = psutil.disk_usage('/')
cursor.execute(
    "INSERT INTO disk_metrics (timestamp, total_disk, used_disk, free_disk, disk_percent) VALUES (%s, %s, %s, %s, %s)",
    (timestamp, disk.total, disk.used, disk.free, disk.percent)
)

net = psutil.net_io_counters()
cursor.execute(
    "INSERT INTO network_metrics (timestamp, bytes_sent, bytes_recv, packets_sent, packets_recv) VALUES (%s, %s, %s, %s, %s)",
    (timestamp, net.bytes_sent, net.bytes_recv, net.packets_sent, net.packets_recv)
)

conn.commit()

print("System metrics stored successfully at:", timestamp)

cursor.close()
conn.close()
