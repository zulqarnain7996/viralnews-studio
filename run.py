import os
import sys
import socket
import subprocess
import webbrowser
import threading
import time
import uvicorn

def is_port_in_use(port, host="127.0.0.1"):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0

def free_port(port):
    """Safely frees a port on Windows if occupied by an old hanging process."""
    if not is_port_in_use(port):
        return True
    try:
        cmd = f'netstat -ano | findstr :{port}'
        output = subprocess.check_output(cmd, shell=True).decode(errors='ignore')
        current_pid = str(os.getpid())
        for line in output.strip().splitlines():
            parts = line.strip().split()
            # Format: TCP 127.0.0.1:8000 0.0.0.0:0 LISTENING 1234
            if len(parts) >= 5 and "LISTENING" in parts:
                pid = parts[-1]
                if pid != current_pid and pid.isdigit():
                    print(f"[*] Releasing port {port} (stopping previous instance PID {pid})...")
                    subprocess.call(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    time.sleep(1)
        return not is_port_in_use(port)
    except Exception as e:
        print(f"[*] Note while checking port: {e}")
        return False

def open_browser(port):
    time.sleep(1.8)
    url = f"http://127.0.0.1:{port}"
    print(f"\n[ViralNews Studio] Opening dashboard in your browser: {url}")
    webbrowser.open(url)

if __name__ == "__main__":
    target_port = 8000

    print("=" * 60)
    print("   VIRALNEWS STUDIO - AI AND SOCIAL MEDIA NEWS AUTOMATOR")
    print("=" * 60)
    
    # Check if port is in use and attempt to free it
    if is_port_in_use(target_port):
        freed = free_port(target_port)
        if not freed:
            # Fallback to alternate port if port 8000 is still locked
            for alt_port in range(8001, 8010):
                if not is_port_in_use(alt_port):
                    target_port = alt_port
                    break

    print(f"[*] Starting local server on http://127.0.0.1:{target_port}")
    print("[*] Categories: Trending, Pakistan, Local Cities, World")
    print("[*] Features: Bulk Selection, 1080p News Cards, FB & TikTok Poster, Auto-Pilot")
    print("=" * 60)

    # Launch browser automatically
    threading.Thread(target=open_browser, args=(target_port,), daemon=True).start()

    # Run Uvicorn server
    uvicorn.run("app.main:app", host="127.0.0.1", port=target_port, reload=False)
