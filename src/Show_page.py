from .http_utils import get_last_modified, format_http_date, parse_http_date
from .http_response import build_response
from .log import write_log

def handle_page_request(html_file_path, headers, connectionSocket, connection_header, addr):
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
                    if connection_header == "close":
                        return
                    return
            except (ValueError, TypeError):
                pass

        with open(html_file_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        response = build_response(
            200, html_content, {"Last-Modified": last_modified_text}
        )
        write_log(addr, "200 OK")
        connectionSocket.sendall(response.encode("utf-8"))

    except FileNotFoundError:
        body = "Error: File not found.\n"
        response = build_response(
            404,
            body,
            {
                "Content-Length": str(len(body.encode("utf-8"))),
                "Connection": "close",
            },
        )
        write_log(addr, "404 Not Found")
        connectionSocket.sendall(response.encode("utf-8"))