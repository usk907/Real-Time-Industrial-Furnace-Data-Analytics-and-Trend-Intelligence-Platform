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
3. **SQL Database (TiDB Cloud MySQL / SQLite `tap_data.db`)**: Stores persistent sensor readings, equipment metadata, alarms, KPIs, and audit logs.
4. **Main Backend Server (Port 8000)**: Reads from the SQL database to compute plant KPIs, generate ARIMA forecasts, serve REST APIs, and broadcast live 1 Hz WebSocket frames (`/api/ws`).
5. **React SPA & Mobile APK Clients**: Connect over WebSockets and HTTPS to display live dashboards anywhere.

---

## 🖥️ Directory Structure

```text
├── .env                           # Environment variables config
├── .dockerignore                  # Docker build exclusions
├── docker-compose.yml             # Full 7-service container stack orchestration
├── README.md                      # Platform documentation & operational runbook
├── walkthrough.md                 # Architecture walkthrough & technical details
├── IEIP-Mobile.apk                # Pre-built native Android application (~4.6 MB)
│
├── start_local.bat / .ps1         # One-click Windows/PowerShell launcher for all 4 services
├── stop_local.bat                 # One-click graceful teardown & port release script
├── tunnel.bat                     # Cloudflare live edge tunnel for remote 4G/5G mobile access
├── build_apk.bat                  # Automated Android APK compilation script (Capacitor + Gradle)
│
├── run_diagnostics.py             # Unified system diagnostics & verification suite
├── check_connectivity.py          # Database & core REST API connectivity checks
├── test_tap_pipeline.py           # TAP Server & SQL pipeline verification script
├── test_all_pages.py              # Full 12-page API connectivity benchmark suite
├── view_db.py                     # Unified database inspector & interactive SQL query CLI
├── query_db.py                    # Backward-compatible CLI query execution wrapper
│
├── tap_server/                    # Dedicated TAP Ingestion Server (Port 8001)
│   ├── Dockerfile                 # Container definition for TAP server
│   ├── main.py                    # TAP Ingestion FastAPI service
│   ├── config.py                  # TAP server settings & batch config
│   ├── database.py                # Unified database connection pool
│   └── models.py                  # Unified SQL schemas
│
├── database/
│   ├── init-db.sql                # PostgreSQL/TimescaleDB relational schemas & seed metadata
│   └── mysql_workbench_setup.sql  # Complete MySQL 8.0+ schema & seed script
│
├── backend/
│   ├── Dockerfile                 # Container definition for Backend API
│   ├── requirements.txt           # Python dependencies (FastAPI, SQLAlchemy, PyMySQL, etc.)
│   └── app/
│       ├── main.py                # FastAPI entrypoint & WebSocket handler
│       ├── config.py              # Environment configuration loader
│       ├── database.py            # Unified database engine & SessionLocal
│       ├── models.py              # 15 SQLAlchemy DB models (including TapTelemetryReading)
│       ├── schemas.py             # Pydantic validation schemas
│       ├── auth.py                # JWT authentication & role-based access control
│       ├── router.py              # REST API controllers & KPI analytics engine
│       ├── ai_query.py            # AI text-to-SQL query engine (Gemini + OpenAI)
│       ├── influx_client.py       # InfluxDB time-series client
│       ├── pdf_importer.py        # CrystalEView SCADA PDF report extractor
│       ├── seeder.py              # Database seeding logic
│       └── websocket_manager.py   # WebSocket broadcast manager
│
├── simulator/
│   ├── Dockerfile                 # Container definition for telemetry simulator
│   ├── requirements.txt           # Simulator Python requirements
│   └── scada_simulator.py         # 1 Hz SCADA simulator streaming 60 furnace tags
│
└── frontend/
    ├── Dockerfile                 # Multi-stage production build (Node 20 -> Nginx)
    ├── nginx.conf                 # Nginx reverse proxy for SPA routes, /api, and /api/ws
    ├── capacitor.config.ts        # Native Android Capacitor configuration
    ├── package.json               # Node dependencies (Vite, TS, Capacitor 8, ECharts)
    ├── vite.config.ts             # Vite dev server with 0.0.0.0 host & API proxy
    ├── android/                   # Native Android Studio / Gradle project shell
    └── src/
        ├── main.tsx               # SPA bootstrapper
        ├── config.ts              # Dynamic network routing & transparent API interceptor
        ├── index.css              # Custom styling & dark-theme scrollbars
        ├── App.tsx                # Client routes & layouts
        ├── types/
        │   └── index.ts           # Centralized TypeScript domain interface definitions
        ├── context/
        │   └── AuthContext.tsx    # Auth state & dynamic WebSocket telemetry context
        ├── components/
        │   ├── Sidebar.tsx        # Collapsible dark navigation sidebar
        │   ├── Header.tsx         # Top bar with profile, alerts & Backend Link pill
        │   ├── ServerSettingsModal.tsx # In-app connection switcher with latency ping check
        │   └── Chatbot.tsx        # Floating AI Assistant Chatbot widget
        └── pages/
            ├── Login.tsx          # Stunning login screen with credentials help
            ├── Dashboard.tsx      # Gauges, live charts, and KPI widgets
            ├── LiveMonitoring.tsx # 1 Hz table displaying all 60 tag registers
            ├── Trends.tsx         # InfluxDB-based ECharts queries & comparisons
            ├── Consumption.tsx    # Shift-wise cumulative energy ledger & sparklines
            ├── Analytics.tsx      # Utilization indices, carbon & cost rollups
            ├── Alarms.tsx         # Critical alarm alerts console
            ├── Reports.tsx        # Daily/Weekly report compilation & CSV/PDF export
            ├── AiQuery.tsx        # AI SQL Query Console (NLP to SQL tool)
            ├── Management.tsx     # CRUD modal screens for plants, machines, devices, users
            ├── Settings.tsx       # Safety range thresholds & Audit log display
            └── ResetPassword.tsx  # Secure password reset page
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
Simply double-click [`start_local.bat`](./start_local.bat) (or run `.\start_local.ps1` in PowerShell).
This automatically starts all 4 services and opens your browser:
1. **TAP Ingestion Server** on `http://localhost:8001`
2. **FastAPI Backend** on `http://localhost:8000`
3. **1 Hz SCADA Simulator** streaming live telemetry
4. **React + Vite Frontend** on `http://localhost:5173`

