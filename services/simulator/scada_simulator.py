import time
import random
import requests
import os
import math

# Ingestion target configurations (TAP Server on Port 8001 with Backend 8000 fallback)
TAP_HOST = os.getenv("TAP_HOST", "127.0.0.1")
TAP_PORT = os.getenv("TAP_PORT", "8001")
TAP_URL = os.getenv("TAP_SERVER_URL", f"http://{TAP_HOST}:{TAP_PORT}/tap/telemetry")
BACKEND_FALLBACK_URL = f"http://{TAP_HOST}:8000/api/readings/bulk"
API_URL = TAP_URL

# Exact list of 60 devices seeded in the database
SENSORS_METADATA = [
    # Grid & Distribution (1 - 16)
    {"id": 1, "name": "CB5214 kW", "unit": "kW", "base": 22860.0},
    {"id": 2, "name": "CB14 kW", "unit": "kW", "base": 19888.0},
    {"id": 3, "name": "CB52G4 kW", "unit": "kW", "base": 11939.0},
    {"id": 4, "name": "CB52G14 kW", "unit": "kW", "base": 0.0},
    {"id": 5, "name": "CB52G24 kW", "unit": "kW", "base": 0.0},
    {"id": 6, "name": "SMS Allocated Power", "unit": "kW", "base": 100000.0},
    {"id": 7, "name": "SMS Run. Power", "unit": "kW", "base": 77356.0},
    {"id": 8, "name": "SMS-1 PR", "unit": "", "base": 1.0},
    {"id": 9, "name": "SMS-2 PR", "unit": "", "base": 0.0},
    {"id": 10, "name": "SMS-4 PR", "unit": "", "base": 2.0},
    {"id": 11, "name": "SMS-1 Max Set", "unit": "kW", "base": 70000.0},
    {"id": 12, "name": "SMS-1 Min Set", "unit": "kW", "base": 36000.0},
    {"id": 13, "name": "SMS-2 Max Set", "unit": "kW", "base": 0.0},
    {"id": 14, "name": "SMS-2 Min Set", "unit": "kW", "base": 0.0},
    {"id": 15, "name": "SMS-4 Max Set", "unit": "kW", "base": 30000.0},
    {"id": 16, "name": "SMS-4 Min Set", "unit": "kW", "base": 18000.0},
    
    # SMS-1 Furnace Details (17 - 19)
    {"id": 17, "name": "SMS-1 Max Set", "unit": "kW", "base": 70000.0},
    {"id": 18, "name": "SMS-1 Avl. Power", "unit": "kW", "base": 70000.0},
    {"id": 19, "name": "SMS-1 Run. Power", "unit": "kW", "base": 51135.0},
    
    # SMS-4 Furnace Details (20 - 39)
    {"id": 20, "name": "SMS-4 Max Set", "unit": "kW", "base": 30000.0},
    {"id": 21, "name": "SMS-4 Avl. Power", "unit": "kW", "base": 30000.0},
    {"id": 22, "name": "SMS-4 Run. Power", "unit": "kW", "base": 26163.0},
    {"id": 23, "name": "SMS-4 Utl. Factor(%)", "unit": "%", "base": 87.21},
    {"id": 24, "name": "SMS-4 Fur-1 SP", "unit": "kW", "base": 8300.0},
    {"id": 25, "name": "SMS-4 Fur-1 kW", "unit": "kW", "base": 6573.0},
    {"id": 26, "name": "SMS-4 Fur-1 PP%", "unit": "%", "base": 100.0},
    {"id": 27, "name": "SMS-4 Fur-1 PR", "unit": "", "base": 1.0},
    {"id": 28, "name": "SMS-4 Fur-2 SP", "unit": "kW", "base": 8300.0},
    {"id": 29, "name": "SMS-4 Fur-2 kW", "unit": "kW", "base": 4662.0},
    {"id": 30, "name": "SMS-4 Fur-2 PP%", "unit": "%", "base": 100.0},
    {"id": 31, "name": "SMS-4 Fur-2 PR", "unit": "", "base": 2.0},
    {"id": 32, "name": "SMS-4 Fur-3 SP", "unit": "kW", "base": 8300.0},
    {"id": 33, "name": "SMS-4 Fur-3 kW", "unit": "kW", "base": 7586.0},
    {"id": 34, "name": "SMS-4 Fur-3 PP%", "unit": "%", "base": 45.519},
    {"id": 35, "name": "SMS-4 Fur-3 PR", "unit": "", "base": 3.0},
    {"id": 36, "name": "SMS-4 Fur-4 SP", "unit": "kW", "base": 8300.0},
    {"id": 37, "name": "SMS-4 Fur-4 kW", "unit": "kW", "base": 7342.0},
    {"id": 38, "name": "SMS-4 Fur-4 PP%", "unit": "%", "base": 72.591},
    {"id": 39, "name": "SMS-4 Fur-4 PR", "unit": "", "base": 4.0},
    
    # Turbine Generators (40 - 44)
    {"id": 40, "name": "30MW TG-1 kW", "unit": "kW", "base": 0.0},
    {"id": 41, "name": "30MW TG-2 kW", "unit": "kW", "base": 29200.0},
    {"id": 42, "name": "33MW TG-3 kW", "unit": "kW", "base": 32500.0},
    {"id": 43, "name": "30MW TG-4 kW", "unit": "kW", "base": 0.0},
    {"id": 44, "name": "40MW TG-5 kW", "unit": "kW", "base": 0.0},
    
    # Consumption Accumulations (45 - 50)
    {"id": 45, "name": "Grid Import kWh", "unit": "kWh", "base": 93400.0},
    {"id": 46, "name": "Grid Import kVah", "unit": "kVah", "base": 100564.0},
    {"id": 47, "name": "Avg. P.F.", "unit": "", "base": 0.929},
    {"id": 48, "name": "Load Factor", "unit": "", "base": 23.279},
    {"id": 49, "name": "Grid Export kWh", "unit": "kWh", "base": 130136.0},
    {"id": 50, "name": "Grid Export kVah", "unit": "kVah", "base": 148800.0},

    # Physical Analytics Sensors (51 - 60)
    {"id": 51, "name": "SMS-1 Furnace Temp", "unit": "°C", "base": 1520.0},
    {"id": 52, "name": "SMS-1 Furnace Pressure", "unit": "bar", "base": 1.2},
    {"id": 53, "name": "SMS-1 Cooling Water Flow", "unit": "m³/h", "base": 250.0},
    {"id": 54, "name": "TG-2 Turbine RPM", "unit": "RPM", "base": 3000.0},
    {"id": 55, "name": "CB5214 Voltage", "unit": "V", "base": 11000.0},
    {"id": 56, "name": "CB5214 Current", "unit": "A", "base": 240.0},
    {"id": 57, "name": "SMS Ambient Humidity", "unit": "%", "base": 55.0},
    {"id": 58, "name": "SMS Carbon Dioxide (CO2)", "unit": "ppm", "base": 400.0},
    {"id": 59, "name": "SMS-1 Production Count", "unit": "heats", "base": 12.0},
    {"id": 60, "name": "SMS-4 Gas Level (CO)", "unit": "ppm", "base": 15.0}
]

