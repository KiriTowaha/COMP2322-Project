import os, socket, threading
from src import (
    build_response,
    build_text_response,
    get_request_headers,
    write_log, serve_file, handle_page_request
)

PORT = int(os.environ.get("PORT", 80))

def createSocket(preferred_port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Socket successfully created")
    try:
        server_socket.bind(("", preferred_port))
        bound_port = preferred_port
    except OSError as err:
        if preferred_port == 80:
            server_socket.bind(("", 0))
            bound_port = server_socket.getsockname()[1]
            print("Port 80 is in use, switched to port %s" % bound_port)
        else:
            server_socket.close()
            raise
    return server_socket, bound_port

serverSocket, PORT = createSocket(PORT)
print ("Socket binded to %s" %(PORT))
serverSocket.listen(5)
print ("Socket is listening")

def handle_client(connectionSocket, addr):    
    print("Connection from", addr)
    while True:
        try:
            connection_header = "close"
            message = connectionSocket.recv(1024).decode(errors="replace")
            if not message:
                break

            print(message)
            request_lines = message.splitlines()
            if not request_lines:
                response = build_text_response(400, "Error: Bad Request.\n", connection_header)
                write_log(addr, "400 Bad Request", connection=connection_header)
                connectionSocket.sendall(response.encode("utf-8"))
                break

            request_parts = request_lines[0].split()
            if len(request_parts) != 3:
                response = build_text_response(400, "Error: Bad Request.\n", connection_header)
                write_log(addr, "400 Bad Request", connection=connection_header)
                connectionSocket.sendall(response.encode("utf-8"))
                break

            method, path, version = request_parts
            if method not in ("GET", "HEAD") or not path.startswith("/") or not version.startswith("HTTP/"):
                response = build_text_response(400, "Error: Bad Request.\n", connection_header, method=method)
                write_log(addr, "400 Bad Request", method, path, version, connection_header)
                connectionSocket.sendall(response.encode("utf-8"))
                if connection_header == "close":
                    break
                continue
            headers = get_request_headers(request_lines)
            connection_header = headers.get("connection", "close").lower()

            if path.startswith("/src/assets/"):
                file_path = os.path.join(os.path.dirname(__file__), path.lstrip("/"))
                status, content, extra_headers = serve_file(file_path)
                if status not in (200, 404):
                    response = build_text_response(400, "Error: Bad Request.\n", connection_header, method=method)
                    write_log(addr, "400 Bad Request", method, path, version, connection_header)
                    connectionSocket.sendall(response.encode("utf-8"))
                    if connection_header == "close":
                        break
                    continue
                extra_headers["Connection"] = connection_header
                body = b"" if method == "HEAD" else content
                response = build_response(status, body, extra_headers)
                status_text = "200 OK" if status == 200 else "404 Not Found"
                write_log(addr, status_text, method, path, version, connection_header)
                connectionSocket.sendall(response if isinstance(response, bytes) else response.encode("utf-8"))
                if connection_header == "close":
                    break
                continue
            match path:
                case "/" | "/index.html":
                    html_file_path = os.path.join(os.path.dirname(__file__), "index.html")
                    handle_page_request(html_file_path, headers, connectionSocket, connection_header, addr, method, path, version)
                case "/Page2.html":
                    html_file_path = os.path.join(os.path.dirname(__file__), "Page2.html")
                    handle_page_request(html_file_path, headers, connectionSocket, connection_header, addr, method, path, version)
                case path if path.startswith(("/log", "/src", "/test")):
                    response = build_text_response(403, "Error 403: Forbidden.\n", connection_header, method=method)
                    write_log(addr, "403 Forbidden", method, path, version, connection_header)
                    connectionSocket.sendall(response.encode("utf-8"))
                    if connection_header == "close":
                        break
                case _:
                    response = build_text_response(404, "Error 404: Not Found.\n", connection_header, method=method)
                    write_log(addr, "404 Not Found", method, path, version, connection_header)
                    connectionSocket.sendall(response.encode("utf-8"))
                    if connection_header == "close":
                        break
            if connection_header == "close":
                break
            continue
        except Exception as e:
            print(f"Error handling client: {e}")
            break

    connectionSocket.close()

while True:
    connectionSocket, addr = serverSocket.accept()
    client_thread = threading.Thread(target=handle_client, args=(connectionSocket, addr))
    client_thread.start()
