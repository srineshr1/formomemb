#!/usr/bin/env python3
"""
gallery_serve.py — Local dev server for the Design Gallery
Run: python gallery_serve.py
Then open http://localhost:8000 on your phone (same WiFi)
"""
import http.server, socketserver, os, socket

PORT = 8000
os.chdir(os.path.dirname(os.path.abspath(__file__)))

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args): pass  # quiet

# Get local IP for mobile access
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()

ip = get_ip()
print(f"\n  ┌─────────────────────────────────────────┐")
print(f"  │  Design Gallery running                  │")
print(f"  │  Local:  http://localhost:{PORT}           │")
print(f"  │  Mobile: http://{ip}:{PORT}      │")
print(f"  │  Ctrl+C to stop                          │")
print(f"  └─────────────────────────────────────────┘\n")

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
