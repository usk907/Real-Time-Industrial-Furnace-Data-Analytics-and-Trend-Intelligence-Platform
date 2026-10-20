"""
IEIP Unified System Diagnostics & Verification Suite
Consolidates system connectivity, TAP ingestion server testing, and full page API verification.
"""
import os
import sys
import time
import requests

# Ensure repository root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from tests.helpers import (
    TOKEN,
    HEADERS,
    BACKEND_BASE_URL,
    TAP_BASE_URL,
    generate_sample_telemetry_batch,
    get_test_session
)

def run_connectivity():
    """Runs basic database and core API connectivity checks."""
    print("=" * 70)
    print("      IEIP PLATFORM SYSTEM CONNECTIVITY DIAGNOSTICS")
    print("=" * 70)

    # 1. Database Connectivity
    try:
        from backend.app.database import SessionLocal
        from backend.app.models import User, Plant, Machine, Device, SensorReading
        db = SessionLocal()
        u_count = db.query(User).count()
        p_count = db.query(Plant).count()
        m_count = db.query(Machine).count()
        d_count = db.query(Device).count()
        r_count = db.query(SensorReading).count()
        db.close()
        print("[1] DATABASE LINK:")
        print("    --> Status: [CONNECTED / ONLINE]")
        print(f"    --> Metadata: {p_count} Plants, {m_count} Machines, {d_count} Tags/Registers")
        print(f"    --> Telemetry Records: {r_count:,} sensor readings in database")
    except Exception as e:
        print(f"[1] DATABASE LINK: [ERROR] - {e}")

    print("-" * 70)

    # 2. Backend REST API
    try:
        r = requests.get(f"{BACKEND_BASE_URL}/api/dashboard", headers=HEADERS, timeout=3)
        if r.status_code == 200:
            print(f"[2] FASTAPI BACKEND SERVER ({BACKEND_BASE_URL}):")
            print("    --> Status: [ONLINE / ACTIVE - HTTP 200 OK]")
            print(f"    --> Swagger UI: {BACKEND_BASE_URL}/docs")
        else:
            print(f"[2] FASTAPI BACKEND SERVER: [WARNING - HTTP {r.status_code}]")
    except Exception:
        print("[2] FASTAPI BACKEND SERVER: [NOT RUNNING / OFFLINE]")

    print("-" * 70)

    # 3. Energy Consumption API
    try:
        r = requests.get(f"{BACKEND_BASE_URL}/api/consumption", headers=HEADERS, timeout=3)
        if r.status_code == 200:
            data = r.json()
            kwh = data.get("summary", {}).get("total_active_kwh", 0)
            groups = len(data.get("equipment_groups", []))
            print("[3] ENERGY CONSUMPTION LEDGER API:")
            print("    --> Status: [ONLINE / ACTIVE - HTTP 200 OK]")
            print(f"    --> Aggregation: {groups} equipment groups, {kwh:,.1f} kWh total active energy")
        else:
            print(f"[3] ENERGY CONSUMPTION API: [HTTP {r.status_code}]")
    except Exception:
        print("[3] ENERGY CONSUMPTION API: [WAITING FOR BACKEND SERVER]")

    print("=" * 70)

