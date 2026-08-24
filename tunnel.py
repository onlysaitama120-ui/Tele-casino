#!/usr/bin/env python3
"""Quick HTTPS tunnel for Telegram mini app testing."""

import asyncio
import threading
import time
from pyngrok import ngrok
import uvicorn
from api.server import app

# Start tunnel
print("[*] Starting HTTPS tunnel...")
public_url = ngrok.connect(8000).public_url
print(f"[+] HTTPS URL: {public_url}")
print(f"[+] Update config.py WEBAPP_URL to: {public_url}")
print()
print("NOW UPDATE YOUR BOT:")
print(f"1. Open @BotFather")
print(f"2. Send /setmenubutton")
print(f"3. Select @MyCasinoBotx_bot")
print(f"4. Set URL to: {public_url}")
print()
print("Or just test locally first:")
print(f"   Open: {public_url}")
print()

# Start server in thread
def run_server():
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")

server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()

print("[+] Server running on HTTPS!")
print("[*] Press Ctrl+C to stop")
print()

# Keep alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    ngrok.kill()
    print("/n[+] Stopped")
