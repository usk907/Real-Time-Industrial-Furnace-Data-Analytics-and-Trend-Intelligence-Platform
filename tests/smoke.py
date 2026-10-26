"""
End-to-End Smoke Test
Verifies live pipeline: Generator -> MySQL -> Server (/api/live) within 3 seconds.
Run while generator and server are actively running.
"""
import os
import sys
import time
import requests
from datetime import datetime

SERVER_URL = os.getenv("SERVER_URL", "http://127.0.0.1:8000")
ADMIN_USER = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASSWORD")
if not ADMIN_PASS:
    from pathlib import Path
    _env_file = Path(__file__).resolve().parent.parent / "server" / ".env"
    if _env_file.exists():
        for _line in _env_file.read_text(encoding="utf-8").splitlines():
            if _line.strip().startswith("ADMIN_PASSWORD="):
                ADMIN_PASS = _line.split("=", 1)[1].strip().strip("'\"")
                break
if not ADMIN_PASS:
    raise ValueError("ADMIN_PASSWORD must be configured in environment or server/.env")

def run_smoke_test():
    print("=" * 70)
    print("      IEIP END-TO-END SYSTEM SMOKE TEST")
    print("=" * 70)
    print(f"Target Server: {SERVER_URL}")

    # 1. Health check
    try:
        r_health = requests.get(f"{SERVER_URL}/api/health", timeout=3.0)
        assert r_health.status_code == 200, f"Health check failed: {r_health.status_code}"
        health_data = r_health.json()
        print(f"[1/4] Health Check: OK (DB Status: {'CONNECTED' if health_data.get('db_ok') else 'OFFLINE'})")
        assert health_data.get("db_ok"), "Database check reported db_ok=False"
    except Exception as e:
        print(f"[FAIL]: Server unreachable at {SERVER_URL}/api/health: {e}")
        sys.exit(1)

    # 2. Authenticate
    try:
        r_login = requests.post(
            f"{SERVER_URL}/api/auth/login",
            json={"username": ADMIN_USER, "password": ADMIN_PASS},
            timeout=3.0
        )
        assert r_login.status_code == 200, f"Login failed: {r_login.text}"
        token = r_login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"[2/4] Authentication: OK (Logged in as '{ADMIN_USER}')")
    except Exception as e:
        print(f"[FAIL]: Authentication failed: {e}")
        sys.exit(1)

    # 3. Read initial live state
    try:
        r_live1 = requests.get(f"{SERVER_URL}/api/live", headers=headers, timeout=3.0)
        assert r_live1.status_code == 200, f"Live fetch failed: {r_live1.text}"
        tags1 = {t["tag"]: t for t in r_live1.json().get("tags", [])}
        assert len(tags1) == 60, f"Expected 60 tags, got {len(tags1)}"
        sample_tag = "EAF1_Active_Power"
        initial_val = tags1[sample_tag]["value"]
        initial_ts = tags1[sample_tag]["ts"]
        print(f"[3/4] Initial Live Reading: {sample_tag} = {initial_val} (ts: {initial_ts})")
    except Exception as e:
        print(f"[FAIL]: Initial live read failed: {e}")
        sys.exit(1)

    # 4. Wait up to 3 seconds for generator tick to update MySQL and reflect in /api/live
    print("[4/4] Monitoring pipeline for live stream update (waiting up to 3 seconds)...")
    updated = False
    start_wait = time.time()

    while time.time() - start_wait < 3.5:
        time.sleep(1.0)
        r_live2 = requests.get(f"{SERVER_URL}/api/live", headers=headers, timeout=3.0)
        if r_live2.status_code == 200:
            tags2 = {t["tag"]: t for t in r_live2.json().get("tags", [])}
            current_val = tags2[sample_tag]["value"]
            current_ts = tags2[sample_tag]["ts"]
            if current_ts != initial_ts or current_val != initial_val:
                elapsed = round(time.time() - start_wait, 2)
                print(f"[SUCCESS] Telemetry updated in {elapsed}s: {sample_tag} -> {current_val} (ts: {current_ts})")
                updated = True
                break

    if not updated:
        print("[FAIL]: No telemetry update received within 3 seconds. Is generator.py actively running?")
        sys.exit(1)

    print("=" * 70)
    print("      ALL SMOKE CHECKS PASSED: Generator -> MySQL -> /api/live OK")
    print("=" * 70)

if __name__ == "__main__":
    run_smoke_test()