def run_tap_pipeline():
    """Runs verification tests for TAP Ingestion Server on Port 8001."""
    print("=" * 70)
    print("      IEIP PLATFORM: TAP SERVER & SQL PIPELINE VERIFICATION")
    print("=" * 70)

    tap_health = f"{TAP_BASE_URL}/tap/health"
    tap_telemetry = f"{TAP_BASE_URL}/tap/telemetry"
    tap_stats = f"{TAP_BASE_URL}/tap/stats"

    # Step 1: Health
    print("\n[Step 1] Checking TAP Server Health (Port 8001)...")
    try:
        r = requests.get(tap_health, timeout=3)
        if r.status_code == 200:
            info = r.json()
            print(f"  [ PASS ] TAP Server is ONLINE: {info.get('service')} on Port {info.get('port')}")
            print(f"           Target SQL Engine: {info.get('database_url_type')} | Records: {info.get('total_records_in_sql')}")
        else:
            print(f"  [ FAIL ] TAP Server returned HTTP {r.status_code}")
            return False
    except Exception as e:
        print(f"  [ FAIL ] Could not reach TAP Server at {tap_health}: {e}")
        return False

    # Step 2: Sample batch write
    print("\n[Step 2] Sending Test Telemetry Batch to TAP Server...")
    test_batch = generate_sample_telemetry_batch()
    try:
        r = requests.post(tap_telemetry, json=test_batch, timeout=3)
        if r.status_code == 200:
            print(f"  [ PASS ] TAP Ingest acknowledged {len(test_batch)} readings ({r.json().get('status')})")
        else:
            print(f"  [ FAIL ] Batch rejected: HTTP {r.status_code}")
            return False
    except Exception as e:
        print(f"  [ FAIL ] Error posting telemetry: {e}")
        return False

    # Step 3: Check statistics
    print("\n[Step 3] Verifying TAP Ingestion Metrics...")
    try:
        r = requests.get(tap_stats, timeout=3)
        if r.status_code == 200:
            stats = r.json()
            print(f"  [ PASS ] Total Records Ingested: {stats.get('total_records_ingested')}")
            print(f"           Write Latency: {stats.get('last_write_latency_ms')} ms")
        else:
            print(f"  [ FAIL ] Stats returned HTTP {r.status_code}")
    except Exception as e:
        print(f"  [ FAIL ] Stats error: {e}")

    print("=" * 70)
    return True

def run_all_pages():
    """Runs comprehensive connectivity and latency benchmark across all 12 page APIs."""
    print("=" * 70)
    print("      IEIP PLATFORM: COMPREHENSIVE PAGE API BENCHMARK")
    print("=" * 70)

    session = get_test_session()
    tests = [
        ("Executive Dashboard", "GET", "/api/dashboard", None),
        ("Notifications", "GET", "/api/notifications", None),
        ("Live Monitoring", "GET", "/api/devices", None),
        ("Trend Analysis", "GET", "/api/trends?sensor_id=1&quick_filter=1h", None),
        ("Consumption Ledger", "GET", "/api/consumption?shift=ALL", None),
        ("Advanced Analytics", "GET", "/api/analytics", None),
        ("Alarms Console", "GET", "/api/alarms", None),
        ("Shift Reports", "GET", "/api/reports", None),
        ("Resource Management", "GET", "/api/plants", None),
        ("System Settings", "GET", "/api/settings", None),
        ("Security Audit Trail", "GET", "/api/audit-logs", None),
        ("User Profile & Auth", "GET", "/api/auth/me", None),
        ("TAP Bridge Status", "GET", "/api/tap/status", None),
        ("AI Database Copilot", "POST", "/api/ai/query", {"question": "List active plants"})
    ]

    passed = 0
    for page, method, path, payload in tests:
        url = f"{BACKEND_BASE_URL}{path}"
        start = time.time()
        try:
            if method == "GET":
                r = session.get(url, timeout=10)
            else:
                r = session.post(url, json=payload, timeout=20)
            latency = round((time.time() - start) * 1000, 1)
            ok = r.status_code in [200, 201]
            status_str = "PASS" if ok else f"HTTP {r.status_code}"
            print(f"[{status_str:^7}] {page:<24} | {path:<34} | {latency:>6}ms", flush=True)
            if ok:
                passed += 1
        except Exception as e:
            print(f"[ FAIL  ] {page:<24} | {path:<34} | Error: {e}", flush=True)

    print("-" * 70)
    print(f"Results: {passed} / {len(tests)} endpoints passed.")
    print("=" * 70)

if __name__ == "__main__":
    arg = sys.argv[1].lower() if len(sys.argv) > 1 else "--all"
    if arg in ["--conn", "--connectivity", "-c"]:
        run_connectivity()
    elif arg in ["--tap", "-t"]:
        run_tap_pipeline()
    elif arg in ["--pages", "-p"]:
        run_all_pages()
    else:
        run_connectivity()
        print("\n")
        run_tap_pipeline()
        print("\n")
        run_all_pages()
