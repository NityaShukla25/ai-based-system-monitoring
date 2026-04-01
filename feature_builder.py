from db import get_connection


def build_training_features(host_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        WITH latest_cpu AS (
            SELECT *
            FROM cpu_metrics
            WHERE host_id = %s
            ORDER BY collected_at DESC
            LIMIT 1
        ),
        latest_memory AS (
            SELECT *
            FROM memory_metrics
            WHERE host_id = %s
            ORDER BY collected_at DESC
            LIMIT 1
        ),
        latest_disk AS (
            SELECT *
            FROM disk_metrics
            WHERE host_id = %s
            ORDER BY collected_at DESC
            LIMIT 1
        ),
        latest_network AS (
            SELECT *
            FROM network_metrics
            WHERE host_id = %s
            ORDER BY collected_at DESC
            LIMIT 1
        ),
        latest_runtime AS (
            SELECT *
            FROM system_runtime_info
            WHERE host_id = %s
            ORDER BY collected_at DESC
            LIMIT 1
        )
        INSERT INTO model_training_features (
            host_id,
            collected_at,
            cpu_usage,
            memory_usage,
            disk_usage,
            network_in,
            network_out,
            process_count,
            running_processes,
            thread_count,
            load_avg_1m,
            load_avg_5m,
            load_avg_15m
        )
        SELECT
            %s,
            NOW(),
            c.cpu_usage_percent,
            m.memory_percent,
            d.disk_percent,
            n.bytes_received,
            n.bytes_sent,
            r.total_processes,
            r.running_processes,
            r.thread_count,
            r.load_avg_1,
            r.load_avg_5,
            r.load_avg_15
        FROM latest_cpu c, latest_memory m, latest_disk d, latest_network n, latest_runtime r
    """, (host_id, host_id, host_id, host_id, host_id, host_id))

    conn.commit()
    cur.close()
    conn.close()

    print("Training features generated successfully")
