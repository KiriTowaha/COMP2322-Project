import os, socket, threading
from src import (
    build_response,
    get_request_headers,
    write_log, serve_file, handle_page_request
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
    while True:  
        try:
            message = connectionSocket.recv(1024).decode(errors="replace")
            if not message:
                break

            print(message)
            request_lines = message.splitlines()
            if not request_lines:
                response = build_response(400, "Error: Bad Request.\n")
                write_log(addr, "400 Bad Request")
                connectionSocket.sendall(response.encode("utf-8"))
                break

            request_parts = request_lines[0].split()
            if len(request_parts) != 3:
                response = build_response(400, "Error: Bad Request.\n")
                write_log(addr, "400 Bad Request")
                connectionSocket.sendall(response.encode("utf-8"))
                break

            method, path, version = request_parts
            if not path.startswith("/") or not version.startswith("HTTP/"):
                response = build_response(400, "Error: Bad Request.\n")
                write_log(addr, "400 Bad Request")
                connectionSocket.sendall(response.encode("utf-8"))
                break
            headers = get_request_headers(request_lines)
            connection_header = headers.get("connection", "close").lower()

            if path.startswith("/src/assets/"):
                file_path = os.path.join(os.path.dirname(__file__), path.lstrip("/"))
                status, content, extra_headers = serve_file(file_path)
                response = build_response(status, content.decode(errors="replace") if status == 200 else content, extra_headers)
                write_log(addr, f"{status} {'OK' if status == 200 else 'Error'}")
                connectionSocket.sendall(response.encode("utf-8") if isinstance(content, str) else content)
                if connection_header == "close":
                    break
                continue
            match path:
                case "/" | "/index.html":
                    html_file_path = os.path.join(os.path.dirname(__file__), "index.html")
                    handle_page_request(html_file_path, headers, connectionSocket, connection_header, addr)
                case "/Page2.html":
                    html_file_path = os.path.join(os.path.dirname(__file__), "Page2.html")
                    handle_page_request(html_file_path, headers, connectionSocket, connection_header, addr)
                case path if path.startswith(("/log", "/src", "/test")):
                    response = build_response(403, "Error: Forbidden.\n")
                    write_log(addr, "403 Forbidden")
                    connectionSocket.sendall(response.encode("utf-8"))
                    if connection_header == "close":
                        break
                case _:
                    response = build_response(404, "Error: 404 Not Found.\n")
                    write_log(addr, "404 Not Found")
                    connectionSocket.sendall(response.encode("utf-8"))
                    if connection_header == "close":
                        break
            connectionSocket.sendall(response.encode("utf-8"))

            if connection_header == "close":
                break
        except Exception as e:
            print(f"Error handling client: {e}")
            break

    connectionSocket.close()

while True:
    connectionSocket, addr = serverSocket.accept()
    client_thread = threading.Thread(target=handle_client, args=(connectionSocket, addr))
    client_thread.start()