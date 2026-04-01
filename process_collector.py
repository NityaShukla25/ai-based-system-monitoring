import psutil
from db import get_connection


def collect_process_metrics(host_id):
    conn = get_connection()
    cur = conn.cursor()

    for proc in psutil.process_iter([
        'pid', 'ppid', 'name', 'username', 'cmdline', 'status',
        'cpu_percent', 'memory_percent', 'num_threads', 'create_time', 'nice'
    ]):
        try:
            mem_info = proc.memory_info()
            io_info = proc.io_counters() if proc.is_running() else None
            ctx = proc.num_ctx_switches()
            cpu_times = proc.cpu_times()

            try:
                open_files_count = len(proc.open_files())
            except Exception:
                open_files_count = 0

            try:
                connection_count = len(proc.connections(kind='inet'))
            except Exception:
                connection_count = 0

            cur.execute("""
                INSERT INTO process_metrics (
                    host_id, collected_at, pid, ppid, process_name, username, cmdline,
                    status, priority, nice_value, cpu_percent, memory_percent,
                    rss_bytes, vms_bytes, shared_bytes, thread_count,
                    read_bytes, write_bytes, read_count, write_count,
                    open_files_count, connection_count, create_time,
                    cpu_time_user, cpu_time_system,
                    voluntary_ctx_switches, involuntary_ctx_switches
                )
                VALUES (
                    %s, NOW(), %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, to_timestamp(%s),
                    %s, %s, %s, %s
                )
            """, (
                host_id,
                proc.info['pid'],
                proc.info['ppid'],
                proc.info['name'],
                proc.info['username'],
                " ".join(proc.info['cmdline']) if proc.info['cmdline'] else None,
                proc.info['status'],
                proc.info['nice'],
                proc.info['nice'],
                proc.info['cpu_percent'],
                proc.info['memory_percent'],
                mem_info.rss,
                mem_info.vms,
                getattr(mem_info, 'shared', 0),
                proc.info['num_threads'],
                io_info.read_bytes if io_info else 0,
                io_info.write_bytes if io_info else 0,
                io_info.read_count if io_info else 0,
                io_info.write_count if io_info else 0,
                open_files_count,
                connection_count,
                proc.info['create_time'],
                cpu_times.user,
                cpu_times.system,
                ctx.voluntary,
                ctx.involuntary
            ))

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
        except Exception as e:
            print("process_metrics error:", e)
            continue

    conn.commit()
    cur.close()
    conn.close()


def collect_process_connections(host_id):
    conn = get_connection()
    cur = conn.cursor()

    for proc in psutil.process_iter(['pid', 'name']):
        try:
            for c in proc.connections(kind='inet'):
                local_ip = c.laddr.ip if c.laddr else None
                local_port = c.laddr.port if c.laddr else None
                remote_ip = c.raddr.ip if c.raddr else None
                remote_port = c.raddr.port if c.raddr else None
                protocol = "TCP" if c.type == 1 else "UDP"

                cur.execute("""
                    INSERT INTO process_connections (
                        host_id, collected_at, pid, process_name,
                        local_address, local_port, remote_address, remote_port,
                        protocol, state
                    )
                    VALUES (%s, NOW(), %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    host_id,
                    proc.info['pid'],
                    proc.info['name'],
                    local_ip,
                    local_port,
                    remote_ip,
                    remote_port,
                    protocol,
                    c.status
                ))

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
        except Exception as e:
            print("process_connections error:", e)
            continue

    conn.commit()
    cur.close()
    conn.close()


def collect_process_open_files(host_id):
    conn = get_connection()
    cur = conn.cursor()

    for proc in psutil.process_iter(['pid', 'name']):
        try:
            files = proc.open_files()
            for f in files:
                cur.execute("""
                    INSERT INTO process_open_files (
                        host_id, collected_at, pid, process_name, file_path
                    )
                    VALUES (%s, NOW(), %s, %s, %s)
                """, (
                    host_id,
                    proc.info['pid'],
                    proc.info['name'],
                    f.path
                ))

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
        except Exception as e:
            print("process_open_files error:", e)
            continue

    conn.commit()
    cur.close()
    conn.close()


def collect_process_threads(host_id):
    conn = get_connection()
    cur = conn.cursor()

    for proc in psutil.process_iter(['pid']):
        try:
            thread_count = proc.num_threads()

            cur.execute("""
                INSERT INTO process_threads (
                    host_id, collected_at, pid, thread_count
                )
                VALUES (%s, NOW(), %s, %s)
            """, (
                host_id,
                proc.pid,
                thread_count
            ))

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
        except Exception as e:
            print("process_threads error:", e)
            continue

    conn.commit()
    cur.close()
    conn.close()
