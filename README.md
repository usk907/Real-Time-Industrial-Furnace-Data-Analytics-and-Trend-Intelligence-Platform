# Industrial Energy Intelligence Platform (IEIP)

A modular, decoupled industrial furnace telemetry, energy monitoring, and SCADA control system built across 3 independent tiers communicating strictly via fixed database and network contracts.

```mermaid
flowchart LR
    subgraph Tier1 ["Part 1: Generator"]
        G["Furnace SCADA Generator<br/>(generator.py • 60 Tags)"]
    end

    subgraph DB ["Local MySQL Database (127.0.0.1:3306)"]
        FR[("furnace_readings<br/>(Time-Series Archive)")]
        FL[("furnace_latest<br/>(Real-Time State Cache)")]
        US[("users<br/>(RBAC Accounts)")]
        AL[("alarms<br/>(Incident Logs)")]
    end

    subgraph Tier2 ["Part 2: Server"]
        S["FastAPI Telemetry Server<br/>(Port 8000 • SQLAlchemy 2.0)"]
        B["Broadcaster Task<br/>(1 Query/sec)"]
        A["Alarm Supervisor<br/>(Min/Max Bounds)"]
    end

    subgraph Gateway ["Secure Gateway"]
        T["Cloudflare Tunnel<br/>(cloudflared • HTTPS / WSS)"]
    end

    subgraph Tier3 ["Part 3: Client"]
        W["React 18 / Vite Web Dashboard<br/>(Port 5173 • ECharts)"]
        M["Capacitor Native Android APK<br/>(Mobile Control Room)"]
    end

    G -- "SQL INSERT / REPLACE<br/>(generator_user)" --> DB
    DB -- "SQL SELECT / UPDATE<br/>(server_user)" --> S
    S --- B
    S --- A
    S -- "REST API & WebSocket" --> W
    S -- "HTTP (Local)" --> M
    S -- "Tunnel Forward" --> T
    T -- "HTTPS & WSS (Internet)" --> M
    T -- "HTTPS & WSS (Internet)" --> W
```

---

## 3-Tier Architecture & Communication Contracts

