"""
PredictV Public Ngrok Tunnel Runner
"""
import time
import sys
from pyngrok import ngrok

def run():
    print("Starting PredictV public ngrok tunnel...")
    tunnel = ngrok.connect(8000, "http")
    public_url = tunnel.public_url
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
