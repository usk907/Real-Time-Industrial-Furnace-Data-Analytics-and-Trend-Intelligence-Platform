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

The platform separates fast ingestion paths from heavy query loads by implementing a **dual-database write pipeline**:
1. **InfluxDB 2.7**: Stores raw, high-volume time-series telemetry points. Advanced aggregations, resolution resampling, and downsampling are executed directly on InfluxDB using Flux queries.
2. **TimescaleDB / PostgreSQL 15**: Manages relational metadata (plants, departments, machines, devices, users, roles), logs alarms, system events, audit trails, and holds a cache of the last-seen telemetry value.
3. **Redis 7.0**: Acts as an active session cache for JWT token blacklists and as a broker for live WebSocket telemetry broadcasts.

---

## 🖥️ Directory Structure

```text
├── .env                           # Environment variables config
├── README.md                      # Platform documentation
├── view_db.py                     # Database inspector CLI tool
│
├── database/
│   └── init-db.sql                # Relational schemas & Seed metadata
│
├── backend/
│   ├── requirements.txt           # Python dependencies
│   └── app/
│       ├── main.py                # FastAPI entrypoint
│       ├── config.py              # Environment configuration loader
│       ├── database.py            # Database engine setup
│       ├── models.py              # SQLAlchemy DB models
│       ├── schemas.py             # Pydantic validation schemas
│       ├── auth.py                # JWT authentication & Redis blacklisting
│       ├── router.py              # REST API controllers & KPI engine
│       ├── influx_client.py       # InfluxDB connection client
│       └── websocket_manager.py   # WebSocket broadcast manager
│
├── simulator/
│   ├── requirements.txt           # Simulator Python requirements
│   └── scada_simulator.py         # 1 Hz SCADA simulator posting raw tag records
│
└── frontend/
    ├── package.json               # Node dependencies (Vite, TS, Framer, ECharts)
    └── src/
        ├── main.tsx               # SPA bootstrapper
        ├── index.css              # Custom styling & scrollbars
        ├── App.tsx                # Client routes & layouts
        ├── context/
        │   └── AuthContext.tsx    # Auth state & WebSocket telemetry context
        ├── components/
        │   ├── Sidebar.tsx        # Collapsible dark navigation sidebar
        │   └── Header.tsx         # Top bar with profile & alarm notifications
        └── pages/
            ├── Login.tsx          # Stunning login screen with credentials help
            ├── Dashboard.tsx      # Gauges, live charts, and KPI widgets
            ├── LiveMonitoring.tsx # 1 Hz table displaying all 60 tag registers
            ├── Trends.tsx         # InfluxDB-based ECharts queries & comparisons
            ├── Analytics.tsx      # Utilization indices, carbon & cost rollups
            ├── Alarms.tsx         # Acknowledge critical alarm alerts
            ├── Reports.tsx        # Compile and download Daily/Weekly reports
            ├── Management.tsx     # CRUD modal screens for all resources
            └── Settings.tsx       # Safety range thresholds & Audit log display
```

---

## 🚀 Execution & Quick Start
**Prerequisites**: Python 3.10+ and Node.js 18+ installed on your host system.

Open three separate terminal windows in the project root:

1. **Start the FastAPI Backend**:
   ```bash
   cd backend
   python -m venv venv
   .\venv\Scripts\activate      # On Windows (or source venv/bin/activate on Linux/macOS)
   pip install -r requirements.txt
   cd ..
   .\backend\venv\Scripts\uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
   ```
2. **Start the Telemetry Simulator**:
   ```bash
   .\simulator\venv\Scripts\python .\simulator\scada_simulator.py
   ```
3. **Start the React Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Open **`http://localhost:5173/`** to view the live dashboard.

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
