import json
import mimetypes
import socket
import urllib.parse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR = BASE_DIR / "storage"
DATA_FILE = STORAGE_DIR / "data.json"
TEMPLATES_DIR = BASE_DIR / "templates"

HOST = "0.0.0.0"
PORT = 3000


class WebHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        route = urllib.parse.urlparse(self.path).path

        if route == "/":
            self.send_html("index.html")

        elif route == "/message":
            self.send_html("message.html")

        elif route == "/read":
            self.render_messages()

        elif route == "/style.css":
            self.send_static("style.css")

        elif route == "/logo.png":
            self.send_static("logo.png")

        else:
            self.send_error_page()

    def do_POST(self) -> None:
        if self.path == "/message":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)

            decoded_data = post_data.decode("utf-8")
            parsed_data = urllib.parse.parse_qs(decoded_data)

            username = parsed_data.get("username", [""])[0]
            message = parsed_data.get("message", [""])[0]

            self.save_message(username, message)

            self.send_response(302)
            self.send_header("Location", "/")
            self.end_headers()

        else:
            self.send_error_page()

    def send_html(self, filename: str) -> None:
        file_path = BASE_DIR / filename

        if not file_path.exists():
            self.send_error_page()
            return

        content = file_path.read_bytes()

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_static(self, filename: str) -> None:
        file_path = BASE_DIR / filename

        if not file_path.exists():
            self.send_error_page()
            return

        content_type, _ = mimetypes.guess_type(file_path)
        content = file_path.read_bytes()

        self.send_response(200)
        self.send_header(
            "Content-Type",
            content_type or "application/octet-stream",
        )
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_error_page(self) -> None:
        file_path = BASE_DIR / "error.html"

        if file_path.exists():
            content = file_path.read_bytes()
        else:
            content = b"<h1>404 Not Found</h1>"

        self.send_response(404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def save_message(self, username: str, message: str) -> None:
        STORAGE_DIR.mkdir(exist_ok=True)

        if DATA_FILE.exists():
            try:
                data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                data = {}
        else:
            data = {}

        timestamp = str(datetime.now())

        data[timestamp] = {
            "username": username,
            "message": message,
        }

        DATA_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=4),
            encoding="utf-8",
        )

    def render_messages(self) -> None:
        if DATA_FILE.exists():
            try:
                messages = json.loads(
                    DATA_FILE.read_text(encoding="utf-8")
                )
            except json.JSONDecodeError:
                messages = {}
        else:
            messages = {}

        environment = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR)
        )

        template = environment.get_template("read.html")

        content = template.render(messages=messages).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def run_server() -> None:
    server = HTTPServer((HOST, PORT), WebHandler)

    print(f"Server started at http://localhost:{PORT}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run_server()