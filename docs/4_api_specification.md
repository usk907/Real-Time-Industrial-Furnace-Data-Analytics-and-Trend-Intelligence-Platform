# REST API & WebSocket Specification
## Real-Time Industrial Furnace Data Analytics and Trend Prediction System Using SCADA Data

---

### 1. Global API Configuration

* **Protocol**: HTTPS / WSS
* **Base URL Path**: `/api/v1`
* **Default Request/Response Format**: `application/json`
* **Authentication**: JWT token passed in the HTTP Authorization header:
  `Authorization: Bearer <JWT_TOKEN_HERE>`
* **CORS Policy**: Restrict access to registered web server hostnames.

#### 1.1 Standard Error Codes
All endpoints return standard JSON error schemas on failure:

```json
{
  "status_code": 400,
  "error": "Bad Request",
  "message": "Invalid time range format. Use ISO-8601 formatting.",
  "timestamp": "2026-06-30T13:48:00Z"
}
```

* `400 Bad Request`: Incorrect input payload parameters.
* `401 Unauthorized`: Token missing or expired.
* `403 Forbidden`: Insufficient role hierarchy permissions.
* `404 Not Found`: Target resource identifier does not exist.
* `422 Unprocessable Entity`: Validation failure on input schema values.
* `500 Internal Server Error`: Server exception.
* `503 Service Unavailable`: TimescaleDB connection drop or Redis timeout.

---

### 2. SCADA Ingestion & Sensor Endpoints

#### 2.1 Bulk Ingest Telemetry Stream
Allows ingestion drivers to submit SCADA frames in batches.

* **HTTP Method**: `POST`
* **Path**: `/sensors/telemetry`
* **Access Level**: Ingestion Client / Administrator
* **Payload Schema**:

```json
{
  "timestamp": "2026-06-30T13:48:00.000Z",
  "furnace_id": 1,
  "metrics": [
    { "sensor_id": 1, "value": 11020.5 },
    { "sensor_id": 2, "value": 450.2 },
    { "sensor_id": 3, "value": 1250.0 },
    { "sensor_id": 4, "value": 85.3 },
    { "sensor_id": 5, "value": 0.92 }
  ]
}
```

* **Response (202 Accepted)**:

```json
{
  "status": "ACCEPTED",
  "ingested_records": 5,
  "anomalies_detected": 0
}
```

#### 2.2 Get Sensor Metadata List
Fetch sensor channels registered in the environment.

* **HTTP Method**: `GET`
* **Path**: `/sensors`
* **Access Level**: Read-Only Operator / Engineer / Admin
* **Query Parameters**:
  * `furnace_id` (Integer, Optional): Filter sensors by furnace.
  * `is_active` (Boolean, Optional): Filter by active status.
* **Response (200 OK)**:

```json
[
  {
    "sensor_id": 1,
    "furnace_id": 1,
    "name": "Voltage Phase A",
    "register_address": "40001",
    "unit": "V",
    "nominal_min": 10500.0,
    "nominal_max": 11500.0,
    "is_active": true
  }
]
```

---

### 3. Trend Analytics & Statistics Endpoints

#### 3.1 Fetch Trend Metrics
Query historical time-series averages and regression slopes for ECharts.

* **HTTP Method**: `GET`
* **Path**: `/analytics/trends`
* **Access Level**: Operator / Engineer / Admin
* **Query Parameters**:
  * `sensor_id` (Integer, Required): The target sensor channel ID.
  * `start_time` (String, Required): ISO-8601 timestamp (e.g., `2026-06-30T00:00:00Z`).
  * `end_time` (String, Required): ISO-8601 timestamp.
  * `resolution` (String, Optional): Downsampling bucket size: `1m`, `5m`, `1h`, `1d`. Default: `5m`.
* **Response (200 OK)**:

```json
{
  "sensor_id": 1,
  "resolution": "5m",
  "data_points": [
    {
      "time": "2026-06-30T13:40:00Z",
      "actual_value": 11020.5,
      "rolling_mean": 11018.2,
      "rolling_std": 12.4,
      "linear_slope": 0.45,
      "trend_class": "STABLE"
    }
  ]
}
```

---

### 4. KPI Engine Endpoints

#### 4.1 Get Latest Furnace KPIs
Fetch real-time computed performance indices.

* **HTTP Method**: `GET`
* **Path**: `/analytics/kpis`
* **Access Level**: Operator / Engineer / Admin
* **Query Parameters**:
  * `furnace_id` (Integer, Required): The target furnace ID.
* **Response (200 OK)**:

```json
{
  "furnace_id": 1,
  "timestamp": "2026-06-30T13:48:00Z",
  "kpis": {
    "peak_demand_kw": 1250.0,
    "average_load_kw": 980.4,
    "load_factor": 0.78,
    "power_factor": 0.92,
    "transformer_utilization_pct": 85.3,
    "specific_energy_consumption": 520.4,
    "daily_energy_kwh": 23520.0
  }
}
```

