# IEIP Platform Runbook & Operational Guide

This document describes how to operate, test, build, and maintain the **Industrial Energy Intelligence Platform (IEIP)**.

---

## 1. Directory Structure Overview

```text
├── backend/            # FastAPI REST & WebSocket server
├── tap_server/         # High-throughput industrial telemetry ingestion server (Port 8001)
├── simulator/          # SCADA PLC/RTU telemetry simulator (1 Hz)
├── frontend/           # React 19 + TypeScript + Vite + Tailwind CSS + Capacitor
├── database/
│   ├── mysql/          # MySQL / TiDB Workbench migration & setup scripts
│   └── postgres/       # TimescaleDB initialization scripts
├── scripts/
│   ├── tools/          # Unified database inspection & query CLI (`db_tool.py`)
│   └── windows/        # Local process management, cloudflare tunnels, APK builder
├── tests/              # Diagnostics, pipeline checks, and page API benchmarks
├── releases/           # Pre-compiled release artifacts (e.g. `IEIP-Mobile.apk`)
└── docs/               # System architecture, API specifications, and database designs
```

---

## 2. Starting & Stopping Services

### Local Windows Development (Direct Processes)
You can launch or stop all four services (Backend, TAP Ingestion, SCADA Simulator, React Vite Frontend) via PowerShell or Batch:

- **Start Services**:
  ```powershell
  # Recommended:
  .\scripts\windows\start_local.ps1
  # Or legacy wrapper:
  .\start_local.bat
  ```
- **Stop Services**:
  ```powershell
  # Recommended:
  .\scripts\windows\stop_local.ps1
  # Or legacy wrapper:
  .\stop_local.bat
  ```

### Docker Compose Stack
For containerized deployment (TimescaleDB, InfluxDB, Redis, TAP Server, Backend, Simulator, Frontend):
```bash
docker compose up -d --build
docker compose ps
docker compose logs -f
```

---

## 3. Database Administration & Inspection

Use the unified `db_tool.py` located at `scripts/tools/db_tool.py` (or legacy root wrappers `view_db.py` / `query_db.py`):

```bash
# 1. Inspect table counts, active alarms, and latest telemetry
python scripts/tools/db_tool.py --inspect

# 2. Run an ad-hoc SQL query with formatted output
python scripts/tools/db_tool.py "SELECT count(*) FROM sensor_readings;"

# Legacy shortcuts (at project root):
python view_db.py
python query_db.py "SELECT username, email FROM users;"
```

---

## 4. Testing & System Diagnostics

Centralized under `tests/`:

```bash
# Run database & service connectivity check
python tests/diagnostics.py --connectivity

# Run TAP server 8001 ingestion batch verification
python tests/diagnostics.py --tap

# Run comprehensive latency benchmark across all 12 page APIs
python tests/diagnostics.py --pages

# Run the full diagnostic suite
python tests/diagnostics.py --all

# Legacy shortcuts (at project root):
python run_diagnostics.py
python check_connectivity.py
python test_tap_pipeline.py
python test_all_pages.py
```

---

## 5. Android Mobile APK Compilation

To build a standalone Android APK using Capacitor:

```cmd
:: Run build script
.\scripts\windows\build_apk.bat
```
The output APK is automatically placed in:
`releases/IEIP-Mobile.apk`

---

## 6. Remote Access & Cloudflare Live Tunnel

To expose the local development server (port 5173 and backend proxy) securely to the internet:
```cmd
.\scripts\windows\tunnel.bat
```
This generates a temporary `*.trycloudflare.com` public URL accessible from any mobile device on 4G/5G.
