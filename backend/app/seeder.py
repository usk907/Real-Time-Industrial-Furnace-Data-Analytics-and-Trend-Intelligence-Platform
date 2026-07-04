from sqlalchemy.orm import Session
from backend.app.database import engine, Base
from backend.app.models import Role, User, Plant, Department, Machine, Device, SystemSetting, SensorReading, Alarm, Event, Prediction, KPIHistory, Report, AuditLog, Notification

# Array of devices configuration matching init-db.sql
DEVICES_CONFIG = [
    # Grid & Distribution (1 - 16, machine_id = 1)
    {"id": 1, "machine_id": 1, "name": "CB5214 kW", "type": "POWER", "register_address": "30001", "unit": "kW", "min": 0.0, "max": 50000.0, "sn": "SN-CB5214"},
    {"id": 2, "machine_id": 1, "name": "CB14 kW", "type": "POWER", "register_address": "30002", "unit": "kW", "min": 0.0, "max": 50000.0, "sn": "SN-CB14"},
    {"id": 3, "machine_id": 1, "name": "CB52G4 kW", "type": "POWER", "register_address": "30003", "unit": "kW", "min": 0.0, "max": 30000.0, "sn": "SN-CB52G4"},
    {"id": 4, "machine_id": 1, "name": "CB52G14 kW", "type": "POWER", "register_address": "30004", "unit": "kW", "min": 0.0, "max": 30000.0, "sn": "SN-CB52G14"},
    {"id": 5, "machine_id": 1, "name": "CB52G24 kW", "type": "POWER", "register_address": "30005", "unit": "kW", "min": 0.0, "max": 30000.0, "sn": "SN-CB52G24"},
    {"id": 6, "machine_id": 1, "name": "SMS Allocated Power", "type": "POWER", "register_address": "30006", "unit": "kW", "min": 0.0, "max": 150000.0, "sn": "SN-SMS-AL"},
    {"id": 7, "machine_id": 1, "name": "SMS Run. Power", "type": "POWER", "register_address": "30007", "unit": "kW", "min": 0.0, "max": 150000.0, "sn": "SN-SMS-RN"},
    {"id": 8, "machine_id": 1, "name": "SMS-1 PR", "type": "SETPOINT", "register_address": "30008", "unit": "", "min": 0.0, "max": 5.0, "sn": "SN-SMS1PR"},
    {"id": 9, "machine_id": 1, "name": "SMS-2 PR", "type": "SETPOINT", "register_address": "30009", "unit": "", "min": 0.0, "max": 5.0, "sn": "SN-SMS2PR"},
    {"id": 10, "machine_id": 1, "name": "SMS-4 PR", "type": "SETPOINT", "register_address": "30010", "unit": "", "min": 0.0, "max": 5.0, "sn": "SN-SMS4PR"},
    {"id": 11, "machine_id": 1, "name": "SMS-1 Max Set", "type": "SETPOINT", "register_address": "30011", "unit": "kW", "min": 0.0, "max": 100000.0, "sn": "SN-SMS1MAX"},
    {"id": 12, "machine_id": 1, "name": "SMS-1 Min Set", "type": "SETPOINT", "register_address": "30012", "unit": "kW", "min": 0.0, "max": 50000.0, "sn": "SN-SMS1MIN"},
    {"id": 13, "machine_id": 1, "name": "SMS-2 Max Set", "type": "SETPOINT", "register_address": "30013", "unit": "kW", "min": 0.0, "max": 100000.0, "sn": "SN-SMS2MAX"},
    {"id": 14, "machine_id": 1, "name": "SMS-2 Min Set", "type": "SETPOINT", "register_address": "30014", "unit": "kW", "min": 0.0, "max": 50000.0, "sn": "SN-SMS2MIN"},
    {"id": 15, "machine_id": 1, "name": "SMS-4 Max Set", "type": "SETPOINT", "register_address": "30015", "unit": "kW", "min": 0.0, "max": 100000.0, "sn": "SN-SMS4MAX"},
    {"id": 16, "machine_id": 1, "name": "SMS-4 Min Set", "type": "SETPOINT", "register_address": "30016", "unit": "kW", "min": 0.0, "max": 50000.0, "sn": "SN-SMS4MIN"},

    # SMS-1 Furnace Parameters (17 - 19, machine_id = 2)
    {"id": 17, "machine_id": 2, "name": "SMS-1 Max Set", "type": "SETPOINT", "register_address": "31001", "unit": "kW", "min": 0.0, "max": 100000.0, "sn": "SN-SMS1F-MAX"},
    {"id": 18, "machine_id": 2, "name": "SMS-1 Avl. Power", "type": "POWER", "register_address": "31002", "unit": "kW", "min": 0.0, "max": 100000.0, "sn": "SN-SMS1F-AVL"},
    {"id": 19, "machine_id": 2, "name": "SMS-1 Run. Power", "type": "POWER", "register_address": "31003", "unit": "kW", "min": 0.0, "max": 100000.0, "sn": "SN-SMS1F-RUN"},

    # SMS-4 Furnace Details (20 - 39, machine_id = 4)
    {"id": 20, "machine_id": 4, "name": "SMS-4 Max Set", "type": "SETPOINT", "register_address": "32001", "unit": "kW", "min": 0.0, "max": 50000.0, "sn": "SN-SMS4-MAX"},
    {"id": 21, "machine_id": 4, "name": "SMS-4 Avl. Power", "type": "POWER", "register_address": "32002", "unit": "kW", "min": 0.0, "max": 50000.0, "sn": "SN-SMS4-AVL"},
    {"id": 22, "machine_id": 4, "name": "SMS-4 Run. Power", "type": "POWER", "register_address": "32003", "unit": "kW", "min": 0.0, "max": 50000.0, "sn": "SN-SMS4-RUN"},
    {"id": 23, "machine_id": 4, "name": "SMS-4 Utl. Factor(%)", "type": "KPI", "register_address": "32004", "unit": "%", "min": 0.0, "max": 100.0, "sn": "SN-SMS4-UTL"},
    {"id": 24, "machine_id": 4, "name": "SMS-4 Fur-1 SP", "type": "SETPOINT", "register_address": "32005", "unit": "kW", "min": 0.0, "max": 10000.0, "sn": "SN-SMS4-F1SP"},
    {"id": 25, "machine_id": 4, "name": "SMS-4 Fur-1 kW", "type": "POWER", "register_address": "32006", "unit": "kW", "min": 0.0, "max": 10000.0, "sn": "SN-SMS4-F1KW"},
    {"id": 26, "machine_id": 4, "name": "SMS-4 Fur-1 PP%", "type": "POWER", "register_address": "32007", "unit": "%", "min": 0.0, "max": 100.0, "sn": "SN-SMS4-F1PP"},
    {"id": 27, "machine_id": 4, "name": "SMS-4 Fur-1 PR", "type": "SETPOINT", "register_address": "32008", "unit": "", "min": 1.0, "max": 4.0, "sn": "SN-SMS4-F1PR"},
    {"id": 28, "machine_id": 4, "name": "SMS-4 Fur-2 SP", "type": "SETPOINT", "register_address": "32009", "unit": "kW", "min": 0.0, "max": 10000.0, "sn": "SN-SMS4-F2SP"},
    {"id": 29, "machine_id": 4, "name": "SMS-4 Fur-2 kW", "type": "POWER", "register_address": "32010", "unit": "kW", "min": 0.0, "max": 10000.0, "sn": "SN-SMS4-F2KW"},
    {"id": 30, "machine_id": 4, "name": "SMS-4 Fur-2 PP%", "type": "POWER", "register_address": "32011", "unit": "%", "min": 0.0, "max": 100.0, "sn": "SN-SMS4-F2PP"},
    {"id": 31, "machine_id": 4, "name": "SMS-4 Fur-2 PR", "type": "SETPOINT", "register_address": "32012", "unit": "", "min": 1.0, "max": 4.0, "sn": "SN-SMS4-F2PR"},
    {"id": 32, "machine_id": 4, "name": "SMS-4 Fur-3 SP", "type": "SETPOINT", "register_address": "32013", "unit": "kW", "min": 0.0, "max": 10000.0, "sn": "SN-SMS4-F3SP"},
    {"id": 33, "machine_id": 4, "name": "SMS-4 Fur-3 kW", "type": "POWER", "register_address": "32014", "unit": "kW", "min": 0.0, "max": 10000.0, "sn": "SN-SMS4-F3KW"},
    {"id": 34, "machine_id": 4, "name": "SMS-4 Fur-3 PP%", "type": "POWER", "register_address": "32015", "unit": "%", "min": 0.0, "max": 100.0, "sn": "SN-SMS4-F3PP"},
    {"id": 35, "machine_id": 4, "name": "SMS-4 Fur-3 PR", "type": "SETPOINT", "register_address": "32016", "unit": "", "min": 1.0, "max": 4.0, "sn": "SN-SMS4-F3PR"},
    {"id": 36, "machine_id": 4, "name": "SMS-4 Fur-4 SP", "type": "SETPOINT", "register_address": "32017", "unit": "kW", "min": 0.0, "max": 10000.0, "sn": "SN-SMS4-F4SP"},
    {"id": 37, "machine_id": 4, "name": "SMS-4 Fur-4 kW", "type": "POWER", "register_address": "32018", "unit": "kW", "min": 0.0, "max": 10000.0, "sn": "SN-SMS4-F4KW"},
    {"id": 38, "machine_id": 4, "name": "SMS-4 Fur-4 PP%", "type": "POWER", "register_address": "32019", "unit": "%", "min": 0.0, "max": 100.0, "sn": "SN-SMS4-F4PP"},
    {"id": 39, "machine_id": 4, "name": "SMS-4 Fur-4 PR", "type": "SETPOINT", "register_address": "32020", "unit": "", "min": 1.0, "max": 4.0, "sn": "SN-SMS4-F4PR"},

    # Turbine Generators (40 - 44, machine_id = 5)
    {"id": 40, "machine_id": 5, "name": "30MW TG-1 kW", "type": "POWER", "register_address": "33001", "unit": "kW", "min": 0.0, "max": 30000.0, "sn": "SN-TG1"},
    {"id": 41, "machine_id": 5, "name": "30MW TG-2 kW", "type": "POWER", "register_address": "33002", "unit": "kW", "min": 0.0, "max": 30000.0, "sn": "SN-TG2"},
    {"id": 42, "machine_id": 5, "name": "33MW TG-3 kW", "type": "POWER", "register_address": "33003", "unit": "kW", "min": 0.0, "max": 33000.0, "sn": "SN-TG3"},
    {"id": 43, "machine_id": 5, "name": "30MW TG-4 kW", "type": "POWER", "register_address": "33004", "unit": "kW", "min": 0.0, "max": 30000.0, "sn": "SN-TG4"},
    {"id": 44, "machine_id": 5, "name": "40MW TG-5 kW", "type": "POWER", "register_address": "33005", "unit": "kW", "min": 0.0, "max": 40000.0, "sn": "SN-TG5"},

    # Consumption Accumulations (45 - 50, machine_id = 1)
    {"id": 45, "machine_id": 1, "name": "Grid Import kWh", "type": "ACCUMULATOR", "register_address": "34001", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-MTR1"},
    {"id": 46, "machine_id": 1, "name": "Grid Import kVah", "type": "ACCUMULATOR", "register_address": "34002", "unit": "kVah", "min": 0.0, "max": 10000000.0, "sn": "SN-MTR1"},
    {"id": 47, "machine_id": 1, "name": "Avg. P.F.", "type": "KPI", "register_address": "34003", "unit": "", "min": 0.0, "max": 1.0, "sn": "SN-MTR1"},
    {"id": 48, "machine_id": 1, "name": "Load Factor", "type": "KPI", "register_address": "34004", "unit": "", "min": 0.0, "max": 100.0, "sn": "SN-MTR1"},
    {"id": 49, "machine_id": 1, "name": "Grid Export kWh", "type": "ACCUMULATOR", "register_address": "34005", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-MTR2"},
    {"id": 50, "machine_id": 1, "name": "Grid Export kVah", "type": "ACCUMULATOR", "register_address": "34006", "unit": "kVah", "min": 0.0, "max": 10000000.0, "sn": "SN-MTR2"},

    # Physical Analytics Sensors (51 - 60)
    {"id": 51, "machine_id": 2, "name": "SMS-1 Furnace Temp", "type": "TEMPERATURE", "register_address": "35001", "unit": "°C", "min": 0.0, "max": 2000.0, "sn": "SN-SMS1-TEMP"},
    {"id": 52, "machine_id": 2, "name": "SMS-1 Furnace Pressure", "type": "PRESSURE", "register_address": "35002", "unit": "bar", "min": 0.0, "max": 5.0, "sn": "SN-SMS1-PRES"},
    {"id": 53, "machine_id": 2, "name": "SMS-1 Cooling Water Flow", "type": "FLOW", "register_address": "35003", "unit": "m³/h", "min": 0.0, "max": 500.0, "sn": "SN-SMS1-FLOW"},
    {"id": 54, "machine_id": 5, "name": "TG-2 Turbine RPM", "type": "SPEED", "register_address": "35004", "unit": "RPM", "min": 0.0, "max": 5000.0, "sn": "SN-TG2-RPM"},
    {"id": 55, "machine_id": 1, "name": "CB5214 Voltage", "type": "VOLTAGE", "register_address": "35005", "unit": "V", "min": 0.0, "max": 15000.0, "sn": "SN-CB5214-V"},
    {"id": 56, "machine_id": 1, "name": "CB5214 Current", "type": "CURRENT", "register_address": "35006", "unit": "A", "min": 0.0, "max": 1000.0, "sn": "SN-CB5214-A"},
    {"id": 57, "machine_id": 2, "name": "SMS Ambient Humidity", "type": "HUMIDITY", "register_address": "35007", "unit": "%", "min": 0.0, "max": 100.0, "sn": "SN-SMS-HUM"},
    {"id": 58, "machine_id": 2, "name": "SMS Carbon Dioxide (CO2)", "type": "GAS", "register_address": "35008", "unit": "ppm", "min": 0.0, "max": 2000.0, "sn": "SN-SMS-CO2"},
    {"id": 59, "machine_id": 2, "name": "SMS-1 Production Count", "type": "COUNT", "register_address": "35009", "unit": "heats", "min": 0.0, "max": 1000.0, "sn": "SN-SMS1-PROD"},
    {"id": 60, "machine_id": 4, "name": "SMS-4 Gas Level (CO)", "type": "GAS", "register_address": "35010", "unit": "ppm", "min": 0.0, "max": 100.0, "sn": "SN-SMS4-CO"}
]

def init_and_seed_db(db: Session):
    # 1. Compile schema tables dynamically
    Base.metadata.create_all(bind=engine)
    
    # 2. Check if roles are populated
    if db.query(Role).first() is not None:
        return
        
    print("[DATABASE SEED]: Database is empty. Initiating programmatic seeder...")
    
    # Seed default roles
    roles = [
        Role(id=1, name="Admin", permissions=["read_all", "write_all", "manage_users", "acknowledge_alarms", "manage_settings"]),
        Role(id=2, name="Plant Manager", permissions=["read_all", "write_all", "acknowledge_alarms"]),
        Role(id=3, name="Engineer", permissions=["read_all", "acknowledge_alarms"]),
        Role(id=4, name="Operator", permissions=["read_all", "acknowledge_alarms"]),
        Role(id=5, name="Viewer", permissions=["read_all"])
    ]
    for r in roles:
        db.add(r)
    db.commit()
    
    # Seed default admin user (password: admin123)
    admin = User(
        username="admin",
        email="admin@ieip-platform.com",
        password_hash="$2b$12$R.S2uUuWf9Uq0L8M2c2j5uUoA8bS3q1WlQpUaOqF.4n5D5U5m2k5e",
        role_id=1,
        is_active=True
    )
    db.add(admin)
    db.commit()
    
    # Seed settings
    settings_seed = [
        SystemSetting(key="sampling_interval_seconds", value="1", description="Sampling frequency of the telemetry ingestion"),
        SystemSetting(key="alarm_threshold_breaker_max", value="45000.0", description="Max breaker capacity for CB5214 (kW)"),
        SystemSetting(key="alarm_threshold_tg_max", value="30000.0", description="Max turbine power limit for 30MW TG-2 (kW)"),
        SystemSetting(key="alarm_threshold_sms_max", value="95000.0", description="Max threshold power for Steel Melting Shop combined load (kW)"),
        SystemSetting(key="prediction_horizon_minutes", value="60", description="ML Forecasting horizon window")
    ]
    for s in settings_seed:
        db.add(s)
    db.commit()
    
    # Seed Plant
    plant = Plant(id=1, name="Gary Steel Works", location="Gary, Indiana", timezone="EST", description="Primary integrated steel production mill", status="ACTIVE")
    db.add(plant)
    db.commit()
    
    # Seed Departments
    departments = [
        Department(id=1, plant_id=1, name="Power Distribution", description="Substations and distribution parameters"),
        Department(id=2, plant_id=1, name="Steel Melting Shop (SMS)", description="Electric Arc Furnace shops")
    ]
    for d in departments:
        db.add(d)
    db.commit()
    
    # Seed Machines
    machines = [
        Machine(id=1, department_id=1, name="Distribution-System", type="DISTRIBUTION", rated_capacity=150000.0, status="RUNNING"),
        Machine(id=2, department_id=2, name="SMS-1", type="SMS_SHOP", rated_capacity=70000.0, status="RUNNING"),
        Machine(id=3, department_id=2, name="SMS-2", type="SMS_SHOP", rated_capacity=70000.0, status="STOPPED"),
        Machine(id=4, department_id=2, name="SMS-4", type="SMS_SHOP", rated_capacity=30000.0, status="RUNNING"),
        Machine(id=5, department_id=1, name="Turbines", type="TURBINES", rated_capacity=63000.0, status="RUNNING")
    ]
    for m in machines:
        db.add(m)
    db.commit()
    
    # Seed Devices
    for dev_conf in DEVICES_CONFIG:
        device = Device(
            id=dev_conf["id"],
            machine_id=dev_conf["machine_id"],
            name=dev_conf["name"],
            type=dev_conf["type"],
            register_address=dev_conf["register_address"],
            unit=dev_conf["unit"],
            nominal_min=dev_conf["min"],
            nominal_max=dev_conf["max"],
            serial_number=dev_conf["sn"],
            firmware_version="v1.0.0",
            communication_status="ONLINE",
            is_active=True
        )
        db.add(device)
    db.commit()
    print("[DATABASE SEED]: Programmatic database seeding complete.")
