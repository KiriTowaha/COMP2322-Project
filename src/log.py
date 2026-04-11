import threading, datetime

LOG_FILE = "./log/server.log"

log_lock = threading.Lock()

def write_log(client_ip, status):
    with log_lock:
        with open(LOG_FILE, "a") as log:
            time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log.write(f"{client_ip} | {time_str} | {status}\n")
