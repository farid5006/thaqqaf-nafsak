import http.server, json, os, threading, urllib.parse
from typing import Any, Dict, Optional

MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
}

class MatchServer:
    def __init__(self, state=None, web_dir=None, port=8765, on_action=None) -> None:
        self.web_dir = os.path.abspath(web_dir or os.path.join(os.path.dirname(__file__), "web"))
        self.lock = threading.Lock()
        self.state: Dict[str, Any] = state or {}
        self.on_action, self.port = on_action, port
        self._server: Optional[http.server.HTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def _make_handler(self):
        srv = self
        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a) -> None: pass
            def _send(self, code: int, ctype: str, data: bytes) -> None:
                self.send_response(code); self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.send_header("Pragma", "no-cache"); self.send_header("Expires", "0")
                self.end_headers(); self.wfile.write(data)

            def do_GET(self) -> None:
                path = urllib.parse.unquote(urllib.parse.urlparse(self.path).path)
                if path == "/api/state":
                    with srv.lock: return self._send(200, MIME[".json"], json.dumps(srv.state).encode("utf-8"))
                if path == "/api/report":
                    with srv.lock:
                        rep = srv.state.get("html_report") or "<h1>لا يوجد تقرير حالياً</h1>"
                        return self._send(200, MIME[".html"], rep.encode("utf-8"))
                fpath = os.path.abspath(os.path.join(srv.web_dir, "index.html" if path == "/" else path.lstrip("/")))
                if os.path.commonpath([srv.web_dir, fpath]) != srv.web_dir or not os.path.isfile(fpath):
                    return self.send_error(404)
                ext = os.path.splitext(fpath)[1].lower()
                with open(fpath, "rb") as f:
                    self._send(200, MIME.get(ext, "application/octet-stream"), f.read())

            def do_POST(self) -> None:
                if urllib.parse.urlparse(self.path).path != "/api/action": return self.send_error(404)
                try:
                    ln = int(self.headers.get("Content-Length", 0))
                    body = json.loads(self.rfile.read(ln).decode("utf-8") or "{}")
                    with srv.lock:
                        if srv.on_action: srv.on_action(body.get("action", ""), body, srv.state)
                        self._send(200, MIME[".json"], json.dumps(srv.state).encode("utf-8"))
                except Exception as err:
                    self._send(500, MIME[".json"], json.dumps({"error": str(err)}).encode("utf-8"))
        return Handler

    def start(self) -> str:
        if self._server: return self.get_url()
        for p in range(self.port, self.port + 50):
            try:
                self._server, self.port = http.server.HTTPServer(("127.0.0.1", p), self._make_handler()), p
                break
            except OSError: continue
        if not self._server: raise OSError("No free port")
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self.get_url()

    def stop(self) -> None:
        if self._server:
            try:
                self._server.shutdown(); self._server.server_close()
            except Exception: pass
            self._server = None
        if self._thread:
            self._thread.join(timeout=1); self._thread = None

    def get_url(self) -> str: return f"http://127.0.0.1:{self.port}"
