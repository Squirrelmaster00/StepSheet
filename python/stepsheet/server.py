"""Serve the StepSheet editor on 127.0.0.1 and open it in the browser.

Stdlib only - no third-party packages, no internet. The page is the full
self-contained StepSheet web app, so opening/saving .soe files and creating
PDFs all happen in the browser on this computer.

If a .soe path is given, it is auto-loaded into the editor on start.
"""
from __future__ import annotations

import http.server
import json
import os
import socket
import threading
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(HERE, "static")

# Set by serve() when a file is passed on the command line.
_AUTOLOAD_BYTES: bytes | None = None
_AUTOLOAD_NAME: str = ""


def _page() -> bytes:
    with open(os.path.join(STATIC, "StepSheet.html"), "r", encoding="utf-8") as f:
        html = f.read()
    if _AUTOLOAD_BYTES is not None:
        # openFromFile() is a global function in the app; hand it a File built
        # from the bytes we serve at /__autoload.soe.
        inject = (
            "<script>(async()=>{try{"
            "const r=await fetch('/__autoload.soe');if(!r.ok)return;"
            "const b=await r.blob();"
            "const f=new File([b]," + json.dumps(_AUTOLOAD_NAME) + ",{type:'application/octet-stream'});"
            "if(window.openFromFile) await window.openFromFile(f);"
            "}catch(e){console.error('autoload failed',e);}})();</script>"
        )
        if "</body>" in html:
            html = html.replace("</body>", inject + "</body>", 1)
        else:
            html += inject
    return html.encode("utf-8")


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "StepSheet/2.0"

    def log_message(self, *a):  # keep the console quiet
        pass

    def _send(self, code, body, ctype):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html", "/StepSheet.html"):
            return self._send(200, _page(), "text/html; charset=utf-8")
        if path == "/__autoload.soe" and _AUTOLOAD_BYTES is not None:
            return self._send(200, _AUTOLOAD_BYTES, "application/octet-stream")
        # any other same-folder static asset (icons, etc.), if present
        safe = os.path.normpath(path.lstrip("/")).replace("\\", "/")
        if safe and ".." not in safe:
            full = os.path.join(STATIC, safe)
            if os.path.isfile(full):
                import mimetypes
                ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
                with open(full, "rb") as f:
                    return self._send(200, f.read(), ctype)
        self._send(404, "not found", "text/plain")


def _free_port(preferred=8731) -> int:
    for port in (preferred, preferred + 1, preferred + 2, 0):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(("127.0.0.1", port))
            p = s.getsockname()[1]
            s.close()
            return p
        except OSError:
            continue
    return 0


def serve(soe_path: str = "", open_browser: bool = True, port: int = 0) -> None:
    global _AUTOLOAD_BYTES, _AUTOLOAD_NAME
    if soe_path:
        if not os.path.isfile(soe_path):
            raise SystemExit(f"File not found: {soe_path}")
        with open(soe_path, "rb") as f:
            _AUTOLOAD_BYTES = f.read()
        _AUTOLOAD_NAME = os.path.basename(soe_path)

    port = port or _free_port()
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}/"
    print(f"StepSheet is running at {url}")
    if _AUTOLOAD_NAME:
        print(f"Loading {_AUTOLOAD_NAME} ...")
    print("Leave this window open while you work. Press Ctrl+C here to stop.")
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        httpd.server_close()
