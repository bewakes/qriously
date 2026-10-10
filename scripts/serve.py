#!/usr/bin/env python3
"""Static file server for local dev that always revalidates.

`python -m http.server` sends only ``Last-Modified``, so browsers cache JS/CSS
heuristically and keep serving stale files after edits (even on some refreshes).
This adds ``Cache-Control: no-store`` so every reload picks up the latest code.

Usage: python3 scripts/serve.py [port] [directory]
"""

import functools
import http.server
import os
import sys


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    directory = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.getcwd()
    handler = functools.partial(NoCacheHandler, directory=directory)
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as httpd:
        print(f"serving {directory} at http://127.0.0.1:{port} (no-store)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
