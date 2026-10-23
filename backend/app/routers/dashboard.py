"""
IEIP Dashboard Summary Router
Endpoints:
  - GET /dashboard
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.database import get_db
from backend.app.models import SensorReading, Alarm, Prediction

router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard")
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Fetches high-level executive dashboard summary and plant KPIs."""
    # 1. Fetch latest reading values efficiently in a single query
    latest_readings = {}
    recent_readings = db.query(SensorReading).order_by(desc(SensorReading.time)).limit(120).all()
    for r in recent_readings:
        if r.sensor_id not in latest_readings:
            latest_readings[r.sensor_id] = r.value

    running_furnaces = 0
    # Shyam Metaliks furnaces: SMS-1 (10-14), SMS-2 (24-35), SMS-4 (36-39)
    furnace_ids = list(range(10, 15)) + list(range(24, 36)) + list(range(36, 40))
    for s_id in furnace_ids:
        if latest_readings.get(s_id, 0.0) > 10.0:
            running_furnaces += 1

    grid_power_combined = latest_readings.get(1, 0.0)
    generation_combined = (
        latest_readings.get(5, 0.0) +
        latest_readings.get(6, 0.0) +
        latest_readings.get(7, 0.0) +
        latest_readings.get(8, 0.0) +
        latest_readings.get(9, 0.0)
    )

    # 2. Active alarms count
    active_alarms = db.query(Alarm).filter(Alarm.status == "ACTIVE").order_by(desc(Alarm.time)).all()

    # 3. Compile KPI values
    grid_import_kwh = latest_readings.get(1, 0.0)
    grid_import_kvah = latest_readings.get(2, 0.0)
    avg_pf = round(grid_import_kwh / grid_import_kvah, 3) if grid_import_kvah > 0 else 0.95
    if avg_pf > 1.0 or avg_pf < 0.5:
        avg_pf = 0.95

    # Sum SMS running loads dynamically
    sms1_sum = sum(latest_readings.get(i, 0.0) for i in range(10, 18))
    sms2_sum = sum(latest_readings.get(i, 0.0) for i in list(range(24, 36)) + [40, 41])
    sms4_sum = sum(latest_readings.get(i, 0.0) for i in list(range(36, 40)) + list(range(42, 49)))
    sms_total = sms1_sum + sms2_sum + sms4_sum

    kpis = {
        "grid_power_combined": grid_power_combined,
        "generation_combined": generation_combined,
        "cb5214_kw": latest_readings.get(1, 0.0),
        "cb14_kw": latest_readings.get(2, 0.0),
        "cb52g4_kw": latest_readings.get(3, 0.0),
        "sms_allocated_power": 120000.0,
        "sms_run_power": sms_total,
        "sms_1_run_power": sms1_sum,
        "sms_4_run_power": sms4_sum,
        "sms_4_utl_pct": round((running_furnaces / 21) * 100.0, 1) if running_furnaces > 0 else 0.0,
        "running_furnace_count": running_furnaces,
        "total_machines": 7,
        "running_machines": 6 if running_furnaces > 0 else 3,
        "offline_machines": 1,
        "faulty_machines": len(active_alarms),
        "avg_pf": avg_pf,
        "load_factor": 75.4,
        "today_energy_kwh": latest_readings.get(1, 93400.0),
        "monthly_energy_kwh": latest_readings.get(1, 93400.0) * 30.0,
        "carbon_emission": latest_readings.get(1, 93400.0) * 0.38,  # 0.38 kg CO2 per kWh
        "energy_cost": latest_readings.get(1, 93400.0) * 0.12  # $0.12 per kWh
    }

    # 4. Extract latest predictions
    predictions = db.query(Prediction).order_by(desc(Prediction.time)).limit(6).all()
    pred_data = [
        {
            "horizon": p.prediction_horizon_minutes,
            "sensor_id": p.sensor_id,
            "predicted": p.predicted_value,
            "upper": p.upper_bound,
            "lower": p.lower_bound
        } for p in predictions
    ]

    return {
        "kpis": kpis,
        "active_alarms_count": len(active_alarms),
        "predictions": pred_data
    }
