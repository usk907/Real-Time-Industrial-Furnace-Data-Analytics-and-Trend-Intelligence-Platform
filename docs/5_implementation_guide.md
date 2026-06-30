# Implementation Guide & Reference Architecture
## Real-Time Industrial Furnace Data Analytics and Trend Prediction System Using SCADA Data

---

### 1. Project Directory Structure

```text
furnace-analytics-system/
├── start_platform.bat          # Unified Windows Local Host Launcher
├── .env
├── README.md
│
├── database/
│   └── init-db.sql              # Initial database schema setup + Hypertables
│
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entrypoint
│   │   ├── config.py            # Environment settings
│   │   ├── database.py          # SQLAlchemy connection pools
│   │   ├── models.py            # SQLAlchemy model mappings
│   │   ├── schemas.py           # Pydantic schemas (DTo validations)
│   │   ├── auth.py              # JWT tokens and hash utilities
│   │   ├── router.py            # API routing and analytics loops
│   │   └── websocket_manager.py # Real-time client session broadcaster
│   └── requirements.txt
│
├── simulator/
│   ├── scada_simulator.py       # Live telemetry simulator (1 Hz)
│   └── requirements.txt
│
└── frontend/
    ├── package.json
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── tsconfig.json
    ├── index.html
    └── src/
        ├── main.tsx
        ├── index.css
        └── App.tsx
```

---

### 2. Environment Setup

#### 2.1 Backend Setup
1. Create a Python 3.10+ virtual environment:
   ```bash
   python -m venv venv
   source venv/Scripts/activate # On Windows: venv\Scripts\activate
   ```
2. Populate `backend/requirements.txt`:
   ```text
   fastapi==0.100.0
   uvicorn[standard]==0.22.0
   asyncpg==0.28.0
   psycopg2-binary==2.9.6
   redis==5.0.0
   celery==5.3.1
   pydantic==2.0.2
   numpy==1.24.3
   pandas==2.0.3
   torch==2.0.1
   scikit-learn==1.3.0
   paho-mqtt==1.6.1
   ```

#### 2.2 Frontend Setup
1. Scaffold using Vite:
   ```bash
   npx -y create-vite-app@latest frontend --template react-ts
   ```
2. Core dependencies in `frontend/package.json`:
   ```json
   {
     "dependencies": {
       "react": "^18.2.0",
       "react-dom": "^18.2.0",
       "echarts": "^5.4.2",
       "echarts-for-react": "^3.0.2",
       "lucide-react": "^0.263.0"
     }
   }
   ```

---

### 3. Core Boilerplate Code Templates

#### 3.1 Simulated SCADA Tag Publisher (`drivers/scada_simulator.py`)
This script simulates an active furnace tag stream, injecting random voltage spikes/dips and thermal overloads to test the anomaly engines.

```python
import time
import random
import json
import math
import paho.mqtt.client as mqtt

MQTT_BROKER = "mqtt-broker"
MQTT_PORT = 1883
TOPIC = "furnace/1/telemetry"

client = mqtt.Client("SCADA_Simulator_1")
client.connect(MQTT_BROKER, MQTT_PORT, 60)

print("Starting SCADA Tag Simulator. Polling frequency: 1 Hz...")

step = 0
while True:
    step += 1
    # Base physics simulation
    voltage = 11000.0 + random.normalvariate(0, 50)
    power_factor = 0.92 + random.normalvariate(0, 0.01)
    
    # Simulate cyclical load (sine wave representing furnace heat cycle)
    base_kw = 1000.0 + 200.0 * math.sin(step / 100.0)
    grid_kw = base_kw + random.normalvariate(0, 10)
    current = (grid_kw * 1000) / (voltage * power_factor * math.sqrt(3))
    
    transformer_load = (grid_kw / 1500.0) * 100.0 # 1500 kW rated limit
    
    # Inject periodic anomalies
    # 1. Voltage Spike (Every 180 seconds)
    if step % 180 == 0:
        voltage += 2000.0
        print("[ANOMALY INJECTED]: Voltage Spike")
    # 2. Transformer Overload (Every 300 seconds)
    if step % 300 == 0:
        grid_kw += 600.0
        transformer_load = 115.0
        print("[ANOMALY INJECTED]: Transformer Overload")
        
    payload = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "furnace_id": 1,
        "voltage_v": round(voltage, 2),
        "current_a": round(current, 2),
        "grid_kw": round(grid_kw, 2),
        "transformer_load_pct": round(transformer_load, 2),
        "power_factor": round(power_factor, 3),
        "sms_status": 1 if grid_kw > 50 else 0
    }
    
    client.publish(TOPIC, json.dumps(payload))
    time.sleep(1.0)
```

