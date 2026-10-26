# IEIP Operational Runbook

This guide covers initial setup, daily operation, testing, and maintenance of the **Industrial Energy Intelligence Platform (IEIP)**.

---

## 1. Prerequisites

- **Python**: 3.10 or higher
- **Node.js**: 18.x or higher with `npm`
- **MySQL**: MySQL 5.7+ or MariaDB running locally on `127.0.0.1:3307`
- **Cloudflare Tunnel** (`cloudflared` CLI, optional for remote access)
- **Java / Android SDK** (optional for native mobile APK builds)

---

## 2. Initial Setup

### A. Environment Configuration
Copy the template files and fill in strong credentials:
```bash
# Generator environment
cp generator/.env.example generator/.env

# Server environment
cp server/.env.example server/.env
```
> [!NOTE]
> The server and generator validate credentials on startup and will refuse to run if default placeholder values are detected.

### B. Initialize Database & Users
Ensure your MySQL service is running on `127.0.0.1:3307`, then run:
```cmd
scripts\init_database.bat
```
Or execute via python:
```powershell
.\server\venv\Scripts\python.exe scripts\setup_mysql.py
```
This applies `db/schema.sql`, creates least-privilege users (`generator_user`, `server_user`, `admin_user`), and verifies connectivity.

---

## 3. Starting & Stopping Services

### Starting All Services Concurrently
```cmd
scripts\start_all.bat
```
This opens three independent terminal windows:
1. **Generator**: Emits 60 tags once per second to MySQL tables.
2. **Server**: Runs FastAPI backend on `http://127.0.0.1:8000`.
3. **Client**: Starts Vite dev server on `http://127.0.0.1:5173`.

### Starting Services Individually
- **Generator**: `scripts\start_generator.bat`
- **Server**: `scripts\start_server.bat`
- **Client**: `scripts\start_client.bat`

### Stopping All Services
```cmd
scripts\stop_all.bat
```
Gracefully terminates all active IEIP terminal windows.

---

## 4. Verification & Testing

### Automated Test Suite (Pytest)
Run the consolidated test suite from the repository root:
```powershell
.\server\venv\Scripts\python.exe -m pytest -v
```
To run only generator or server suites:
```powershell
.\server\venv\Scripts\python.exe -m pytest generator/tests
.\server\venv\Scripts\python.exe -m pytest server/tests
```

### End-to-End Pipeline Smoke Test
With generator and server actively running, verify the live pipeline:
```powershell
.\server\venv\Scripts\python.exe scripts\smoke_test.py
```

### Live WebSocket Stream Monitor
Verify streaming telemetry frames over WebSockets:
```powershell
.\server\venv\Scripts\python.exe scripts\ws_client.py
```

---

## 5. Android Mobile APK Build

To compile a native Android APK:
```cmd
scripts\build_apk.bat
```
The script compiles web assets, synchronizes Capacitor, invokes Gradle, and places the compiled APK in `releases/IEIP-Mobile.apk`.

---

## 6. Cloudflare Secure Tunnel

To access the server securely from mobile devices or external networks:
```cmd
scripts\start_tunnel.bat
```
Exposes `http://127.0.0.1:8000` via Cloudflare's edge network without opening any firewall ports.

---

## 7. Data Retention & Maintenance

To prune historical telemetry records older than 7 days from `furnace_readings`:
```powershell
$env:DB_PASSWORD="<admin_password>"
.\server\venv\Scripts\python.exe db\prune_readings.py
```
Or execute `db/prune_readings.sql` via MySQL client or Windows Task Scheduler.
