import os
import datetime
import mimetypes
import socket

def get_request_headers(request_lines):
    headers = {}
    for line in request_lines[1:]:
        if not line or ":" not in line:
            continue
        name, value = line.split(":", 1)
        headers[name.strip().lower()] = value.strip()
    return headers


def format_http_date(dt):
    return dt.astimezone(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

def parse_http_date(value):
    http_date_formats = [
        "%a, %d %b %Y %H:%M:%S GMT",
        "%A, %d-%b-%y %H:%M:%S GMT",
        "%a %b %d %H:%M:%S %Y",
    ]
    for date_format in http_date_formats:
        try:
            parsed = datetime.datetime.strptime(value, date_format)
            parsed = parsed.replace(tzinfo=datetime.timezone.utc)
            return parsed
        except ValueError:
            continue
    raise ValueError("Invalid HTTP date")


def get_last_modified(file_path):
    modified_time = datetime.datetime.fromtimestamp(
        os.path.getmtime(file_path), tz=datetime.timezone.utc
    )
    return modified_time.replace(microsecond=0)

def client_host_and_ip(client_address):
    ip_address = client_address[0] if isinstance(client_address, (tuple, list)) else str(client_address)
    try:
        hostname = socket.gethostbyaddr(ip_address)[0]
    except OSError:
        hostname = ip_address
    return f"{hostname}/{ip_address}"

def requested_file_name(path):
    if not path:
        return "-"
    clean_path = path.split("?", 1)[0].split("#", 1)[0]
    if clean_path in ("", "/"):
        return "index.html"
    file_name = os.path.basename(clean_path.rstrip("/"))
    return file_name if file_name else clean_path.strip("/")

def serve_file(file_path):
    try:
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"

        with open(file_path, "rb") as f:
            content = f.read()
        headers = {
            "Content-Type": mime_type,
            "Content-Length": str(len(content))
        }

        return 200, content, headers

    except FileNotFoundError:
        return 404, b"Error: File not found.\n", {"Content-Type": "text/plain"}

    except OSError:
        return 404, b"Error: File not found.\n", {"Content-Type": "text/plain"}
