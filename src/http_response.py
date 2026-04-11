
def build_response(status, body="", extra_headers=None):
    response = response_handle(status, extra_headers)
    return response + body

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