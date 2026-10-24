# Industrial Energy Intelligence Platform (IEIP)

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0-emerald.svg?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2.0-blue.svg?style=flat-square&logo=react)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.1.6-blue.svg?style=flat-square&logo=typescript)](https://www.typescriptlang.org/)
[![TimescaleDB](https://img.shields.io/badge/TimescaleDB-PostgreSQL_15-blue.svg?style=flat-square&logo=postgresql)](https://www.timescale.com/)
[![InfluxDB](https://img.shields.io/badge/InfluxDB-2.7-orange.svg?style=flat-square&logo=influxdb)](https://www.influxdata.com/)
[![Redis](https://img.shields.io/badge/Redis-7.0-red.svg?style=flat-square&logo=redis)](https://redis.io/)

IEIP is a production-quality, modular, and containerized Industrial Energy Monitoring and Analytics Web Application. Inspired by SCADA platforms like Crystal e View, it provides a sleek, high-contrast, dark-themed control-room dashboard built on a modern, decoupled architecture designed for high-density telemetry streams.

---

## 🏗️ System Architecture & Dual-Database Strategy

The platform separates fast ingestion paths from heavy query loads by implementing a **dedicated TAP Ingestion Server + SQL storage architecture**:
1. **SCADA Simulator / Industrial PLC**: Streams 60 real-time tag readings every second (1 Hz).
2. **TAP Ingestion Server (Port 8001)**: High-performance data tap service that receives raw telemetry streams, buffers them, and writes high-speed batches directly to the SQL Server (`tap_telemetry_readings`).
3. **SQL Database (TiDB Cloud MySQL / TimescaleDB / SQLite `furnace.db`)**: Stores persistent sensor readings, equipment metadata, alarms, KPIs, and audit logs.
4. **Main Backend Server (Port 8000)**: Reads from the SQL database to compute plant KPIs, generate linear regression forecasts, serve REST APIs, and broadcast live 1 Hz WebSocket frames (`/api/ws`).
5. **React SPA & Mobile APK Clients**: Connect over WebSockets and HTTPS to display live dashboards anywhere.

---

## 🖥️ Modular Directory Structure

```text
├── .env.example                       # Production-ready environment variable template
├── docker-compose.yml                 # Full 7-service container stack orchestration
├── README.md                          # Platform documentation
├── walkthrough.md                     # Architecture walkthrough & technical details
│
├── docs/                              # Architecture, runbooks & specification documents
│   ├── runbook.md                     # Operational procedures, commands, and deployment guides
│   ├── 1_software_requirements_specification.md
│   ├── 2_system_architecture_design.md
│   ├── 3_database_design.md
│   ├── 4_api_specification.md
│   └── 5_implementation_guide.md
│
├── releases/                          # Pre-compiled release artifacts
│   └── IEIP-Mobile.apk                # Production Android application (~4.6 MB)
│
├── scripts/
│   ├── windows/                       # Windows automation scripts
│   │   ├── start_local.bat / .ps1     # One-click Windows/PowerShell launcher for all 4 services
│   │   ├── stop_local.bat / .ps1      # One-click graceful teardown & port release script
│   │   ├── tunnel.bat                 # Cloudflare live edge tunnel for remote 4G/5G mobile access
│   │   └── build_apk.bat              # Automated Android APK compilation script (Capacitor + Gradle)
│   └── tools/
│       └── db_tool.py                 # Unified database inspector & interactive SQL query CLI
│
├── tests/                             # Unified testing & diagnostics suite
│   ├── diagnostics.py                 # System connectivity, TAP ingestion, and benchmark suite
│   ├── helpers.py                     # Shared test session provider, auth tokens & mock data
│   ├── test_tap_pipeline.py           # Ingestion pipeline validation test
│   └── test_all_pages.py              # Full 12-page API connectivity benchmark suite
│
├── database/
│   ├── postgres/
│   │   └── init-db.sql                # PostgreSQL/TimescaleDB relational schemas & seed metadata
│   └── mysql/
│       └── mysql_workbench_setup.sql  # MySQL 8.0+ / TiDB schema & seed script
│
├── services/                          # Independent operational microservices
│   ├── tap_server/                    # Dedicated Port 8001 TAP Ingestion Service
│   │   ├── main.py                    # Fast Ingestion API & buffer management
│   │   ├── config.py                  # Ingestion settings & buffer configuration
│   │   ├── database.py                # Database connector
│   │   ├── models.py                  # SQL schemas
│   │   └── Dockerfile                 # Container image
│   ├── simulator/                     # SCADA 1 Hz Telemetry Generator
│   │   ├── scada_simulator.py         # 1 Hz simulator streaming 60 furnace tags
│   │   ├── requirements.txt           # Simulator Python requirements
│   │   └── Dockerfile                 # Container image
│   └── shared/                        # Shared contracts across services
│       ├── __init__.py
│       └── schemas.py                 # Normalized RawTelemetryItem schema
│
├── backend/
│   ├── Dockerfile                     # Multi-stage production container definition
│   ├── requirements.txt               # Backend Python dependencies (FastAPI, SQLAlchemy, PyMySQL, etc.)
│   └── app/
│       ├── main.py                    # FastAPI entrypoint, CORS, startup seed & WebSocket route
│       ├── config.py                  # BaseSettings loader (.env)
│       ├── database.py                # SQLAlchemy engine & SessionLocal provider
│       ├── models.py                  # 15 SQLAlchemy relational database models
│       ├── schemas.py                 # Pydantic validation models
│       ├── auth.py                    # JWT authentication & RoleChecker RBAC
│       ├── router.py                  # Master API router with backward-compatible re-exports
│       ├── routers/                   # Modular domain-specific sub-routers
│       │   ├── auth.py                # Authentication, password resets & user CRUD
│       │   ├── dashboard.py           # Executive dashboard KPIs & summary stats
│       │   ├── telemetry.py           # Telemetry bulk ingestion, InfluxDB trends & TAP status
│       │   ├── consumption.py         # PowerPlus cumulative energy ledger & PDF imports
│       │   ├── analytics.py           # Energy analytics, load distribution & ML models
│       │   ├── alarms.py              # Alarms console, acknowledgements & notifications
│       │   ├── reports.py             # CSV report generation & downloads
│       │   ├── plants.py              # Plants, departments, machines, and devices CRUD
│       │   ├── settings.py            # Safety thresholds & audit logs
│       │   └── ai.py                  # AI Chatbot & Natural Language text-to-SQL
│       ├── services/                  # Business logic & computation services
│       │   ├── kpi_engine.py          # Rolling averages, load factors, regression & alarms
│       │   └── ai_copilot.py          # Google Gemini NLP-to-SQL & control room assistant
│       ├── influx_client.py           # InfluxDB 2.7 time-series client
│       ├── pdf_importer.py            # CrystalEView SCADA PDF report extractor
│       ├── seeder.py                  # Automated initial database seeder
│       └── websocket_manager.py       # High-concurrency WebSocket broadcaster
│
├── frontend/
│   ├── Dockerfile                     # Multi-stage production build (Node 20 -> Nginx)
│   ├── nginx.conf                     # Nginx reverse proxy for SPA routes, /api, and /api/ws
│   ├── capacitor.config.ts            # Native Android Capacitor configuration
│   ├── package.json                   # React 18, Vite, TypeScript, ECharts, Lucide
│   ├── vite.config.ts                 # Vite bundler with @/ path aliases & API proxy
│   ├── tsconfig.json                  # TypeScript compiler settings with @/* path mapping
│   ├── android/                       # Native Android Studio / Gradle project shell
│   └── src/
│       ├── main.tsx                   # SPA root mounting
│       ├── config.ts                  # Dynamic API routing, transparent fetch interceptor & WS URL
│       ├── index.css                  # Custom styling & dark-theme scrollbars
│       ├── App.tsx                    # React Router client navigation
│       ├── api/                       # Centralized typed API client layer
│       │   ├── client.ts              # Core apiFetch helper with auto Bearer token injection
│       │   ├── telemetry.ts           # Dashboard, trends, and TAP status calls
│       │   ├── consumption.ts         # Energy ledger & PDF report import calls
│       │   ├── alarms.ts              # Alarms & notifications calls
│       │   └── ai.ts                  # AI chat & SQL copilot calls
│       ├── utils/
│       │   └── formatters.ts          # Formatters for kW/MW, kWh/MWh, currency, timestamps
│       ├── types/
│       │   └── index.ts               # Domain TypeScript interfaces
│       ├── context/
│       │   └── AuthContext.tsx        # Auth state & dynamic WebSocket telemetry provider
│       ├── components/
│       │   ├── layout/                # Layout components (Header, Sidebar)
│       │   ├── common/                # Shared widgets (Chatbot, ServerSettingsModal)
│       │   ├── Sidebar.tsx            # Navigation sidebar (with layout mirror)
│       │   ├── Header.tsx             # Top bar with profile & connection status (with layout mirror)
│       │   ├── ServerSettingsModal.tsx# In-app connection switcher with latency ping check
│       │   └── Chatbot.tsx            # Floating AI Assistant Chatbot widget
│       └── pages/
│           ├── Login.tsx              # Control room login screen
│           ├── Dashboard.tsx          # Real-time gauges, live charts, and KPI widgets
│           ├── LiveMonitoring.tsx     # 1 Hz table displaying all 60 tag registers
│           ├── Trends.tsx             # InfluxDB-based ECharts queries & comparisons
│           ├── Consumption.tsx        # Shift-wise cumulative energy ledger & sparklines
│           ├── Analytics.tsx          # Utilization indices, carbon & cost rollups
│           ├── Alarms.tsx             # Critical alarm alerts console
│           ├── Reports.tsx            # Daily/Weekly report compilation & CSV/PDF export
│           ├── AiQuery.tsx            # AI SQL Query Console (NLP to SQL tool)
│           ├── Management.tsx         # CRUD modal screens for plants, machines, devices, users
│           ├── Settings.tsx           # Safety range thresholds & Audit log display
│           └── ResetPassword.tsx      # Secure password reset page
│
└── [Legacy Root Forwarders]           # Thin delegating wrappers for 100% backward compatibility
    ├── start_local.bat / .ps1         # Delegates to scripts/windows/start_local.*
    ├── stop_local.bat                 # Delegates to scripts/windows/stop_local.*
    ├── tunnel.bat                     # Delegates to scripts/windows/tunnel.bat
    ├── build_apk.bat                  # Delegates to scripts/windows/build_apk.bat
    ├── view_db.py / query_db.py       # Delegates to scripts/tools/db_tool.py
    ├── run_diagnostics.py             # Delegates to tests/diagnostics.py
    ├── check_connectivity.py          # Delegates to tests/diagnostics.py
    ├── test_tap_pipeline.py           # Delegates to tests/test_tap_pipeline.py
    └── test_all_pages.py              # Delegates to tests/test_all_pages.py
```

---

## ⚡ PowerPlus Energy Consumption & SCADA Importer

Integrated from the [PowerPlus](https://github.com/Mayur-112005/powerplus.git) architecture:

1. **Daily Energy Consumption Ledger (`/consumption`)**:
   - Real-time date selector and shift filtering (**Shift A**: 06:00–14:00, **Shift B**: 14:00–22:00, **Shift C**: 22:00–06:00, **All Day**).
   - High-contrast summary metrics for **Total Active Energy (`kWh`)**, **Apparent Energy (`kVAh`)**, **Reactive Energy (`kVArh`)**, **Peak Demand (`kW`)**, **Average Power Factor**, and **Cost & Carbon Estimates**.
   - Grouped equipment registers (Furnaces, Auxiliary Transformers, Rolling Mills, Water Treatment) with inline 4-hour sparklines and min/avg/max statistics.
   - One-click **CSV/Excel Export** of filtered ledgers.

2. **CrystalEView SCADA PDF Report Importer**:
   - Backend endpoint `POST /api/reports/import-pdf` powered by `pdfplumber`.
   - Direct upload from the frontend UI to extract tabular columns from real CrystalEView / SCADA energy PDF reports, automatically mapping headers to register tags and syncing history to the database.

---

## 🚀 Execution & Quick Start

### Option A: One-Click Windows Launch (Recommended)
Simply double-click [`start_local.bat`](./start_local.bat) or run:
```powershell
.\scripts\windows\start_local.ps1
```
This automatically starts all 4 services and opens your browser:
1. **TAP Ingestion Server** on `http://localhost:8001`
2. **FastAPI Backend** on `http://localhost:8000`
3. **1 Hz SCADA Simulator** streaming live telemetry
4. **React + Vite Frontend** on `http://localhost:5173`

To cleanly shut down all services at any time, run [`stop_local.bat`](./stop_local.bat) or `.\scripts\windows\stop_local.ps1`.

---

### Option B: Docker Compose (Full Container Stack)
Run the entire production stack (TimescaleDB, InfluxDB 2.7, Redis 7.0, TAP Server, FastAPI Backend, 1 Hz Simulator, and Frontend Nginx) in one command:
```bash
docker compose up -d
```
Access the dashboard at `http://localhost:5173` (or port 80).

---

### Option C: Remote 4G/5G Access & Cloudflare Tunnel
To access the live platform from your mobile phone or outside the local network without port forwarding:
```cmd
.\scripts\windows\tunnel.bat
```
This generates a secure, passwordless `https://*.trycloudflare.com` URL that proxies both the frontend and backend WebSocket/REST telemetry streams.

---

### Option D: Mobile Android APK
- **Pre-Built APK**: A ready-to-install Android package is available in the releases folder:
  👉 **[`releases/IEIP-Mobile.apk`](./releases/IEIP-Mobile.apk)** *(~4.6 MB)*
- **In-App Server Switcher**: Tapping the **Backend Link** pill in the top header opens the Connection Settings modal where you can point the app to any LAN IP (`http://192.168.x.x:8000`), Android emulator (`http://10.0.2.2:8000`), or Cloudflare live tunnel, complete with instant latency ping checks.
- **Rebuilding from Source**:
  Run [`scripts/windows/build_apk.bat`](./scripts/windows/build_apk.bat) to compile the APK from source using Capacitor 8 and Gradle.

---

### Option E: Manual Multi-Terminal Launch
**Prerequisites**: Python 3.10+ and Node.js 18+ installed on your host system.

Open separate terminal windows in the project root:

1. **Start the TAP Ingestion Server**:
   ```bash
   .\backend\venv\Scripts\activate
   uvicorn services.tap_server.main:app --host 0.0.0.0 --port 8001
   ```
2. **Start the FastAPI Backend**:
   ```bash
   .\backend\venv\Scripts\activate
   uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
   ```
3. **Start the Telemetry Simulator**:
   ```bash
   .\simulator\venv\Scripts\activate
   python services\simulator\scada_simulator.py
   ```
4. **Start the React Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```
   Open **`http://localhost:5173/`** in your browser.

---

## 🗄️ Database Configuration & Inspection

### 1. Database Connection Configuration
By default, if no external database is detected, the backend falls back to local SQLite (`furnace.db`). To link your local MySQL or TimescaleDB instance:
1. Copy `.env.example` to `.env` in the project root.
2. Update the `DATABASE_URL` variable:
   ```ini
   DATABASE_URL=mysql+pymysql://<user>:<password>@127.0.0.1:3306/furnace_db
   ```
3. The backend will compile the schemas and seed all initial metadata automatically on next startup.

### 2. Inspecting the Database (`db_tool.py`)
A unified CLI database inspection and query tool is available under `scripts/tools/db_tool.py` (with root wrappers `view_db.py` and `query_db.py`):
```bash
# View table record counts, active alarms, and latest telemetry
python scripts/tools/db_tool.py --inspect

# Execute an arbitrary SQL query with formatted tabular output
python scripts/tools/db_tool.py "SELECT id, username, email FROM users;"
```

---

## 🧪 Testing & System Diagnostics

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
```

---

## 🔒 Security Profiles & Credentials

The platform implements strict JWT authentication. Security checks are enforced via role validation:
- **Admin**: Full access (CRUD on all plants, machines, devices, users, and modifying settings).
- **Plant Manager**: Full CRUD access on plants/departments/machines, views reports, and acknowledges alarms.
- **Engineer**: Read-only access to configurations, can register new machines, download reports, and acknowledge alarms.
- **Operator**: Read-only dashboards and alarms log, can acknowledge alarms.
- **Viewer**: Read-only dashboards.

### Seed Verification Logins (Username / Password)
- **Admin**: `admin` / `admin123`
- *(New users can be registered dynamically via the Management tab by an administrator).*

---

## 🔌 Future Protocols & AI Integration

- **Industrial Hardware Protocols**: The architecture is decoupled so that `scada_simulator.py` can be replaced with standard driver daemons (e.g. using `pymodbus` or `asyncua` for Modbus TCP/OPC-UA links) pointing to `/api/readings/bulk` without any modifications required on the backend database or frontend dashboards.
- **AI Modules**: In `/api/analytics`, placeholder routes are prepared for LSTM-based anomaly detection, predictive remaining useful life (RUL) estimation on electrodes, and PatchTST transformer demand forecasting.
- **AI SQL Query Copilot (Integrated)**: The platform features a natural language database assistant ("AI Database Copilot"). It dynamically translates operator queries in plain English into secure, read-only SQL queries, executes them, and returns both structured table results and natural language summaries. To enable this, add your Google Gemini API key to `.env`:
   ```ini
   GEMINI_API_KEY=your_gemini_api_key_here
   ```
