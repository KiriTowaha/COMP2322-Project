import unittest
import socket
import time
import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestHTTPServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.host = "127.0.0.1"
        cls.port = 80

        env = os.environ.copy()
        env["PORT"] = str(cls.port)

        cls.server_proc = subprocess.Popen(
            [sys.executable, "server.py"],
            cwd=str(ROOT),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.time() + 5
        while time.time() < deadline:
            try:
                with socket.create_connection((cls.host, cls.port), timeout=0.5):
                    return
            except OSError:
                time.sleep(0.1)

        raise RuntimeError("Server did not start on port 80")

    @classmethod
    def tearDownClass(cls):
        if cls.server_proc and cls.server_proc.poll() is None:
            cls.server_proc.terminate()
            try:
                cls.server_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                cls.server_proc.kill()

    def send_request(self, request_text):
        try:
            with socket.create_connection((self.host, self.port), timeout=2) as sock:
                sock.sendall(request_text.encode("utf-8"))
                chunks = []
                while True:
                    data = sock.recv(4096)
                    if not data:
                        break
                    chunks.append(data)
            return b"".join(chunks).decode("utf-8", errors="replace")
        except Exception as e:
            return f"Connection error: {e}"

    def send_request_raw(self, request_bytes):
        with socket.create_connection((self.host, self.port), timeout=2) as sock:
            sock.sendall(request_bytes)
            chunks = []
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                chunks.append(data)
        return b"".join(chunks)

    def test_index_request(self):
        response = self.send_request("GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")
        self.assertIn("200 OK", response)
    def test_index_html_request(self):
        response = self.send_request("GET /index.html HTTP/1.1\r\nHost: localhost\r\n\r\n")
        self.assertIn("200 OK", response)
    def test_index_html_request(self):
        response = self.send_request("GET /index.html HTTP/1.1\r\nHost: localhost\r\n\r\n")
        self.assertIn("200 OK", response)

    def test_not_found(self):
        response = self.send_request("GET /nonexistent.html HTTP/1.1\r\nHost: localhost\r\n\r\n")
        self.assertIn("404 Not Found", response)

    def test_forbidden_log_access(self):
        response = self.send_request("GET /log HTTP/1.1\r\nHost: localhost\r\n\r\n")
        self.assertIn("403 Forbidden", response)

    def test_bad_request_no_path(self):
        response = self.send_request("GET HTTP/1.1\r\nHost: localhost\r\n\r\n")
        self.assertIn("400 Bad Request", response)

    def test_if_modified_since_header(self):
        response = self.send_request(
            "GET / HTTP/1.1\r\nHost: localhost\r\nIf-Modified-Since: Mon, 01 Jan 2024 00:00:00 GMT\r\n\r\n"
        )
        self.assertIn("200 OK", response)

    def test_content_type_html(self):
        response = self.send_request("GET /index.html HTTP/1.1\r\nHost: localhost\r\n\r\n")
        self.assertIn("text/html", response)

    def test_content_type_not_found(self):
        response = self.send_request("GET /missing HTTP/1.1\r\nHost: localhost\r\n\r\n")
        self.assertIn("text/plain", response)

    def test_multithreaded_handling(self):
        from concurrent.futures import ThreadPoolExecutor

        def make_request():
            return self.send_request("GET /index.html HTTP/1.1\r\nHost: localhost\r\n\r\n")

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            responses = [future.result() for future in futures]

        for response in responses:
            self.assertIn("200 OK", response)

    def test_get_text_file(self):
        response = self.send_request("GET /index.html HTTP/1.1\r\nHost: localhost\r\n\r\n")
        self.assertIn("200 OK", response)
        self.assertIn("text/html", response)

    def test_get_image_file(self):
        response = self.send_request_raw(b"GET /src/assets/Polyu.png HTTP/1.1\r\nHost: localhost\r\n\r\n")
        self.assertIn(b"200 OK", response)
        self.assertIn(b"Content-Type: image/png", response)

    def test_head_request(self):
        response = self.send_request("HEAD /index.html HTTP/1.1\r\nHost: localhost\r\n\r\n")
        self.assertIn("200 OK", response)
        self.assertNotIn("<!DOCTYPE html>", response)

    def test_response_statuses(self):
        response = self.send_request("GET /index.html HTTP/1.1\r\nHost: localhost\r\n\r\n")
        self.assertIn("200 OK", response)

        response = self.send_request("GET HTTP/1.1\r\nHost: localhost\r\n\r\n")
        self.assertIn("400 Bad Request", response)

        response = self.send_request("GET /log HTTP/1.1\r\nHost: localhost\r\n\r\n")
        self.assertIn("403 Forbidden", response)

        response = self.send_request("GET /nonexistent.html HTTP/1.1\r\nHost: localhost\r\n\r\n")
        self.assertIn("404 Not Found", response)

        response = self.send_request(
            "GET /index.html HTTP/1.1\r\nHost: localhost\r\nIf-Modified-Since: Mon, 01 Jan 2024 00:00:00 GMT\r\n\r\n"
        )
        self.assertIn("200 OK", response)

    def test_not_modified_304(self):
        initial = self.send_request("GET /index.html HTTP/1.1\r\nHost: localhost\r\n\r\n")
        self.assertIn("Last-Modified:", initial)
        last_modified = next(
            line.split(": ", 1)[1]
            for line in initial.split("\r\n")
            if line.lower().startswith("last-modified:")
        )
        response = self.send_request(
            f"GET /index.html HTTP/1.1\r\nHost: localhost\r\nIf-Modified-Since: {last_modified}\r\n\r\n"
        )
        self.assertIn("304 Not Modified", response)

    def test_last_modified_header(self):
        response = self.send_request("GET /index.html HTTP/1.1\r\nHost: localhost\r\n\r\n")
        self.assertIn("Last-Modified", response)

        response = self.send_request(
            "GET /index.html HTTP/1.1\r\nHost: localhost\r\nIf-Modified-Since: Mon, 01 Jan 2024 00:00:00 GMT\r\n\r\n"
        )
        self.assertTrue("304 Not Modified" in response or "200 OK" in response)

    def test_connection_header(self):
        with socket.create_connection((self.host, self.port), timeout=2) as sock:
            sock.sendall(b"GET /index.html HTTP/1.1\r\nHost: localhost\r\nConnection: keep-alive\r\n\r\n")
            response = sock.recv(4096).decode("utf-8", errors="replace")
            self.assertIn("200 OK", response)
            self.assertIn("Connection: keep-alive", response)

        response = self.send_request("GET /index.html HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n")
        self.assertIn("200 OK", response)
        self.assertIn("Connection: close", response)

    def test_persistent_connection_two_requests(self):
        with socket.create_connection((self.host, self.port), timeout=2) as sock:
            first = b"GET /index.html HTTP/1.1\r\nHost: localhost\r\nConnection: keep-alive\r\n\r\n"
            second = b"GET /Page2.html HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n"
            sock.sendall(first)
            data1 = sock.recv(4096)
            self.assertIn(b"200 OK", data1)
            self.assertIn(b"Connection: keep-alive", data1)

            sock.sendall(second)
            chunks = []
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                chunks.append(data)
            data2 = b"".join(chunks)
            self.assertIn(b"200 OK", data2)
            self.assertIn(b"Connection: close", data2)


if __name__ == "__main__":
    unittest.main()
