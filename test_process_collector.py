from static_collector import get_or_create_host
from process_collector import (
    collect_process_metrics,
    collect_process_connections,
    collect_process_open_files,
    collect_process_threads
)

host_id = get_or_create_host()

collect_process_metrics(host_id)
collect_process_connections(host_id)
collect_process_open_files(host_id)
collect_process_threads(host_id)

print("Process data collected successfully!")