---

### 5. Anomaly & Alarm Endpoints

#### 5.1 Retrieve Alarms List
Queries active and acknowledged alarms.

* **HTTP Method**: `GET`
* **Path**: `/anomalies/alarms`
* **Access Level**: Operator / Engineer / Admin
* **Query Parameters**:
  * `status` (String, Optional): `ACTIVE`, `ACKNOWLEDGED`, `CLEARED`.
  * `severity` (String, Optional): `INFO`, `WARNING`, `CRITICAL`.
  * `limit` (Integer, Optional): Default: 50.
* **Response (200 OK)**:

```json
[
  {
    "alarm_id": 9812,
    "time": "2026-06-30T13:45:12Z",
    "end_time": null,
    "sensor_id": 1,
    "alarm_type": "VOLTAGE_SPIKE",
    "severity": "CRITICAL",
    "trigger_value": 12850.0,
    "status": "ACTIVE",
    "acknowledged_by": null,
    "comments": null
  }
]
```

#### 5.2 Acknowledge Active Alarm
Allows operators to log checkups and acknowledge active warnings.

* **HTTP Method**: `PUT`
* **Path**: `/anomalies/alarms/{alarm_id}/acknowledge`
* **Access Level**: Operator / Engineer / Admin
* **Payload Schema**:

```json
{
  "acknowledged_by": "kushal_engineer",
  "comments": "Checked transformer cooling system. Load stabilized."
}
```

* **Response (200 OK)**:

```json
{
  "alarm_id": 9812,
  "status": "ACKNOWLEDGED",
  "acknowledged_at": "2026-06-30T13:48:35Z",
  "acknowledged_by": "kushal_engineer"
}
```

---

### 6. ML Forecasting Endpoints

#### 6.1 Get Active Predictions
Retrieve predictive time-series arrays alongside real-time target lines.

* **HTTP Method**: `GET`
* **Path**: `/predictions/forecasts`
* **Access Level**: Engineer / Admin
* **Query Parameters**:
  * `furnace_id` (Integer, Required): The target furnace ID.
  * `target_variable` (String, Required): Target metric: `grid_kw` or `specific_energy_consumption`.
* **Response (200 OK)**:

```json
{
  "furnace_id": 1,
  "target_variable": "grid_kw",
  "generated_at": "2026-06-30T13:45:00Z",
  "forecasts": [
    {
      "time": "2026-06-30T13:50:00Z",
      "horizon_minutes": 5,
      "predicted_value": 1265.4,
      "upper_bound": 1290.1,
      "lower_bound": 1240.7
    },
    {
      "time": "2026-06-30T14:00:00Z",
      "horizon_minutes": 15,
      "predicted_value": 1282.1,
      "upper_bound": 1320.4,
      "lower_bound": 1243.8
    }
  ]
}
```

---

### 7. Automated Report Endpoints

#### 7.1 Trigger Report Generation
Manually compile operational PDF/Excel documentation.

* **HTTP Method**: `POST`
* **Path**: `/reports/generate`
* **Access Level**: Engineer / Admin
* **Payload Schema**:

```json
{
  "report_type": "WEEKLY",
  "start_date": "2026-06-22",
  "end_date": "2026-06-28",
  "format": "PDF"
}
```

* **Response (202 Accepted)**:

```json
{
  "task_id": "rep-task-98a72c1f",
  "status": "PROCESSING",
  "estimated_time_seconds": 15
}
```

---

### 8. Live WebSocket Stream (`/ws/telemetry`)

Allows the React browser frontend to open a persistent connection to receive live 1 Hz updates.

* **Protocol Connection URL**: `wss://<host>/api/v1/ws/telemetry`
* **Handshake Parameters**: HTTP headers must pass a query string containing authentication tokens:
  `wss://<host>/api/v1/ws/telemetry?token=<JWT_TOKEN>`

#### 8.1 Inbound Messages (Client to Server)
Allows subscribing/unsubscribing to specific furnace instances.

```json
{
  "action": "SUBSCRIBE",
  "furnace_id": 1
}
```

#### 8.2 Outbound Telemetry Message (Server to Client)
Sent at 1 Hz when updates are posted to the Redis channel:

```json
{
  "event": "TELEMETRY_UPDATE",
  "furnace_id": 1,
  "timestamp": "2026-06-30T13:48:02.105Z",
  "data": {
    "voltage_v": 11020.5,
    "current_a": 450.2,
    "grid_kw": 1250.0,
    "transformer_load_pct": 85.3,
    "power_factor": 0.92,
    "sms_status": true
  }
}
```
