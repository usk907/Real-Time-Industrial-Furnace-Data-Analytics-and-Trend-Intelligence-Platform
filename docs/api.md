# IEIP API Specification

The IEIP FastAPI backend runs on `http://127.0.0.1:8000`. Interactive OpenAPI documentation is available locally at `http://127.0.0.1:8000/docs`.

---

## Authentication

All protected endpoints require a Bearer token in the HTTP `Authorization` header:
```http
Authorization: Bearer <access_token>
```
For WebSocket streaming, provide the token as a query parameter:
```
ws://127.0.0.1:8000/api/ws?token=<access_token>
```

---

## REST Endpoints

### 1. Health Probe
- **`GET /api/health`**
  - **Auth**: None
  - **Response `200 OK`**:
    ```json
    {
      "status": "healthy",
      "db_ok": true,
      "timestamp": "2026-10-26T14:15:00.000000"
    }
    ```

---

### 2. Authentication
- **`POST /api/auth/login`**
  - **Auth**: None
  - **Request Body**:
    ```json
    {
      "username": "admin",
      "password": "<your_password>"
    }
    ```
  - **Response `200 OK`**:
    ```json
    {
      "access_token": "eyJhbGciOi...",
      "token_type": "bearer",
      "role": "admin",
      "username": "admin"
    }
    ```

- **`GET /api/auth/me`**
  - **Auth**: Required
  - **Response `200 OK`**: Current authenticated user profile with assigned RBAC role.

---

### 3. Live Telemetry
- **`GET /api/live`**
  - **Auth**: Required
  - **Description**: Returns the latest reading for all 60 furnace and equipment tags joined with metadata.
  - **Response `200 OK`**:
    ```json
    {
      "tags": [
        {
          "tag": "EAF1_Active_Power",
          "value": 42150.0,
          "unit": "kW",
          "status": "OK",
          "ts": "2026-10-26T14:15:00.000000",
          "equipment": "Electric Arc Furnace 1",
          "min": 15000.0,
          "max": 55000.0
        }
      ],
      "count": 60,
      "ts": "2026-10-26T14:15:00.000000"
    }
    ```

---

### 4. Historical Telemetry & Aggregation
- **`GET /api/history`**
  - **Auth**: Required
  - **Query Parameters**:
    - `tag` (string, required): Tag name (e.g., `EAF1_Active_Power`)
    - `from_ts` (ISO datetime string, required): Range start
    - `to_ts` (ISO datetime string, required): Range end
    - `bucket` (string, optional): `none`, `1m`, `5m`, `15m`, `1h`, `1d`
  - **Response `200 OK`**:
    ```json
    {
      "tag": "EAF1_Active_Power",
      "bucket": "1m",
      "points": [
        {
          "ts": "2026-10-26T14:00:00",
          "value": 41800.5,
          "min": 41200.0,
          "max": 42400.0,
          "count": 60
        }
      ]
    }
    ```

---

### 5. Alarm Supervision
- **`GET /api/alarms`**
  - **Auth**: Required
  - **Query Parameters**:
    - `status` (string, optional): `ACTIVE`, `ACKNOWLEDGED`, `CLEARED`, or `ALL`
  - **Response `200 OK`**: List of alarms with breach severity, tag, trigger value, and timestamps.

- **`POST /api/alarms/{id}/ack`**
  - **Auth**: Required (`admin`, `manager`, `engineer`, `operator` roles)
  - **Description**: Acknowledges active alarm instance.

---

## WebSocket Telemetry Stream

- **`ws://127.0.0.1:8000/api/ws?token=<access_token>`**
  - **Broadcast Rate**: 1.0 Hz (configurable via `WS_PUSH_INTERVAL_SECONDS`)
  - **Frame Payload**:
    ```json
    {
      "ts": "2026-10-26T14:15:00.000000",
      "tags": [
        {
          "tag": "EAF1_Active_Power",
          "value": 42150.0,
          "unit": "kW",
          "status": "OK"
        }
      ]
    }
    ```
