import os, socket, threading
from src import (
    build_response,
    format_http_date,
    get_last_modified,
    get_request_headers,
    parse_http_date,
    write_log,
)

PORT= 80

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print ("Socket successfully created")
serverSocket.bind(('', PORT))
print ("Socket binded to %s" %(PORT))
serverSocket.listen(5)
print ("Socket is listening")




def handle_client(connectionSocket, addr):    
    print("Connection from", addr)
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
    if len(request_parts) != 3:
        response = build_response(400, "Error: Bad Request.\n") 
        write_log(addr, "400 Bad Request")
        connectionSocket.sendall(response.encode("utf-8"))
        connectionSocket.close()
        return

    method, path, version = request_parts
    if not path.startswith("/") or not version.startswith("HTTP/"):
        response = build_response(400, "Error: Bad Request.\n")
        write_log(addr, "400 Bad Request")
        connectionSocket.sendall(response.encode("utf-8"))
        connectionSocket.close()
        return

    headers = get_request_headers(request_lines)

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
                    200, html_content, {"Last-Modified": last_modified_text}
                )
                write_log(addr, "200 OK")
            except FileNotFoundError:
                response = build_response(404, "Error: index.html not found.\n")
                write_log(addr, "404 Not Found")

        case path if path.startswith("/log"):
            response = build_response(403, "Error: Forbidden.\n")
            write_log(addr, "403 Forbidden")

        case _:
            response = build_response(404, "Error: 404 Not Found.\n")
            write_log(addr, "404 Not Found")

    connectionSocket.sendall(response.encode("utf-8"))
    connectionSocket.close()

while True:
    # establish connection with client.
    connectionSocket, addr = serverSocket.accept()
    client_thread = threading.Thread(target=handle_client, args=(connectionSocket, addr))
    client_thread.start()