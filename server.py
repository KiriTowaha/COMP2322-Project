import os, socket, datetime, threading
from src.log import write_log

PORT= 80

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print ("Socket successfully created")
serverSocket.bind(('', PORT))
print ("Socket binded to %s" %(PORT))
serverSocket.listen(5)
print ("Socket is listening")

def get_request_headers(request_lines):
    headers = {}
    for line in request_lines[1:]:
        if not line or ":" not in line:
            continue
        name, value = line.split(":", 1)
        headers[name.strip().lower()] = value.strip()
    return headers


def get_last_modified(file_path):
    modified_time = datetime.datetime.fromtimestamp(
        os.path.getmtime(file_path), tz=datetime.timezone.utc
    )
    return modified_time.replace(microsecond=0)


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
            if date_format == "%a %b %d %H:%M:%S %Y":
                parsed = parsed.replace(tzinfo=datetime.timezone.utc)
            else:
                parsed = parsed.replace(tzinfo=datetime.timezone.utc)
            return parsed
        except ValueError:
            continue
    raise ValueError("Invalid HTTP date")


def build_response(status, body="", extra_headers=None):
    response = response_handle(status, extra_headers)
    return response + body


def handle_client(connectionSocket, addr):    
    print('Connection from', addr)
    message = connectionSocket.recv(1024).decode(errors="replace")
    print(message)
    request_lines = message.splitlines()
    if not request_lines:
        response = build_response(400, "Error: Bad Request.\n")
        write_log(addr, "400 Bad Request")
        connectionSocket.sendall(response.encode("utf-8"))
        connectionSocket.close()
        return

    request_parts = request_lines[0].split()
    if len(request_parts) < 2:
        response = build_response(400, "Error: Bad Request.\n")
        write_log(addr, "400 Bad Request")
        connectionSocket.sendall(response.encode("utf-8"))
        connectionSocket.close()
        return

    headers = get_request_headers(request_lines)
    path = request_parts[1]
    match path:
        case "/" | "/index.html":
            html_file_path = os.path.join(os.path.dirname(__file__), "index.html")
            try:
                last_modified = get_last_modified(html_file_path)
                last_modified_text = format_http_date(last_modified)
                if_modified_since = headers.get("if-modified-since")
                if if_modified_since:
                    try:
                        modified_since_time = parse_http_date(if_modified_since)
                        if modified_since_time.replace(microsecond=0) >= last_modified:
                            response = build_response(
                                304,
                                extra_headers={"Last-Modified": last_modified_text},
                            )
                            write_log(addr, "304 Not Modified")
                            connectionSocket.sendall(response.encode("utf-8"))
                            connectionSocket.close()
                            return
                    except (ValueError, TypeError):
                        pass

                with open(html_file_path, "r", encoding="utf-8") as f:
                    html_content = f.read()
                response = build_response(
                    200,
                    html_content,
                    {"Last-Modified": last_modified_text},
                )
                write_log(addr, "200 OK")
            except FileNotFoundError:
                response = build_response(404, "Error: index.html not found.\n")
                write_log(addr, "404 Not Found")
        case path if path.startswith("/log"):
            response = build_response(403)
            write_log(addr, "403 Forbidden")
        case _:
            response = build_response(404, "Error: 404 Not Found.\n")
            write_log(addr, "404 Not Found")
    connectionSocket.sendall(response.encode("utf-8"))
    connectionSocket.close()

def response_handle(status, extra_headers=None):
    header_lines = []
    if extra_headers:
        for name, value in extra_headers.items():
            header_lines.append(f"{name}: {value}\r\n")
    headers = "".join(header_lines)
    match status:
        case 200:
            return (
                "HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n"
                f"{headers}\r\n"
            )
        case 400:
            return (
                "HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain; charset=utf-8\r\n"
                f"{headers}\r\n"
            )
        case 403:
            return (
                "HTTP/1.1 403 Forbidden\r\nContent-Type: text/plain; charset=utf-8\r\n"
                f"{headers}\r\n"
            )
        case 404:
            return (
                "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain; charset=utf-8\r\n"
                f"{headers}\r\n"
            )
        case 304:
            return (
                "HTTP/1.1 304 Not Modified\r\n"
                f"{headers}\r\n"
            )
        case _:
            return (
                "HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/plain; charset=utf-8\r\n"
                f"{headers}\r\n"
            )
        
while True:
    # establish connection with client.
    connectionSocket, addr = serverSocket.accept()
    client_thread = threading.Thread(target=handle_client, args=(connectionSocket, addr))
    client_thread.start()