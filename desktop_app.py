import sys
import os
import time
import socket
import threading
import uvicorn

sys.path.insert(0, os.path.abspath("."))
from services.api.main import app

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def start_backend_if_needed():
    if not is_port_in_use(8000):
        print("[Desktop App] Starting local backend server on port 8000...")
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
    else:
        print("[Desktop App] Backend server already running on port 8000. Reusing existing instance.")

def launch_desktop():
    backend_thread = threading.Thread(target=start_backend_if_needed, daemon=True)
    backend_thread.start()
    time.sleep(0.5)

    try:
        import webview
        print("[Desktop App] Opening Native Windows Desktop Window...")
        webview.create_window(
            title="ASTHA ERP — Astha Builders & Hardware (Desktop App)",
            url="http://127.0.0.1:8000",
            width=1280,
            height=820,
            resizable=True,
            min_size=(900, 600)
        )
        webview.start()
    except Exception as e:
        print(f"[Desktop App] PyWebView fallback ({e}): opening browser...")
        import webbrowser
        webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    launch_desktop()