#### 3.2 FastAPI WebSocket Broadcaster (`backend/main.py`)
Listens to incoming events from the SCADA publisher (via Redis or database queues) and pumps values to subscribed browsers.

```python
import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as aioredis

app = FastAPI(title="Furnace Analytics API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REDIS_URL = "redis://redis:6379"

# Connection manager for Active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                # Handle stale connections
                pass

manager = ConnectionManager()

async def redis_listener():
    """Tails Redis pub/sub channel and broadcasts live packets."""
    r = aioredis.from_url(REDIS_URL, decode_responses=True)
    pubsub = r.pubsub()
    await pubsub.subscribe("telemetry:stream")
    
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                payload = json.loads(message["data"])
                broadcast_packet = {
                    "event": "TELEMETRY_UPDATE",
                    "furnace_id": payload["furnace_id"],
                    "timestamp": payload["timestamp"],
                    "data": {
                        "voltage_v": payload["voltage_v"],
                        "current_a": payload["current_a"],
                        "grid_kw": payload["grid_kw"],
                        "transformer_load_pct": payload["transformer_load_pct"],
                        "power_factor": payload["power_factor"],
                        "sms_status": payload["sms_status"]
                    }
                }
                await manager.broadcast(json.dumps(broadcast_packet))
    except asyncio.CancelledError:
        pass
    finally:
        await pubsub.unsubscribe("telemetry:stream")

@app.on_event("startup")
async def startup_event():
    # Start Redis background listener
    asyncio.create_task(redis_listener())

@app.websocket("/api/v1/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; accept inbound messages
            data = await websocket.receive_text()
            # Handle client-specific requests (e.g. subscribe to specific ID)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

#### 3.3 PyTorch Forecasting Network (`backend/ml/model.py`)
An LSTM model class designed to read sequential furnace patterns and predict loads at multiple steps ahead.

```python
import torch
import torch.nn as nn

class FurnaceLoadLSTM(nn.Module):
    def __init__(self, input_dim=6, hidden_dim=64, num_layers=2, output_dim=5):
        """
        input_dim: Number of input features (Voltage, Current, Load, PF, load_avg, hour_sine)
        hidden_dim: Dimension of LSTM cells
        num_layers: Depth of recurrent network
        output_dim: 5 target predictions (5m, 15m, 30m, 1h, 24h forecasts)
        """
        super(FurnaceLoadLSTM, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.2 if num_layers > 1 else 0.0
        )
        
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        # Input tensor structure: (batch_size, sequence_length, input_dim)
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).to(x.device)
        
        # LSTM forward pass
        out, _ = self.lstm(x, (h0, c0))
        
        # Decode the hidden state of the last time step
        out = self.fc(out[:, -1, :])
        return out
```

### 4. Local Orchestration Setup (`start_platform.bat`)

The platform is configured to run fully on a local Windows host. The following unified batch script starts the FastAPI Backend, the SCADA Simulator, and the React frontend inside three separate Command Prompt windows:

```cmd
@echo off
title SCADA Furnace Data Analytics and Trend Intelligence Platform Launcher
echo =========================================================================
echo  SCADA Furnace Analytics Platform Local Host Launcher (Dockerless)
echo =========================================================================
echo.

:: 1. Launch FastAPI Backend
echo [1/3] Spinning up FastAPI Backend in a separate window...
start "FastAPI Backend Server" cmd /k "cd backend && (if not exist venv (echo Creating virtualenv... && python -m venv venv)) && call venv\Scripts\activate && echo Installing dependencies... && pip install -r requirements.txt && echo Launching FastAPI on port 8000... && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

:: 2. Launch SCADA Simulator
echo [2/3] Spinning up SCADA Telemetry Simulator in a separate window...
start "SCADA Telemetry Simulator" cmd /k "cd simulator && (if not exist venv (echo Creating virtualenv... && python -m venv venv)) && call venv\Scripts\activate && echo Installing dependencies... && pip install -r requirements.txt && echo Launching SCADA telemetry loop (1 Hz)... && python scada_simulator.py"

:: 3. Launch React Frontend
echo [3/3] Spinning up Vite React Dev Server in a separate window...
start "React Dashboard Frontend" cmd /k "cd frontend && (if not exist node_modules (echo Installing Node packages... && npm install)) && echo Launching Vite local server on port 3000... && npm run dev -- --port 3000"

echo.
echo =========================================================================
echo  Startup triggers completed!
echo  - Backend: http://127.0.0.1:8000
echo  - Frontend Dashboard: http://localhost:3000
echo  Please ensure your local PostgreSQL database is running on port 5432.
echo =========================================================================
pause
```
