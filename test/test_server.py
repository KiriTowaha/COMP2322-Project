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

        # wait until server is ready
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

    def test_index_request(self):
        response = self.send_request("GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")
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
        self.assertTrue("304 Not Modified" in response or "200 OK" in response)

    def test_content_type_html(self):
        response = self.send_request("GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")
        self.assertIn("text/html", response)

    def test_content_type_not_found(self):
        response = self.send_request("GET /missing HTTP/1.1\r\nHost: localhost\r\n\r\n")
        self.assertIn("text/plain", response)


if __name__ == "__main__":
    unittest.main()