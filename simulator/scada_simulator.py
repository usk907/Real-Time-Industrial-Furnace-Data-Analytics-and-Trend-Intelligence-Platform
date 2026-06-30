import time
import random
import requests
import os

# Ingestion target configurations
BACKEND_HOST = os.getenv("BACKEND_HOST", "localhost")
BACKEND_PORT = os.getenv("BACKEND_PORT", "8000")
API_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}/api/readings/bulk"

# Exact list of 50 sensors seeded in the database
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
    {"id": 50, "name": "Grid Export kVah", "unit": "kVah", "base": 148800.0}
]

# Keep track of active values for simulation variations
current_values = {s["id"]: s["base"] for s in SENSORS_METADATA}

# Increments accumulators based on current power load (kW * (1s / 3600s))
def update_consumption_accumulators():
    # Grid Import kWh increments trailing the circuit breaker loads (CB5214 + CB14)
    cb_power = current_values[1] + current_values[2]
    increment_kwh = cb_power * (1.0 / 3600.0)
    
    current_values[45] += increment_kwh # Import kWh
    current_values[46] += (increment_kwh / 0.929) # Import kVah (assuming PF = 0.929)
    
    # Grid Export kWh increments trailing Turbine Generator output (TG-2 + TG-3)
    tg_power = current_values[41] + current_values[42]
    export_increment = tg_power * (1.0 / 3600.0)
    
    current_values[49] += export_increment # Export kWh
    current_values[50] += (export_increment / 0.94) # Export kVah

def main_loop():
    tick = 0
    print(f"Simulator starting. Posting to: {API_URL}")
    
    while True:
        tick += 1
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
        
        # 1. Fluctuating Turbine Generators
        # TG-2 (30MW limit) & TG-3 (33MW limit) run at high capacities
        current_values[41] = 29200.0 + random.normalvariate(0, 50)  # TG-2
        current_values[42] = 32500.0 + random.normalvariate(0, 80)  # TG-3
        
        # 2. Fluctuating Breaker Loads (CB5214 & CB14)
        current_values[1] = 22860.0 + random.normalvariate(0, 100) # CB5214
        current_values[2] = 19888.0 + random.normalvariate(0, 80)  # CB14
        current_values[3] = 11939.0 + random.normalvariate(0, 50)  # CB52G4
        
        # 3. SMS-4 Furnace loads (Furnace 1 to 4)
        current_values[25] = 6573.0 + random.normalvariate(0, 30)  # Fur-1 kW
        current_values[29] = 4662.0 + random.normalvariate(0, 40)  # Fur-2 kW
        current_values[33] = 7586.0 + random.normalvariate(0, 20)  # Fur-3 kW
        current_values[37] = 7342.0 + random.normalvariate(0, 35)  # Fur-4 kW
        
        # Dynamic recalculation of SMS running power sum
        sms_4_run = current_values[25] + current_values[29] + current_values[33] + current_values[37]
        current_values[22] = sms_4_run
        
        # SMS-4 Utl. Factor (%) = (Run Power / Avl Power) * 100
        current_values[23] = (sms_4_run / current_values[21]) * 100.0
        
        # SMS-1 Run. Power averages around 51,135 kW
        current_values[19] = 51135.0 + random.normalvariate(0, 150)
        
        # Total SMS running power = SMS-1 + SMS-4 running power
        current_values[7] = current_values[19] + current_values[22]
        
        # 4. Increment accumulators
        update_consumption_accumulators()
        
        # -------------------------------------------------------------
        # Periodical Anomaly Injections
        # -------------------------------------------------------------
        # Voltage/Current spikes mocked on Turbine loads
        injected_msg = None
        if tick % 150 == 0:
            current_values[41] = 34500.0  # TG-2 Overload spike
            injected_msg = "Overload Spike on TG-2 Turbine"
        elif tick % 200 == 0:
            current_values[1] = 48000.0   # Circuit Breaker surge
            injected_msg = "Current Surge on Breaker CB5214"
            
        if injected_msg:
            print(f"[ANOMALY INJECTED]: {injected_msg}")
            
        # Compile payload
        payload = []
        for sensor in SENSORS_METADATA:
            s_id = sensor["id"]
            val = current_values[s_id]
            
            # Simple threshold check
            status = "OK"
            if s_id in [1, 2] and val > 45000.0:
                status = "HIGH_LIMIT"
            elif s_id == 41 and val > 30000.0:
                status = "HIGH_LIMIT"
            elif s_id == 42 and val > 33000.0:
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
            
        # Post to API backend
        try:
            r = requests.post(API_URL, json=payload, timeout=2.0)
            if r.status_code in [200, 201]:
                print(f"[{timestamp}] Successfully posted {len(payload)} SCADA signals. API: {r.status_code}")
            else:
                print(f"[{timestamp}] Ingestion Error. API Status: {r.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"[{timestamp}] Backend unreachable at {API_URL}: {e}")
            
        time.sleep(1.0)

if __name__ == "__main__":
    time.sleep(2.0)  # Wait for backend initialization
    main_loop()
