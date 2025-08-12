import http.server
import json
import urllib.parse
import mimetypes
from datetime import datetime
from pathlib import Path

HTTP_PORT = 3000
STORAGE_PATH = Path("./storage")
DATAFILE_PATH = STORAGE_PATH / "data.json"
TEMPLATES_DIR = Path("./templates")


STORAGE_PATH.mkdir(parents=True, exist_ok=True)


class HttpHandler(http.server.BaseHTTPRequestHandler):
    def send_html_file(self, filename: str, status: int = 200) -> None:
        file_path = TEMPLATES_DIR / filename
        if not file_path.exists():
            self.send_error(404, "File not found")
            return
        content = file_path.read_text(encoding="utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content.encode("utf-8"))))
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def send_static_file(self, file_path: Path, status: int = 200) -> None:
        if not file_path.exists() or not file_path.is_file():
            self.send_error(404, "File not found")
            return
        ctype, _ = mimetypes.guess_type(str(file_path))
        ctype = ctype or "application/octet-stream"
        data = file_path.read_bytes()
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):  # noqa: N802 - required name by BaseHTTPRequestHandler
        pr_url = urllib.parse.urlparse(self.path)
        path = pr_url.path

        # HTML routes
        if path in ('/', '/index', '/index.html'):
            self.send_html_file('index.html')
            return
        if path in ('/message', '/message.html'):
            self.send_html_file('message.html')
            return
        if path in ('/error', '/error.html'):
            # Serve the error page with 404 status for explicit /error route
            self.send_html_file('error.html', 404)
            return

        # Favicon (reuse logo.png)
        if path == '/favicon.ico':
            logo_path = Path('logo.png')
            if logo_path.exists():
                self.send_static_file(logo_path)
            else:
                # No favicon available; respond with 204 No Content
                self.send_response(204)
                self.end_headers()
            return

        # Static files like style.css, logo.png
        file_path = Path(path[1:])
        if file_path.exists() and file_path.is_file():
            self.send_static_file(file_path)
        else:
            self.send_html_file('error.html', 404)

    def do_POST(self):  # noqa: N802 - required name by BaseHTTPRequestHandler
        length = int(self.headers.get('Content-Length', '0'))
        raw = self.rfile.read(length).decode('utf-8') if length > 0 else ''
        parsed = urllib.parse.parse_qs(raw)
        message_data = {k: v[0] for k, v in parsed.items()}

        try:
            all_data = {}
            if DATAFILE_PATH.exists():
                with DATAFILE_PATH.open('r', encoding='utf-8') as f:
                    all_data = json.load(f)
            timestamp = datetime.now().isoformat()
            all_data[timestamp] = message_data
            with DATAFILE_PATH.open('w', encoding='utf-8') as f:
                json.dump(all_data, f, ensure_ascii=False, indent=4)
        except (json.JSONDecodeError, OSError):
            self.send_html_file('error.html', 500)
            return

        self.send_response(302)
        self.send_header('Location', '/message')
        self.end_headers()


def run_http_server():
    server = http.server.HTTPServer(('0.0.0.0', HTTP_PORT), HttpHandler)
    print(f"HTTP server running on port {HTTP_PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    run_http_server()