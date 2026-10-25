import os
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime, timezone
from typing import List, Dict, Any

class InfluxDBManager:
    def __init__(self):
        self.url = os.getenv("INFLUXDB_URL", "http://localhost:8086")
        self.token = os.getenv("INFLUXDB_TOKEN", "my-super-secret-admin-token-1234567890")
        self.org = os.getenv("INFLUXDB_ORG", "ieip_org")
        self.bucket = os.getenv("INFLUXDB_BUCKET", "furnace_telemetry")
        
        self.client = None
        self.write_api = None
        self.query_api = None
        
        if self.url:
            try:
                # Set a low timeout (1.5 seconds) for the initial health check
                self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org, timeout=1500)
                health = self.client.health()
                if health.status == "pass":
                    self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
                    self.query_api = self.client.query_api()
                    print(f"[INFLUXDB]: Connected successfully to {self.url} (Org: {self.org}, Bucket: {self.bucket})")
                else:
                    print(f"[INFLUXDB WARNING]: Service status check failed. Running in SQLite-only telemetry fallback.")
                    self.client = None
            except Exception as e:
                print(f"[INFLUXDB WARNING]: Client connection failed (offline): {e}")
                print("[INFLUXDB]: Running in SQLite-only telemetry fallback.")
                self.client = None

    def write_readings(self, readings: List[Dict[str, Any]]):
        """Bulk writes a list of SCADA telemetry readings to InfluxDB in a single batch."""
        if not self.write_api:
            return
        try:
            points = []
            for r in readings:
                ts = r.get("timestamp")
                if isinstance(ts, str):
                    try:
                        # Parse ISO string
                        ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    except Exception:
                        ts = datetime.now(timezone.utc)
                if not ts:
                    ts = datetime.now(timezone.utc)
                    
                point = Point("telemetry") \
                    .tag("sensor_id", str(r["sensor_id"])) \
                    .tag("sensor_name", r["sensor_name"]) \
                    .tag("plant", r.get("plant", "Gary Steel Works")) \
                    .field("value", float(r["value"])) \
                    .field("quality", r.get("quality", "GOOD")) \
                    .field("status", r.get("status", "OK")) \
                    .time(ts, WritePrecision.NS)
                points.append(point)
            
            self.write_api.write(bucket=self.bucket, org=self.org, record=points)
        except Exception as e:
            # Silence connection drop printouts
            pass

    def query_readings(self, sensor_id: int, start_time: datetime, end_time: datetime, resolution: str = "1m") -> List[Dict[str, Any]]:
        if not self.query_api:
            return []
        
        start_str = start_time.isoformat()
        end_str = end_time.isoformat()
        
        query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: {start_str}, stop: {end_str})
          |> filter(fn: (r) => r["_measurement"] == "telemetry")
          |> filter(fn: (r) => r["sensor_id"] == "{sensor_id}")
          |> filter(fn: (r) => r["_field"] == "value")
          |> aggregateWindow(every: {resolution}, fn: mean, createEmpty: false)
          |> yield(name: "mean")
        '''
        
        try:
            result = self.query_api.query(org=self.org, query=query)
            data = []
            for table in result:
                for record in table.records:
                    data.append({
                        "time": record.get_time(),
                        "sensor_id": int(record.values.get("sensor_id")),
                        "value": record.get_value()
                    })
            return data
        except Exception as e:
            print(f"[INFLUXDB ERROR]: Query execution failed: {e}")
            return []

    def close(self):
        if self.client:
            self.client.close()

influx_manager = InfluxDBManager()
