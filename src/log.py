import os
import threading, datetime
from .http_utils import client_host_and_ip, requested_file_name

LOG_FILE = "./log/server.log"

log_lock = threading.Lock()

def write_log(client_ip, status, method=None, path=None, version=None, connection=None):
    log_dir = os.path.dirname(LOG_FILE)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    client_info = client_host_and_ip(client_ip)
    file_name = requested_file_name(path)
    response_type = status

    with log_lock:
        with open(LOG_FILE, "a") as log:
            time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log.write(
                f"{time_str} | Client: {client_info} | File: {file_name} | Response: {response_type}\n"
            )