To cleanly shut down all services at any time, double-click [`stop_local.bat`](./stop_local.bat).

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
```bash
.\tunnel.bat
```
This generates a secure, passwordless `https://*.trycloudflare.com` URL that proxies both the frontend and backend WebSocket/REST telemetry streams.

---

### Option D: Mobile Android APK
- **Pre-Built APK**: A ready-to-install Android package is available in the root:
  👉 **[`IEIP-Mobile.apk`](./IEIP-Mobile.apk)** *(~4.6 MB)*
- **In-App Server Switcher**: Tapping the **Backend Link** pill in the top header opens the Connection Settings modal where you can point the app to any LAN IP (`http://192.168.x.x:8000`), Android emulator (`http://10.0.2.2:8000`), or Cloudflare live tunnel, complete with instant latency ping checks.
- **Rebuilding from Source**:
  Run [`build_apk.bat`](./build_apk.bat) to compile the APK from source using Capacitor 8 and Gradle.

---

### Option E: Manual Multi-Terminal Launch
**Prerequisites**: Python 3.10+ and Node.js 18+ installed on your host system.

Open separate terminal windows in the project root:

1. **Start the TAP Ingestion Server**:
   ```bash
   .\backend\venv\Scripts\activate
   uvicorn tap_server.main:app --host 0.0.0.0 --port 8001
   ```
2. **Start the FastAPI Backend**:
   ```bash
   .\backend\venv\Scripts\activate
   uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
   ```
3. **Start the Telemetry Simulator**:
   ```bash
   .\simulator\venv\Scripts\activate
   python .\simulator\scada_simulator.py
   ```
4. **Start the React Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```
   Open **`http://localhost:5173/`** in your browser.

---

## 🗄️ Database Configuration & Inspection

### 1. MySQL Setup
By default, if no external database is detected, the backend falls back to local SQLite (`furnace.db`). To link your local MySQL instance:
1. Open the `.env` file in the project root.
2. Update the `DATABASE_URL` variable. Note that if your password contains special characters like `@`, it must be percent-encoded:
   ```ini
   DATABASE_URL=mysql+pymysql://<user>:<encoded_password>@127.0.0.1:3306/furnace_db
   ```
3. Establish your schema by running `CREATE DATABASE furnace_db;` in your MySQL console once. The backend will compile the schemas and seed all data automatically on next startup.

### 2. Inspecting the Database (view_db.py)
A CLI database inspector script is available in the root. Run it to inspect record counts and check live inputs in either SQLite or MySQL:
```bash
python view_db.py
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
- *(New users can be registered dynamically via the Management tab by the administrator).*

---

## 🔌 Future Protocols & AI Integration

- **Industrial Hardware Protocols**: The architecture is decoupled so that `scada_simulator.py` can be replaced with standard driver daemons (e.g. using `pymodbus` or `asyncua` for Modbus TCP/OPC-UA links) pointing to `/api/readings/bulk` without any modifications required on the backend database or frontend dashboards.
- **AI Modules**: In `/api/analytics`, placeholder routes are prepared for LSTM-based anomaly detection, predictive remaining useful life (RUL) estimation on electrodes, and PatchTST transformer demand forecasting.
- **AI SQL Query Copilot (Integrated)**: The platform features a natural language database assistant ("AI Database Copilot"). It dynamically translates operator queries in plain English into secure, read-only MySQL queries, executes them, and returns both structured table results and natural language summaries. To enable this, add your Google Gemini API key to `.env`:
   ```ini
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

