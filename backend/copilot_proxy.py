#!/usr/bin/env python3
"""
Copilot LLM Proxy — lightweight OpenAI-compatible proxy for Codespaces.

Forwards /v1/chat/completions to the GitHub Copilot API using
short-lived tokens obtained via `gh auth`.

Usage:
    python copilot_proxy.py          # port 8080 (default)
    PORT=3000 python copilot_proxy.py
"""

import json
import os
import subprocess
import sys
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.error import HTTPError
from urllib.request import Request, urlopen

PORT = int(os.environ.get("PORT", "8080"))
TOKEN_TTL = 600  # refresh every 10 min (tokens last ~30 min)

_lock = threading.Lock()
_cache: dict = {"token": None, "endpoint": None, "expires": 0}


# ── Token management ────────────────────────────────────────────────

def _fetch_token() -> dict:
    gh_token = subprocess.check_output(
        ["gh", "auth", "token", "-h", "github.com"], text=True
    ).strip()

    req = Request(
        "https://api.github.com/copilot_internal/v2/token",
        headers={
            "Authorization": f"token {gh_token}",
            "Editor-Version": "vscode/1.96.0",
            "Editor-Plugin-Version": "copilot-chat/0.40.0",
        },
    )
    with urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())

    return {
        "token": data["token"],
        "endpoint": data.get("endpoints", {}).get(
            "api", "https://api.enterprise.githubcopilot.com"
        ),
        "expires": time.time() + TOKEN_TTL,
    }


def _get_token():
    with _lock:
        if _cache["token"] is None or time.time() >= _cache["expires"]:
            _cache.update(_fetch_token())
        return _cache["token"], _cache["endpoint"]


# ── HTTP handler ─────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Health check — returns 302 like the real Copilot proxy."""
        self.send_response(302)
        self.send_header("Location", "https://github.com/features/copilot")
        self.end_headers()

    def do_POST(self):
        if self.path != "/v1/chat/completions":
            self._reply(404, {"error": "not found"})
            return

        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))

        try:
            token, endpoint = _get_token()
        except Exception as exc:
            self._reply(502, {"error": f"token error: {exc}"})
            return

        upstream = Request(
            f"{endpoint}/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Editor-Version": "vscode/1.96.0",
                "Copilot-Integration-Id": "vscode-chat",
            },
            method="POST",
        )

        try:
            with urlopen(upstream, timeout=120) as r:
                resp_body = r.read()
                self.send_response(r.status)
                ct = r.headers.get("Content-Type", "application/json")
                self.send_header("Content-Type", ct)
                self.end_headers()
                self.wfile.write(resp_body)
        except HTTPError as exc:
            self.send_response(exc.code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(exc.read())

    # ── helpers ──

    def _reply(self, code: int, obj: dict):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode())

    def log_message(self, fmt, *args):
        # one-line log
        print(f"[proxy] {args[0]}")


# ── main ─────────────────────────────────────────────────────────────

def main():
    try:
        _get_token()
    except Exception as exc:
        print(f"[proxy] FATAL: cannot get Copilot token — {exc}", file=sys.stderr)
        print("[proxy] Run: gh auth login -h github.com -p https -w", file=sys.stderr)
        sys.exit(1)

    print(f"[proxy] Copilot LLM Proxy listening on http://0.0.0.0:{PORT}")
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()


if __name__ == "__main__":
    main()
