# IEIP FastAPI Server (Part 2)

Dedicated telemetry API and real-time WebSocket control service for the Industrial Energy Intelligence Platform.

## Overview
- **Framework**: FastAPI + SQLAlchemy 2.0 + PyMySQL.
- **Port**: `8000` (Bound locally to `127.0.0.1`).
- **Database Access**: Connects as `server_user` with SELECT-only rights on telemetry readings, and SELECT/INSERT/UPDATE on users and alarms. The server never writes to `furnace_readings` or `furnace_latest`.
- **Security**: JWT authentication on all data endpoints, slowapi rate-limiting on login (5/min per IP), CORS restricted to explicit origin list, parameter-only parameterized SQL queries.

## Endpoints
- `POST /api/auth/login`: Rate-limited authentication endpoint returning JWT with embedded role claims.
- `GET /api/health`: Public system health and database ping check.
- `GET /api/live`: Real-time telemetry snapshot of all 60 tags from `furnace_latest` joined with `tag_meta.json`.
- `GET /api/history`: Time-series query supporting dynamic SQL downsampling (`raw`, `1m`, `5m`, `1h`) with a 5000-point hard limit.
- `GET /api/alarms`: Active or historical alarm event log.
- `POST /api/alarms/{id}/ack`: Role-authorized alarm acknowledgment (`admin`, `manager`, `engineer`, `operator`).
- `WS /api/ws`: WebSocket telemetry stream with JWT handshake validation. Pushes single broadcast frame every second regardless of client count.

## Configuration (`server/.env`)
| Variable | Description | Default |
| :--- | :--- | :--- |
| `DATABASE_URL` | SQLAlchemy connection string | `mysql+pymysql://server_user:...@127.0.0.1:3306/furnace_db` |
| `JWT_SECRET` | Secret key for JWT signing | Strong random string (min 32 chars) |
| `JWT_EXPIRE_MINUTES` | Access token lifespan | `1440` (24 hours) |
| `ADMIN_USERNAME` | Default admin username | `admin` |
| `ADMIN_PASSWORD` | Strong password for auto-created admin | Strong password (min 8 chars) |
| `CORS_ORIGINS` | Permitted browser origins | `http://localhost:5173,http://127.0.0.1:5173` |
| `WS_PUSH_INTERVAL_SECONDS` | Broadcast interval | `1.0` |

## Execution
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env

# 3. Launch server
uvicorn server.app.main:app --host 127.0.0.1 --port 8000 --reload
```
