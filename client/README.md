# IEIP Frontend Client & Mobile APK (Part 3)

React 18 + Vite + TypeScript web application and Capacitor Android APK for the Industrial Energy Intelligence Platform.

## Overview
- **UI Framework**: React 18, Vite, TypeScript, TailwindCSS, ECharts.
- **Theme**: Industrial dark control-room theme.
- **Port**: `5173` (Runs locally on `http://127.0.0.1:5173`).
- **Telemetry Ingestion**: Consumes live SCADA data strictly via the Part 2 server:
  - WebSocket (`/api/ws?token=...`) with automatic exponential backoff reconnection.
  - REST endpoints (`/api/auth/login`, `/api/live`, `/api/history`, `/api/alarms`, `/api/health`).
  - Never connects directly to MySQL.
- **Device Support**: Dual-target deployment (Responsive Web Browser & Native Android APK via Capacitor).

## Network Configuration (`src/config.ts`)
The client resolves the backend server URL in the following priority order:
1. `localStorage.getItem("api_base")` (Set dynamically by clicking the **Backend Link** button in the header).
2. Environment variable `import.meta.env.VITE_API_BASE`.
3. Native Android fallback: `http://10.0.2.2:8000`.
4. Browser default: `http://localhost:8000`.

WebSocket URL is derived automatically:
- `http://...` $\rightarrow$ `ws://.../api/ws`
- `https://...` (Cloudflare Tunnel) $\rightarrow$ `wss://.../api/ws`

## Execution & Development
```bash
# 1. Install dependencies
npm install

# 2. Launch Vite dev server
npm run dev

# 3. Compile production web bundle
npm run build
```

## Android APK Compilation
To compile and package the native Android APK:
```powershell
.\scripts\windows\build_apk.bat
```
Output APK is synchronized and built in `client/android/app/build/outputs/apk/debug/`.
