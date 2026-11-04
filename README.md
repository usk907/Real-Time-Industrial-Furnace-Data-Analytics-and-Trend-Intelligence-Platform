# IEIP — Web Dashboard + Android APK (`branch/client`)

This branch contains both the **FastAPI backend** and the **React frontend**, which runs as:
- 🌐 **Web dashboard** — in any browser via Vite dev server or Nginx
- 📱 **Android APK** — native mobile app via Capacitor (same React codebase, built into APK)

The generator (`branch/generator`) must be running and writing to MySQL for live data.

```
branch/client
├── server/                 ← FastAPI backend (REST + WebSocket, port 8000)
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/
│   │   ├── services/
│   │   ├── auth.py
│   │   ├── models.py
│   │   ├── config.py
│   │   ├── database.py
│   │   └── tag_meta.json
│   ├── requirements.txt
│   └── .env.example        ← Copy → .env, fill in DB + JWT settings
├── client/                 ← React 18 + TypeScript + Vite + Capacitor
│   ├── src/                ← Shared source for web AND APK
│   ├── android/            ← Capacitor native Android project
│   ├── package.json
│   ├── capacitor.config.ts
│   ├── nginx.conf          ← Production web server config
│   └── .env.example        ← Copy → .env, set VITE_API_URL
├── db/
│   ├── schema.sql
│   └── create_users.sql
└── scripts/
    ├── init_database.bat   ← Run ONCE if generator hasn't set up DB yet
    ├── start_server.bat    ← FastAPI on :8000
    ├── start_client.bat    ← Vite web on :5173
    ├── start_all.bat       ← Both server + client together
    ├── stop_all.bat
    ├── start_tunnel.bat    ← Cloudflare Tunnel (remote/mobile access)
    └── build_apk.bat       ← Full Android APK build pipeline
```

---

## Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- MySQL 8.x with schema initialized (see `db/schema.sql`)
- **For APK only:** Java JDK 17 or 21 + Android Studio SDK

---

## Setup

### 1 — Initialize Database *(if generator hasn't done it yet)*

```cmd
scripts\init_database.bat
```

### 2 — Configure the Server

```cmd
copy server\.env.example server\.env
notepad server\.env
```

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | MySQL connection string | `mysql+pymysql://server_user:pw@127.0.0.1:3307/furnace_db` |
| `JWT_SECRET` | Random 32+ char secret key | `change_me_min_32_characters_long` |
| `JWT_EXPIRE_MINUTES` | Token lifetime | `1440` |
| `ADMIN_USERNAME` | First admin account | `admin` |
| `ADMIN_PASSWORD` | First admin password | `securepassword` |
| `CORS_ORIGINS` | Allowed browser origins | `http://localhost:5173` |
| `WS_PUSH_INTERVAL_SECONDS` | WebSocket cadence | `1.0` |

### 3 — Configure the Client

```cmd
copy client\.env.example client\.env
```

| Variable | Web (local) | APK / Remote |
|---|---|---|
| `VITE_API_URL` | Leave **empty** (proxied to :8000) | Set to your Cloudflare Tunnel URL e.g. `https://xxxx.trycloudflare.com` |

> ⚠️ For the **APK build**, `VITE_API_URL` **must** be set to a public URL — the APK cannot reach `localhost`.

### 4 — Install Dependencies

```cmd
cd server
python -m venv venv
venv\Scripts\pip install -r requirements.txt
cd ..\client
npm install
cd ..
```

---

## Run — Web Dashboard

```cmd
scripts\start_all.bat
```

| Service | URL |
|---|---|
| FastAPI backend + WebSocket | http://127.0.0.1:8000 |
| React dashboard | http://127.0.0.1:5173 |

For remote/mobile browser access via Cloudflare Tunnel:
```cmd
scripts\start_tunnel.bat
```

---

## Build — Android APK

### Prerequisites
- Java JDK 17 or 21 (`JAVA_HOME` set, or auto-detected from common install paths)
- Android Studio with SDK (`ANDROID_HOME` set, or auto-detected from `%LOCALAPPDATA%\Android\Sdk`)

### Steps

**1. Set `VITE_API_URL` in `client\.env`** to your public server URL (Cloudflare Tunnel or hosted server):
```
VITE_API_URL=https://xxxx.trycloudflare.com
```

**2. Build:**
```cmd
scripts\build_apk.bat
```

The script will:
1. `npm run build` — compiles React to `client/dist/`
2. `npx cap sync android` — syncs web assets into the native Android project
3. `gradlew assembleDebug` — compiles the native APK
4. Copies output to `releases\IEIP-Mobile.apk`

**3. Install on device:**
```cmd
adb install releases\IEIP-Mobile.apk
```
Or sideload `releases\IEIP-Mobile.apk` directly (enable *Install from unknown sources* in Android settings).

---

## Pre-built APK

A pre-built debug APK is in `releases\IEIP-Mobile.apk`.  
> This was built against the developer's server URL. Rebuild with your own `VITE_API_URL` for production.
