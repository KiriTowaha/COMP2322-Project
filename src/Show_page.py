from .http_utils import get_last_modified, format_http_date, parse_http_date
from .http_response import build_response, build_text_response
from .log import write_log

def handle_page_request(html_file_path, headers, connectionSocket, connection_header, addr, method, path, version):
    try:
        last_modified = get_last_modified(html_file_path)
        last_modified_text = format_http_date(last_modified)
        if_modified_since = headers.get("if-modified-since")

        if if_modified_since:
            try:
                modified_since_time = parse_http_date(if_modified_since)
                if last_modified <= modified_since_time.replace(microsecond=0):
                    response = build_response(
                        304,
                        extra_headers={
                            "Last-Modified": last_modified_text,
                            "Connection": connection_header,
                        },
                    )
                    write_log(addr, "304 Not Modified", method, path, version, connection_header)
                    connectionSocket.sendall(response.encode("utf-8"))
                    if connection_header == "close":
                        return
                    return
            except (ValueError, TypeError):
                pass

        with open(html_file_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        body = "" if method == "HEAD" else html_content
        content_length = len(html_content.encode("utf-8"))
        response = build_response(
            200,
            body,
            {
                "Last-Modified": last_modified_text,
                "Content-Length": str(content_length),
                "Connection": connection_header,
            },
        )
        write_log(addr, "200 OK", method, path, version, connection_header)
        connectionSocket.sendall(response.encode("utf-8"))

    except FileNotFoundError:
        response = build_text_response(404, "Error: File not found.\n", connection_header, method=method)
        write_log(addr, "404 Not Found", method, path, version, connection_header)
        connectionSocket.sendall(response.encode("utf-8"))
