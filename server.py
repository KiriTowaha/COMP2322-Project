import os,socket,threading
# create a socket object
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print ("socket successfully created")
serverPort = 80
serverSocket.bind(('', serverPort))
print ("socket binded to %s" %(serverPort))
serverSocket.listen(5)
print ("socket is listening")
def handle_client(connectionSocket, addr):
    print('Connection from', addr)
    message = connectionSocket.recv(1024).decode()
    print(message)
    request_line = message.splitlines()[0]
    request_path = request_line.split()[1]
    if request_path in ['/','/index.html']:
        html_file_path = os.path.join(os.path.dirname(__file__), "index.html")

        try:
            with open(html_file_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            response = f"""HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8

{html_content}
"""
        except FileNotFoundError:
            response = """HTTP/1.1 404 Not Found
Content-Type: text/plain; charset=utf-8

Error: index.html not found.
"""
    else:
        response = """HTTP/1.1 404 Not Found
Content-Type: text/plain; charset=utf-8

Error: 404 Not Found.
"""

    connectionSocket.sendall(response.encode("utf-8"))
    connectionSocket.close()

while True:
    # establish connection with client.
    connectionSocket, addr = serverSocket.accept()
    client_thread = threading.Thread(target=handle_client, args=(connectionSocket, addr))
    client_thread.start()