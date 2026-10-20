# Walkthrough: Industrial Energy Intelligence Platform (IEIP)

Below is a comprehensive breakdown of the platform architecture, key gap implementations, unification of similar files, and deployment options.

---

## 🏗️ 1. Complete System Architecture Summary

The platform operates on a high-throughput, decoupled schema running either locally or inside containers:

```
 [ SCADA / PLC Registers ] 
             │  (1 Hz Telemetry with dynamic fluctuations)
             ▼
 [ simulator/scada_simulator.py ]
             │  (HTTP POST /tap/telemetry or /api/readings/bulk)
             ▼
 [ tap_server/ (Port 8001) ] ───> [ SQL Database (TiDB / MySQL / SQLite) ]
                                          ▲
 [ backend/ (FastAPI Port 8000) ] ────────┘
             │                                   - 15 Relational Tables
             │                                   - Alarms, events, audits, settings
             │                                   - Tap telemetry readings
             │                                   - InfluxDB 2.7 time-series cache
             │
             │  (WebSocket /api/ws & REST APIs)
             ▼
 [ frontend/ (Vite + React 18 + TS + Capacitor 8) ]
             ├── Desktop Web (http://localhost:5173)
             ├── Remote 4G/5G Web (Cloudflare Quick Tunnel)
             └── Native Android App (IEIP-Mobile.apk)
```

---

## 🛠️ 2. Key Gap Implementations (Ported from PowerPlus)

### A. One-Click Launch & Teardown
* **`start_local.bat` / `start_local.ps1`**: Starts TAP Ingestion Server (:8001), FastAPI Backend (:8000), 1 Hz SCADA Simulator, and Vite Frontend (:5173), then automatically opens the default web browser.
* **`stop_local.bat`**: Gracefully kills all 4 services and releases ports 8000, 8001, and 5173.

### B. Cloudflare Live Public Tunnel
* **`tunnel.bat`**: Uses `cloudflared` to expose `http://localhost:5173` over a secure `https://*.trycloudflare.com` URL without port forwarding, password walls, or login prompts. Both the frontend and backend APIs (`/api`, `/api/ws`) are routed seamlessly.

### C. Containerization & Docker Compose
* **`docker-compose.yml`**: Full 7-service container stack:
  1. `timescaledb`: PostgreSQL 15 / TimescaleDB with seed schemas
  2. `influxdb`: InfluxDB 2.7 time-series storage
  3. `redis`: Redis 7.0 for token blacklisting & cache
  4. `tap_server`: Port 8001 high-speed ingestion
  5. `backend`: Port 8000 FastAPI REST & WebSocket server
  6. `simulator`: 1 Hz SCADA telemetry streaming daemon
  7. `frontend`: Port 5173 / 80 Nginx reverse proxy

### D. Mobile Android APK & In-App Server Switcher
* **`IEIP-Mobile.apk`**: Pre-built native Android application (~4.6 MB) compiled with Capacitor 8 and Gradle.
* **`build_apk.bat`**: Automated one-click script that compiles web assets, syncs Capacitor, and builds the Android APK.
* **`ServerSettingsModal.tsx`**: In-app modal accessible from the top header **Backend Link** pill. Enables mobile operators to switch API servers (Localhost, Android Emulator, LAN IP, or Cloudflare Tunnel) with instant latency ping checks.

---

## 🔄 3. Unified & Merged Files

| Target | Previous State | Unified Implementation |
| :--- | :--- | :--- |
| **Database Pool** | `tap_server/database.py` had a duplicate engine factory | Now imports and re-exports from `backend.app.database`, sharing pooled connections |
| **Data Models** | `tap_server/models.py` had duplicate `SensorReading` table | Unified in `backend/app/models.py`; `tap_server/models.py` re-exports them |
| **CLI Tools** | `query_db.py` & `view_db.py` had duplicate connection code | Merged query engine into `view_db.py`; `query_db.py` delegates to it |
| **Diagnostics** | `check_connectivity.py`, `test_tap_pipeline.py`, `test_all_pages.py` | Consolidated into `run_diagnostics.py` with individual delegating wrappers |
| **TypeScript Types** | Duplicate interfaces across frontend pages | Centralized in `frontend/src/types/index.ts` |

---

## 🧪 4. Validation Results

1. **Python Validation**:
   - `python -c "import backend.app.models; import tap_server.models; import tap_server.database"` passed with exit code 0.
   - `python check_connectivity.py` passed with exit code 0.
   - `python view_db.py` passed with exit code 0.
   - `python query_db.py "SELECT ..."` passed with exit code 0.
2. **Frontend Validation**:
   - `tsc && vite build` bundled successfully in ~5.8s with 0 errors.
3. **Android Build**:
   - `assembleDebug` compiled successfully in 27s with exit code 0.
