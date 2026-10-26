# IEIP Architecture Documentation

The **Industrial Energy Intelligence Platform (IEIP)** is a real-time SCADA and telemetry intelligence platform designed for industrial furnace monitoring, energy analytics, and power distribution supervision.

---

## High-Level Architecture

The platform consists of three decoupled subsystems communicating through local MySQL and standard Web protocols:

```
┌─────────────────────────────────┐
│     Generator (Part 1)          │
│  - 60 Industrial Tags (1 Hz)    │
│  - State preserved in MySQL     │
└──────────────┬──────────────────┘
               │ INSERT (furnace_readings)
               │ REPLACE (furnace_latest)
               ▼
┌─────────────────────────────────┐
│    MySQL Database (Port 3307)   │
│  - furnace_latest (60 rows)     │
│  - furnace_readings (history)   │
│  - users (RBAC & auth)          │
│  - alarms (threshold breaches)  │
└──────────────▲──────────────────┘
               │ SELECT readings / latest
               │ CRUD users & alarms
┌──────────────┴──────────────────┐
│     FastAPI Server (Part 2)     │
│  - Port 8000 (REST & WebSocket) │
│  - JWT Auth & RBAC supervisor   │
│  - 1 Hz Broadcaster & Alarms    │
└──────────────▲──────────────────┘
               │ HTTP / JSON REST
               │ WebSocket /api/ws
┌──────────────┴──────────────────┐
│     React Dashboard (Part 3)    │
│  - Port 5173 (Vite + React)     │
│  - ECharts Visualization        │
│  - Capacitor Android Mobile     │
└─────────────────────────────────┘
```

---

## 1. Subsystem Breakdown

### Part 1: Telemetry Generator (`generator/`)
- Emits real-time industrial SCADA telemetry across **60 standardized tags**:
  - Electric Arc Furnace 1 (EAF-1): 15 tags (kW, kVA, kVAr, V, kA, PF, Temps, Pressures, Water, Energy)
  - Ladle Refining Furnace 2 (LRF-2): 15 tags (kW, kVA, kVAr, V, kA, PF, Temp, Argon, Water, Energy)
  - Main Substation & Transformers (TR-1, TR-2): 15 tags (kV, V, A, kA, kW, kVA, kVAr, PF, Temps, Grid Import)
  - Hot Rolling Mill (RM-1): 8 tags (kW, RPM, Motor Current, Reheat Temps, Descaler, Water, Energy)
  - Water Treatment & Utilities (WTP-1): 7 tags (kW, Current, Pressure, Flow, Supply/Return Temp, Energy)
- On startup, loads current cumulative kWh tag values from `furnace_latest` to ensure energy counters never reset across restarts.
- Performs random walk within physical min/max bounds and commits updates once per second to MySQL.

### Part 2: Backend Application (`server/`)
- High-performance asynchronous FastAPI server running on **port 8000**.
- **Broadcaster Service**: Queries `furnace_latest` once per second in a background loop and pushes unified telemetry frames over `/api/ws` to all active WebSocket clients.
- **Alarm Supervision Engine**: Evaluates live sensor readings against upper/lower threshold definitions, automatically registering new active alarms and resolving cleared alarms.
- **Security & RBAC**: Issues signed JWT tokens using HMAC-SHA256 (`server/.env`). Role-based authorization enforces privileges across `admin`, `manager`, `engineer`, `operator`, and `viewer`.

### Part 3: Frontend Client (`client/`)
- Dark-themed industrial control-room application built with React, TypeScript, Tailwind CSS, and Apache ECharts.
- Connects to `/api/ws` for live streaming gauges and trends, with automatic reconnection and fallback to REST.
- Packaged as a native Android mobile application via `@capacitor/android`.

---

## 2. Port Map & Network Isolation

| Port | Service | Host Interface | Exposure Strategy |
| :--- | :--- | :--- | :--- |
| **3307** | MySQL Database | `127.0.0.1` | **Internal only.** Never exposed to public internet. Least-privilege users. |
| **8000** | FastAPI Backend | `127.0.0.1` | Local development. Exposed publicly only via Cloudflare Tunnel. |
| **5173** | Vite Dev Server | `127.0.0.1` | Local web dashboard. Proxies `/api` to port 8000. |

---

## 3. Database Design (`db/schema.sql`)

1. **`furnace_readings`**: Append-only time-series table storing all historical readings with composite index `(tag, ts)`.
2. **`furnace_latest`**: In-memory / fast lookup table storing exactly 60 rows (one per tag) containing current values and timestamps.
3. **`users`**: User credentials with bcrypt password hashing and assigned RBAC roles.
4. **`alarms`**: Active and acknowledged alarm states, breach values, timestamps, and acknowledging user references.
