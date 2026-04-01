import time
import psutil
from db import get_connection
from config import COLLECTION_INTERVAL
from static_collector import get_or_create_host
from process_collector import (
    collect_process_metrics,
    collect_process_connections,
    collect_process_open_files,
    collect_process_threads
)
from feature_builder import build_training_features


def get_training_row_count(host_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*)
        FROM model_training_features
        WHERE host_id = %s
    """, (host_id,))

    count = cur.fetchone()[0]

    cur.close()
    conn.close()
    return count


def collect_system_runtime_info(host_id):
    boot_time = psutil.boot_time()
    uptime_seconds = int(time.time() - boot_time)

    try:
        load1, load5, load15 = psutil.getloadavg()
    except Exception:
        load1, load5, load15 = 0, 0, 0

    total_processes = 0
    running = 0
    sleeping = 0
    zombie = 0
    stopped = 0
    thread_count = 0

    for p in psutil.process_iter(['status', 'num_threads']):
        try:
            total_processes += 1
            status = p.info['status']
            thread_count += p.info['num_threads'] or 0

            if status == psutil.STATUS_RUNNING:
                running += 1
            elif status in [psutil.STATUS_SLEEPING, psutil.STATUS_DISK_SLEEP]:
                sleeping += 1
            elif status == psutil.STATUS_ZOMBIE:
                zombie += 1
            elif status == psutil.STATUS_STOPPED:
                stopped += 1
        except Exception:
            continue

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO system_runtime_info (
            host_id, collected_at, boot_time, uptime_seconds,
            load_avg_1, load_avg_5, load_avg_15,
            total_processes, running_processes, sleeping_processes,
            zombie_processes, stopped_processes, thread_count
        )
        VALUES (%s, NOW(), to_timestamp(%s), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        host_id, boot_time, uptime_seconds,
        load1, load5, load15,
        total_processes, running, sleeping, zombie, stopped, thread_count
    ))

    conn.commit()
    cur.close()
    conn.close()


def collect_cpu_metrics(host_id):
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_times = psutil.cpu_times_percent(interval=None)
    cpu_stats = psutil.cpu_stats()

    iowait = getattr(cpu_times, "iowait", 0.0)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO cpu_metrics (
            host_id, collected_at, cpu_usage_percent,
            user_percent, system_percent, idle_percent,
            iowait_percent, irq_count, softirq_count,
            interrupts, context_switches, cpu_temperature_c
        )
        VALUES (%s, NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        host_id,
        cpu_percent,
        cpu_times.user,
        cpu_times.system,
        cpu_times.idle,
        iowait,
        getattr(cpu_stats, "interrupts", 0),
        getattr(cpu_stats, "soft_interrupts", 0),
        getattr(cpu_stats, "interrupts", 0),
        getattr(cpu_stats, "ctx_switches", 0),
        None
    ))

    per_core = psutil.cpu_percent(interval=None, percpu=True)

    for core_num, usage in enumerate(per_core):
        cur.execute("""
            INSERT INTO cpu_core_metrics (
                host_id, collected_at, core_number,
                usage_percent, user_percent, system_percent, idle_percent
            )
            VALUES (%s, NOW(), %s, %s, %s, %s, %s)
        """, (
            host_id,
            core_num,
            usage,
            None,
            None,
            None
        ))

    conn.commit()
    cur.close()
    conn.close()


def collect_memory_metrics(host_id):
    vm = psutil.virtual_memory()
    swap = psutil.swap_memory()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO memory_metrics (
            host_id, collected_at, total_ram_bytes, used_ram_bytes, free_ram_bytes,
            available_ram_bytes, cached_bytes, buffers_bytes, shared_bytes,
            memory_percent, swap_total_bytes, swap_used_bytes, swap_free_bytes, swap_percent
        )
        VALUES (%s, NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        host_id,
        vm.total,
        vm.used,
        vm.free,
        vm.available,
        getattr(vm, "cached", 0),
        getattr(vm, "buffers", 0),
        getattr(vm, "shared", 0),
        vm.percent,
        swap.total,
        swap.used,
        swap.free,
        swap.percent
    ))

    conn.commit()
    cur.close()
    conn.close()


def collect_disk_metrics(host_id):
    disk_usage = psutil.disk_usage("/")
    io = psutil.disk_io_counters()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO disk_metrics (
            host_id, collected_at, disk_total_bytes, disk_used_bytes, disk_free_bytes,
            disk_percent, read_bytes, write_bytes, read_count, write_count,
            read_time_ms, write_time_ms, busy_time_ms
        )
        VALUES (%s, NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        host_id,
        disk_usage.total,
        disk_usage.used,
        disk_usage.free,
        disk_usage.percent,
        getattr(io, "read_bytes", 0) if io else 0,
        getattr(io, "write_bytes", 0) if io else 0,
        getattr(io, "read_count", 0) if io else 0,
        getattr(io, "write_count", 0) if io else 0,
        getattr(io, "read_time", 0) if io else 0,
        getattr(io, "write_time", 0) if io else 0,
        getattr(io, "busy_time", 0) if io else 0
    ))

    partitions = psutil.disk_partitions()
    for part in partitions:
        try:
            usage = psutil.disk_usage(part.mountpoint)
            cur.execute("""
                INSERT INTO partition_metrics (
                    host_id, collected_at, device_name, mountpoint, filesystem_type,
                    total_bytes, used_bytes, free_bytes, usage_percent
                )
                VALUES (%s, NOW(), %s, %s, %s, %s, %s, %s, %s)
            """, (
                host_id,
                part.device,
                part.mountpoint,
                part.fstype,
                usage.total,
                usage.used,
                usage.free,
                usage.percent
            ))
        except Exception:
            continue

    conn.commit()
    cur.close()
    conn.close()


def collect_network_metrics(host_id):
    net = psutil.net_io_counters()
    pernic = psutil.net_io_counters(pernic=True)
    stats = psutil.net_if_stats()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO network_metrics (
            host_id, collected_at, bytes_sent, bytes_received,
            packets_sent, packets_received, errin, errout, dropin, dropout
        )
        VALUES (%s, NOW(), %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        host_id,
        net.bytes_sent,
        net.bytes_recv,
        net.packets_sent,
        net.packets_recv,
        net.errin,
        net.errout,
        net.dropin,
        net.dropout
    ))

    for iface, counters in pernic.items():
        iface_stat = stats.get(iface)
        status = "up" if iface_stat and iface_stat.isup else "down"

        cur.execute("""
            INSERT INTO interface_metrics (
                host_id, collected_at, interface_name,
                bytes_sent, bytes_received, packets_sent, packets_received,
                errin, errout, status
            )
            VALUES (%s, NOW(), %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            host_id,
            iface,
            counters.bytes_sent,
            counters.bytes_recv,
            counters.packets_sent,
            counters.packets_recv,
            counters.errin,
            counters.errout,
            status
        ))

    conn.commit()
    cur.close()
    conn.close()


def run_live_collector():
    host_id = get_or_create_host()
    print(f"Starting full collector for host_id = {host_id}")

    while True:
        try:
            collect_system_runtime_info(host_id)
            collect_cpu_metrics(host_id)
            collect_memory_metrics(host_id)
            collect_disk_metrics(host_id)
            collect_network_metrics(host_id)

            collect_process_metrics(host_id)
            collect_process_connections(host_id)
            collect_process_open_files(host_id)
            collect_process_threads(host_id)

            build_training_features(host_id)

            row_count = get_training_row_count(host_id)
            print(f"Training feature rows available: {row_count}")
            print("Collection cycle completed successfully.\n")

            time.sleep(COLLECTION_INTERVAL)

        except KeyboardInterrupt:
            print("Collector stopped by user.")
            break
        except Exception as e:
            print("Collector error:", e)
            time.sleep(COLLECTION_INTERVAL)


if __name__ == "__main__":
    run_live_collector()