| Tier | Component | Directory | Responsibility | Contract |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1** | **Telemetry Generator** | [`generator/`](file:///c:/Users/kusha/trends%20analysis/generator/) | Generates realistic telemetry for 60 industrial tags every second using bounded random walks. | Writes to MySQL `furnace_readings` and `furnace_latest` via atomic `executemany` transactions. |
| **Database** | **Local MySQL 8** | [`db/`](file:///c:/Users/kusha/trends%20analysis/db/) | Relational time-series and state cache storage bound strictly to `127.0.0.1:3306`. | [`db/schema.sql`](file:///c:/Users/kusha/trends%20analysis/db/schema.sql) & [`db/create_users.sql`](file:///c:/Users/kusha/trends%20analysis/db/create_users.sql). |
| **Tier 2** | **Backend Server** | [`server/`](file:///c:/Users/kusha/trends%20analysis/server/) | FastAPI telemetry backend, JWT authentication, downsampled SQL history, multiplexed WebSocket broadcaster, background alarm supervisor. | Exposes REST & WebSocket API on port 8000; never writes to readings tables. |
| **Tier 3** | **Client & Mobile APK** | [`client/`](file:///c:/Users/kusha/trends%20analysis/client/) | Dark control-room UI (React 18 + Vite + TypeScript) and native Android APK (Capacitor). | Consumes REST + WebSocket API via [`client/src/config.ts`](file:///c:/Users/kusha/trends%20analysis/client/src/config.ts). Never connects to MySQL. |

---

## Network Ports & Exposure Rules

| Port | Service | Bound To | Exposure Rules |
| :--- | :--- | :--- | :--- |
| **3306** | MySQL Database | `127.0.0.1` | **NEVER exposed.** Localhost connection only. No remote root access. |
| **8000** | FastAPI Backend | `127.0.0.1` | Local development. Made public **ONLY** via Cloudflare Tunnel (`cloudflared`). |
| **5173** | Vite Dev Server | `127.0.0.1` | Local developer dashboard. |
| **HTTPS/WSS** | Cloudflare Public Gateway | Cloudflare Edge | Public encrypted entrypoint for browser and mobile Android APK. |

---

## Environment Variables

### Part 1: Generator (`generator/.env`)
| Variable | Default | Description |
| :--- | :--- | :--- |
| `DB_HOST` | `127.0.0.1` | MySQL server hostname (binds to localhost). |
| `DB_PORT` | `3306` | MySQL server port. |
| `DB_USER` | `generator_user` | Least-privilege MySQL user (INSERT/REPLACE on readings only). |
| `DB_PASSWORD` | `GenPassword123!` | Password for `generator_user`. |
| `DB_NAME` | `furnace_db` | Target database name. |
| `GEN_INTERVAL_SECONDS` | `1.0` | Cadence of telemetry emission in seconds. |
| `LOG_INTERVAL_TICKS` | `10` | Output logging cadence (1 line per 10 ticks). |

### Part 2: Server (`server/.env`)
| Variable | Default | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `mysql+pymysql://server_user:...@127.0.0.1:3306/furnace_db` | SQLAlchemy connection string using `server_user`. |
| `JWT_SECRET` | *Strong Random String (Min 32 chars)* | Secret key for signing bearer tokens. Server refuses to start if placeholder is used. |
| `JWT_EXPIRE_MINUTES` | `1440` | JWT token validity lifespan (24 hours). |
| `ADMIN_USERNAME` | `admin` | Initial admin username auto-seeded if user table is empty. |
| `ADMIN_PASSWORD` | *Strong Password (Min 8 chars)* | Initial admin password. Server refuses to start if placeholder is used. |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Explicit whitelist of allowed browser origins (never `*`). |
| `WS_PUSH_INTERVAL_SECONDS` | `1.0` | Multiplexed WebSocket broadcasting interval. |

---

## Start Order & Operating Instructions

To start the platform on your Windows machine, execute the launchers in the following sequence:

### 1. Initialize Database (First-Time Setup Only)
Apply the database schema and least-privilege users:
```bash
mysql -u root -p < db/schema.sql
mysql -u root -p < db/create_users.sql
```

### 2. Start Telemetry Generator (Part 1)
Double-click [`scripts/windows/start_generator.bat`](file:///c:/Users/kusha/trends%20analysis/scripts/windows/start_generator.bat) or run:
```powershell
.\generator\venv\Scripts\python.exe generator\generator.py
```
*Restores previous tag states from `furnace_latest` to preserve cumulative kWh tags across restarts, then emits 60 tags per second.*

### 3. Start Backend Server (Part 2)
Double-click [`scripts/windows/start_server.bat`](file:///c:/Users/kusha/trends%20analysis/scripts/windows/start_server.bat) or run:
```powershell
.\server\venv\Scripts\python.exe -m uvicorn server.app.main:app --host 127.0.0.1 --port 8000 --reload
```
*Seeds initial admin account, initiates the background broadcaster, and supervises live alarm thresholds.*

### 4. Start Frontend Client (Part 3)
Double-click [`scripts/windows/start_client.bat`](file:///c:/Users/kusha/trends%20analysis/scripts/windows/start_client.bat) or run:
```bash
cd client
npm run dev -- --host 127.0.0.1 --port 5173
```
*Opens the dark control-room dashboard at `http://127.0.0.1:5173`.*

### 5. Expose Secure Public Tunnel (Optional / For Mobile APK)
Double-click [`scripts/windows/start_tunnel.bat`](file:///c:/Users/kusha/trends%20analysis/scripts/windows/start_tunnel.bat) or run:
```bash
cloudflared tunnel --url http://localhost:8000
```
*Generates a public URL (e.g. `https://xxxx.trycloudflare.com`) giving secure HTTPS and WSS access.*

---

## Mobile Android APK (Capacitor)

The mobile client is packaged as a native Android APK using Capacitor.
1. Run the build pipeline launcher:
   ```powershell
   .\scripts\windows\build_apk.bat
   ```
2. The script compiles the React web bundle, synchronizes assets to native Android, and outputs the debug binary in:
   ```text
   client/android/app/build/outputs/apk/debug/app-debug.apk
   ```
3. Open the app on your mobile device, tap the **Backend Link** button in the header, and paste your public Cloudflare Tunnel URL or local Wi-Fi IP to stream real-time telemetry anywhere.

---

## Security Model

1. **Least-Privilege Database Isolation**:
   - `generator_user`: INSERT and REPLACE rights on `furnace_readings` and `furnace_latest` only. Cannot read user accounts or alter schemas.
   - `server_user`: SELECT rights on readings tables; SELECT, INSERT, UPDATE on users and alarms. The server can never alter telemetry readings.
   - `admin_user`: Maintenance and retention operations only.
2. **Localhost Binding**:
   - MySQL binds strictly to `127.0.0.1`. Port 3306 is blocked from external networks.
3. **No String-Built Queries**:
   - All historical and live SQL statements use strict parameterized statements (`:tag`, `:from_ts`, `:to_ts`).
4. **Placeholder Password Rejection**:
   - The server inspects `JWT_SECRET` and `ADMIN_PASSWORD` at launch and refuses to start if insecure placeholder strings are found.
5. **SlowAPI Rate Limiting**:
   - The login route (`POST /api/auth/login`) is throttled to 5 requests per minute per IP address.

---

## Automated Verification Suite

Run the test suite from the repository root:
```powershell
# 1. Generator Tag Bounds & Cumulative Monotonicity
.\server\venv\Scripts\python.exe tests/test_generator_tags.py

# 2. Server Authentication, JWT, and Live Telemetry
.\server\venv\Scripts\python.exe -m pytest tests/test_server_auth.py tests/test_server_live.py

# 3. Live WebSocket 3-Frame Stream Verification
.\server\venv\Scripts\python.exe tests/test_ws_client.py

# 4. End-to-End System Smoke Test (Generator -> MySQL -> Server /api/live)
.\server\venv\Scripts\python.exe tests/smoke.py
```

---

## Data Retention Policy
A 7-day retention cleaner is provided to prevent unbounded disk growth:
- **SQL Script**: [`scripts/prune_readings.sql`](file:///c:/Users/kusha/trends%20analysis/scripts/prune_readings.sql)
- **Python Runner**: [`scripts/prune_readings.py`](file:///c:/Users/kusha/trends%20analysis/scripts/prune_readings.py) (can be scheduled via Windows Task Scheduler).

---

## Legacy Code Archive (`legacy/`)

In accordance with strict architectural preservation rules, all previous components were relocated rather than deleted:
- `legacy/services/tap_server/`: High-throughput TAP ingestion server.
- `legacy/services/simulator/`: Multi-furnace SCADA hardware emulator.
- `legacy/influx_client.py`: InfluxDB client and telemetry points builder.
- `legacy/server_archive/`: Monolithic routers (`router.py`, `dashboard.py`, `consumption.py`, `plants.py`, `analytics.py`, `reports.py`, `settings.py`), PDF invoice importer, and AI text-to-SQL copilot (`ai_copilot.py`).
- `legacy/database/`: Previous MySQL Workbench setup scripts and Postgres Docker initialization mounts.
