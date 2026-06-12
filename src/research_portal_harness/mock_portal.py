from __future__ import annotations

import os
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterator


class MockResearchHandler(BaseHTTPRequestHandler):
    server_version = "MockResearchPortal/0.1"

    def log_message(self, format: str, *args: object) -> None:
        return

    def do_GET(self) -> None:  # noqa: N802
        if self.path in {"/", "/login"}:
            self._html(
                """
                <html><body>
                <h1>Mock Research Portal</h1>
                <a href="/research">Research</a>
                </body></html>
                """
            )
            return
        if self.path.startswith("/research"):
            self._html(
                """
                <html><body>
                <h1>Research Library</h1>
                <a href="/downloads/report.pdf">AI networking initiation report PDF</a>
                <a href="/downloads/model.xlsx">AI networking financial model Excel</a>
                <a href="/downloads/prices.csv">AI networking trading data CSV</a>
                <a href="/terms">Terms</a>
                </body></html>
                """
            )
            return
        if self.path == "/downloads/report.pdf":
            self._bytes(b"%PDF-1.4\n% mock report\n1 0 obj\n<<>>\nendobj\n%%EOF\n", "application/pdf", "report.pdf")
            return
        if self.path == "/downloads/model.xlsx":
            self._bytes(_xlsx_bytes(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "model.xlsx")
            return
        if self.path == "/downloads/prices.csv":
            self._bytes(b"ticker,price\nABC,12.3\n", "text/csv", "prices.csv")
            return
        if self.path == "/terms":
            self._html("<html><body>Terms</body></html>")
            return
        self.send_response(404)
        self.end_headers()

    def _html(self, body: str) -> None:
        self.send_response(200)
        self.send_header("content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def _bytes(self, body: bytes, content_type: str, filename: str) -> None:
        self.send_response(200)
        self.send_header("content-type", content_type)
        self.send_header("content-disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(body)


def _xlsx_bytes() -> bytes:
    try:
        import openpyxl
    except ImportError:
        return b"ticker,value\nABC,1\n"
    from io import BytesIO

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Model"
    sheet.append(["ticker", "revenue"])
    sheet.append(["ABC", 123])
    handle = BytesIO()
    workbook.save(handle)
    return handle.getvalue()


@contextmanager
def run_mock_portal() -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), MockResearchHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