# Keep track of active values for simulation variations
current_values = {s["id"]: s["base"] for s in SENSORS_METADATA}

def update_consumption_accumulators():
    cb_power = current_values[1] + current_values[2]
    increment_kwh = cb_power * (1.0 / 3600.0)
    
    current_values[45] += increment_kwh
    current_values[46] += (increment_kwh / 0.929)
    
    tg_power = current_values[41] + current_values[42]
    export_increment = tg_power * (1.0 / 3600.0)
    
    current_values[49] += export_increment
    current_values[50] += (export_increment / 0.94)

def main_loop():
    tick = 0
    print(f"SCADA Simulator starting. Target API: {API_URL}")
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=5, pool_maxsize=5, max_retries=1)
    session.mount("http://", adapter)
    
    while True:
        tick += 1
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
        
        # 1. Apply baseline random fluctuation to all sensors to simulate background noise and prevent frozen alarms
        for sensor in SENSORS_METADATA:
            s_id = sensor["id"]
            base = sensor["base"]
            # Generate a subtle random walk/variation from base
            if base == 0.0:
                if s_id in [4, 5, 13, 14, 40, 43, 44]:
                    # standby loads instead of flat zero
                    current_values[s_id] = round(abs(random.normalvariate(200.0, 15.0)), 2)
                elif s_id == 9:
                    # state change
                    current_values[s_id] = float(random.choice([0, 1]))
                else:
                    current_values[s_id] = round(abs(random.normalvariate(0.5, 0.05)), 3)
            else:
                # Add small noise (0.2% - 1%)
                noise = random.normalvariate(0, max(base * 0.003, 0.05))
                current_values[s_id] = round(base + noise, 3)

        # 2. Physics Engine Overrides
        # Turbines (Power, RPM)
        current_values[41] = round(29200.0 + random.normalvariate(0, 50), 3)  # TG-2 kW
        current_values[42] = round(32500.0 + random.normalvariate(0, 80), 3)  # TG-3 kW
        current_values[54] = round(3000.0 + random.normalvariate(0, 15), 1)   # TG-2 RPM
        
        # Breakers (Power, Voltage, Current)
        current_values[1] = round(22860.0 + random.normalvariate(0, 100), 3) # CB5214 kW
        current_values[2] = round(19888.0 + random.normalvariate(0, 80), 3)  # CB14 kW
        current_values[3] = round(11939.0 + random.normalvariate(0, 50), 3)  # CB52G4 kW
        
        # CB5214 Voltage floats around 11,000 V
        current_values[55] = round(11000.0 + random.normalvariate(0, 35), 2)
        # Current calculated from Power & Voltage (I = P / (V * sqrt(3) * PF))
        power_factor = 0.929
        current_values[56] = round((current_values[1] * 1000.0) / (current_values[55] * math.sqrt(3.0) * power_factor), 2)
        
        # SMS-4 Furnace loads
        current_values[25] = round(6573.0 + random.normalvariate(0, 30), 3)  # Fur-1 kW
        current_values[29] = round(4662.0 + random.normalvariate(0, 40), 3)  # Fur-2 kW
        current_values[33] = round(7586.0 + random.normalvariate(0, 20), 3)  # Fur-3 kW
        current_values[37] = round(7342.0 + random.normalvariate(0, 35), 3)  # Fur-4 kW
        
        sms_4_run = current_values[25] + current_values[29] + current_values[33] + current_values[37]
        current_values[22] = round(sms_4_run, 3)
        current_values[23] = round((sms_4_run / current_values[21]) * 100.0, 3)
        current_values[60] = round(15.0 + random.normalvariate(0, 1.2), 2)   # SMS-4 CO Gas Level
        
        # SMS-1 Furnace details
        current_values[19] = round(51135.0 + random.normalvariate(0, 150), 3)
        current_values[7] = round(current_values[19] + current_values[22], 3) # Total SMS Running Power
        
        # SMS-1 Physical Indicators (Temperature, Pressure, Flow, CO2)
        cycle_angle = (tick % 360) * (math.pi / 180.0)
        current_values[51] = round(1550.0 + 80.0 * math.sin(cycle_angle) + random.normalvariate(0, 5.0), 1)
        current_values[52] = round(1.25 + 0.15 * math.sin(cycle_angle) + random.normalvariate(0, 0.02), 3)
        current_values[53] = round(250.0 + random.normalvariate(0, 2.0), 2)
        current_values[57] = round(55.0 + 3.0 * math.sin(cycle_angle / 10.0) + random.normalvariate(0, 0.5), 1) # Humidity
        current_values[58] = round(420.0 + 40.0 * math.sin(cycle_angle) + random.normalvariate(0, 10.0), 1) # CO2
        
        # Production Count increments slowly (every 300 ticks / heats)
        if tick % 300 == 0:
            current_values[59] += 1
            print(f"[PRODUCTION]: SMS-1 completed a new heat batch! Total heats: {int(current_values[59])}")
        
        # 4. Increment accumulators
        update_consumption_accumulators()
        
        # 5. Periodical Anomaly Injections
        injected_msg = None
        if tick % 180 == 0:
            # Turbine TG-2 Overload Spike
            current_values[41] = 34500.0  
            current_values[54] = 4100.0   # Speed surge
            injected_msg = "Overload Surge on TG-2 Turbine & RPM"
        elif tick % 240 == 0:
            # Circuit Breaker load surge
            current_values[1] = 48500.0
            injected_msg = "Current / Power Surge on Circuit Breaker CB5214"
        elif tick % 320 == 0:
            # Temperature spike warning (EAF overheating)
            current_values[51] = 1750.0
            injected_msg = "Critical Temperature Warning on SMS-1 furnace (>1700°C)"
            
        if injected_msg:
            print(f"[ANOMALY INJECTED]: {injected_msg}")
            
        # Compile payload list
        payload = []
        for sensor in SENSORS_METADATA:
            s_id = sensor["id"]
            val = current_values[s_id]
            
            # Simple threshold flags for simulator output logs
            status = "OK"
            if s_id in [1, 2] and val > 45000.0:
                status = "HIGH_LIMIT"
            elif s_id == 41 and val > 30000.0:
                status = "HIGH_LIMIT"
            elif s_id == 42 and val > 33000.0:
                status = "HIGH_LIMIT"
            elif s_id == 51 and val > 1700.0:
                status = "HIGH_LIMIT"
                
            payload.append({
                "timestamp": timestamp,
                "sensor_id": s_id,
                "sensor_name": sensor["name"],
                "plant": "Gary Steel Works",
                "unit": sensor["unit"],
                "value": round(val, 3),
                "quality": "GOOD",
                "status": status
            })
            
        # Stream to TAP Ingestion Server (:8001) for fast SQL writes
        try:
            session.post(TAP_URL, json=payload, timeout=1.0)
        except Exception:
            pass

        # Stream to Backend (:8000) for real-time WebSocket broadcast & live alarms
        try:
            r = session.post(BACKEND_FALLBACK_URL, json=payload, timeout=1.0)
            if r.status_code in [200, 201] and tick % 5 == 0:
                print(f"[{timestamp}] Streamed {len(payload)} SCADA signals to TAP (:8001) & Backend (:8000).")
        except Exception as e:
            if tick % 5 == 0:
                print(f"[{timestamp}] Backend sync: {e}")

if __name__ == "__main__":
    time.sleep(5.0)  # Wait for backend and database setup in Docker Compose
    main_loop()
