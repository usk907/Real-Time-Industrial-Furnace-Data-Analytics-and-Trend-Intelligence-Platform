# Real-Time Industrial Furnace Data Analytics and Trend Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=flat-square&logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0-emerald.svg?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2.0-blue.svg?style=flat-square&logo=react)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.1.6-blue.svg?style=flat-square&logo=typescript)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-blue.svg?style=flat-square&logo=postgresql)](https://www.postgresql.org/)
[![Apache ECharts](https://img.shields.io/badge/Apache_ECharts-5.4.2-red.svg?style=flat-square&logo=apache)](https://echarts.apache.org/)

A high-performance, enterprise-grade industrial analytics and real-time monitoring overlay for steel melting shops (SMS) and power substations. The platform ingests 1 Hz telemetry streams from SCADA systems (supporting OPC UA and Modbus TCP pathways), computes dynamic performance KPIs, executes inline anomaly checks, runs regression forecasts, and displays high-density control-room dashboards.

---

## 🖥️ Platform Visual Layouts

The application user interface is custom-aligned to match professional SCADA dashboards:
* **Data Monitor Tab**: Renders high-contrast rounded parameter tables with yellow headers (**Distribution Parameters**, **SMS-1 Furnace Parameters**, and **SMS-4 Furnace Parameters**) displaying circuit breaker loads, allocated sets, and Ladle/Burner priorities.
* **Trends Tab**: Features an interactive **"Set Parameter Selection" checkboxes modal** to customize and overlay multi-series chart compare trends.
* **Consumption Tab**: Renders a comprehensive 42-parameter audit table showing active grid import/export kWh levels, average power factors, and furnace auxiliary accumulations.

---

## 🏗️ System Architecture

```
         [ SCADA / PLC Registers ] 
                     │  (1 Hz Telemetry)
                     ▼
         [ simulator/scada_simulator.py ]
                     │  (HTTP POST /api/readings/bulk)
                     ▼
         [ backend/ (FastAPI Web Services) ] <───> [ local/PostgreSQL ]
                     │  (WebSocket telemetry stream /api/ws)
                     ▼
         [ frontend/ (Vite + React + TS Dashboard) ]
```

* **SCADA Simulator**: Emulates turbine generators (`TG-1` to `TG-5`), circuit breakers (`CB5214`, `CB14`), and melting shops (`SMS-1` & `SMS-4`) heat cycle physics with periodic anomaly injections (overloads, spikes).
* **FastAPI Backend**: Orchestrates API ingestion, tracks breaker limits, calculates rolling load factors, compiles CSV summaries, and broadcasts frames over WebSockets.
* **React Frontend**: High-density control-room theme with electric blue accents, responsive layouts (including desktop sidebars and mobile bottom tabs), custom SVG dials, and ref-based ECharts.

---

## 📁 Repository Directory Structure

```text
├── start_platform.bat             # Unified Windows Local Host Launcher
├── .gitignore                     # Git ignore rules for node modules and venv
├── README.md                      # Platform overview and setup guidelines
│
├── database/
│   └── init-db.sql                # Robust SQL DDL & Seed values (runs with or without TimescaleDB)
│
├── backend/
│   ├── requirements.txt           # Python backend dependencies
│   └── app/
│       ├── main.py                # FastAPI entry point
│       ├── config.py              # Settings wrapper
│       ├── database.py            # SQLAlchemy Connection Pool Setup
│       ├── models.py              # Database models mapping
│       ├── schemas.py             # Pydantic validation schemas
│       ├── auth.py                # Crypt & token wrappers
│       ├── router.py              # REST controllers, KPI engines, and alerts
│       └── websocket_manager.py   # WebSocket Client Connection coordinator
│
├── simulator/
│   ├── requirements.txt
│   └── scada_simulator.py         # 1 Hz SCADA telemetry simulator client
│
└── frontend/
    ├── package.json               # Node dev requirements
    ├── postcss.config.js
    ├── tailwind.config.js         # Tailwind Utility styling config
    ├── tsconfig.json              # TypeScript specifications
    ├── index.html
    └── src/
        ├── main.tsx
        ├── index.css              # Custom scrollbars and styling rules
        └── App.tsx                # Control room dashboard and custom gauges
```

---

## 🚀 Local Host Installation & Run Steps

### Prerequisite: Database Initialization
Initialize a PostgreSQL instance containing a database named `furnace_db` on port `5432` with username `admin` and password `securepassword`. Execute the initialization script to seed metadata:
```bash
psql -U admin -d furnace_db -f database/init-db.sql
```
*Note: The script dynamically detects if the TimescaleDB extension is active on your server. If it is missing, it falls back to standard indexing, ensuring compatibility on standard PostgreSQL environments.*

### Launching the Platform
To launch all services (Backend, SCADA Simulator, and Frontend Client) simultaneously:
1. Double-click the root file: **`start_platform.bat`**.
2. The batch script will automatically:
   * Scaffold Python virtual environments in `backend/venv` and `simulator/venv`.
   * Install python requirements from `requirements.txt`.
   * Execute `npm install` inside the `frontend/` directory.
   * Open three independent Command Prompt consoles running the live API, simulator, and Vite client.
3. Open your browser and navigate to: **`http://localhost:3000`** to view the live dashboard!

---

## 🔒 Security & User Management

* **Role-Based Access Control**: Standard profiles (`Administrator`, `Plant Engineer`, `Operator`, `Viewer`).
* **Authentication**: Token-based JWT validation checking privileges before database updates or alarm acknowledgment operations.
* **Fallback Simulation Support**: The SCADA simulator client uses direct endpoint calls, bypassing authentication to simplify local testing setups.

---

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.
