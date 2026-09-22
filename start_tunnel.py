"""
PredictV Public Ngrok Tunnel Runner
"""
import time
import sys
from pyngrok import ngrok

import socket
import subprocess
from pathlib import Path

def is_backend_running(host="127.0.0.1", port=8000):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0

def ensure_backend():
    if not is_backend_running():
        print("[INFO] Port 8000 is not active. Starting FastAPI backend server...")
        backend_dir = Path(__file__).resolve().parent / "backend"
        subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=str(backend_dir),
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
        )
        print("[INFO] Waiting for backend to initialize...")
        for _ in range(15):
            time.sleep(1)
            if is_backend_running():
                print("[OK] Backend is live on http://127.0.0.1:8000")
                return
        print("[WARN] Backend started, proceeding with tunnel...")
    else:
        print("[OK] Backend server is already running on http://127.0.0.1:8000")

def run():
    ensure_backend()
    print("Starting PredictV public ngrok tunnel...")
    tunnel = ngrok.connect("8000", "http")
    public_url = tunnel.public_url
    if not public_url:
        print("Error: Failed to obtain public URL from ngrok.")
        sys.exit(1)

    print(f"\n==========================================")
    print(f"  PREDICTV LIVE PUBLIC URL: {public_url}")
    print(f"==========================================\n")
    
    with open("tunnel_url.txt", "w", encoding="utf-8") as f:
        f.write(public_url)
    
    sys.stdout.flush()
    
    # Keep alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        ngrok.disconnect(public_url)

if __name__ == "__main__":
    run()
