from __future__ import annotations
import os
import threading
from angel_platform.webui.server import run as run_ui
from angel_platform.engineering.api import run as run_engineering_api


def main():
    data = os.getenv("ANGEL_DATA_DIR", "/data")
    os.makedirs(data, exist_ok=True)
    host = os.getenv("ANGEL_HOST", "0.0.0.0")
    port = int(os.getenv("ANGEL_PORT", "8765"))
    api_host = os.getenv("ANGEL_ENGINEERING_HOST", "0.0.0.0")
    api_port = int(os.getenv("ANGEL_ENGINEERING_PORT", "8780"))
    api = run_engineering_api(host=api_host, port=api_port)
    threading.Thread(target=api.serve_forever, name="angel-engineering-api", daemon=True).start()
    ui = run_ui(host=host, port=port)
    print(f"Angel Harness workspace: http://127.0.0.1:{port}", flush=True)
    print(f"LocalAI provider: {os.getenv('ANGEL_LOCALAI_BASE_URL', 'http://api:8080')}", flush=True)
    print(f"Persistent Angel data: {data}", flush=True)
    try:
        ui.serve_forever()
    finally:
        ui.shutdown()
        api.shutdown()


if __name__ == "__main__":
    main()
