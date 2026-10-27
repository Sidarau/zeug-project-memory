"""A local stand-in for cmd.zeuglab.com, for testing the installers and zm without a real key.

Serves this repository under /repo/ (so the installers fetch the files being tested) and the agent API under
/api/agent/ for one fake key. Usage: python3 tests/mock_cmd.py <repo dir> [port]
"""
import http.server
import json
import os
import sys
import urllib.parse

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8765
KEY = "Bearer zlm_" + "T" * 43
NOTES: list[dict] = []


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code: int, body: object, kind: str = "application/json") -> None:
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        url = urllib.parse.urlsplit(self.path)
        if url.path.startswith("/repo/"):
            path = os.path.normpath(os.path.join(ROOT, url.path[len("/repo/"):]))
            if not path.startswith(ROOT) or not os.path.isfile(path):
                return self.send(404, {"error": "not found"})
            with open(path, "rb") as f:
                return self.send(200, f.read(), "text/plain")
        if self.headers.get("Authorization") != KEY:
            return self.send(401, {"error": "Missing, revoked or unknown access key."})
        if url.path == "/api/agent/project":
            return self.send(200, {"project": "zz-ci", "name": "CI", "memory": {"enabled": True, "notes": len(NOTES)},
                                   "documents": [], "drops": []})
        if url.path == "/api/agent/memory":
            q = urllib.parse.parse_qs(url.query).get("q", [""])[0].lower()
            if q:
                return self.send(200, {"project": "zz-ci", "results": [n for n in NOTES if q in (n["title"] + n["text"]).lower()]})
            return self.send(200, {"project": "zz-ci", "notes": NOTES})
        if url.path.startswith("/api/agent/documents/"):
            return self.send(404, {"error": "No such document in this project."})
        self.send(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.headers.get("Authorization") != KEY:
            return self.send(401, {"error": "Missing, revoked or unknown access key."})
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode("utf-8")
        if "x-www-form-urlencoded" in self.headers.get("Content-Type", ""):
            body = {k: v[0] for k, v in urllib.parse.parse_qs(raw).items()}
        else:
            body = json.loads(raw or "{}")
        if len(body.get("text", "").strip()) < 20:
            return self.send(400, {"error": "Write at least 20 characters."})
        NOTES.append({"title": body.get("title", ""), "text": body["text"]})
        self.send(201, {"project": "zz-ci", "id": str(len(NOTES))})


http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
