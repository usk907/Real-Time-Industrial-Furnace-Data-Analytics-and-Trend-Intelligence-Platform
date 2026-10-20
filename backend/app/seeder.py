from sqlalchemy.orm import Session
from backend.app.database import engine, Base
from backend.app.models import Role, User, Plant, Department, Machine, Device, SystemSetting, SensorReading, Alarm, Event, Prediction, KPIHistory, Report, AuditLog, Notification

# Array of devices configuration matching init-db.sql
DEVICES_CONFIG = [
    # Grid & Distribution (1 - 4, machine_id = 1)
    {"id": 1, "machine_id": 1, "name": "Grid Import kWh", "type": "ACCUMULATOR", "register_address": "30001", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-MTR1"},
    {"id": 2, "machine_id": 1, "name": "Grid Import kVah", "type": "ACCUMULATOR", "register_address": "30002", "unit": "kVah", "min": 0.0, "max": 10000000.0, "sn": "SN-MTR1"},
    {"id": 3, "machine_id": 1, "name": "Grid Export kWh", "type": "ACCUMULATOR", "register_address": "30003", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-MTR2"},
    {"id": 4, "machine_id": 1, "name": "Grid Export kVah", "type": "ACCUMULATOR", "register_address": "30004", "unit": "kVah", "min": 0.0, "max": 10000000.0, "sn": "SN-MTR2"},

    # Turbine Generators (5 - 9, machine_id = 5)
    {"id": 5, "machine_id": 5, "name": "30MW TG-1 kWh", "type": "ACCUMULATOR", "register_address": "30005", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-TG1"},
    {"id": 6, "machine_id": 5, "name": "30MW TG-2 kWh", "type": "ACCUMULATOR", "register_address": "30006", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-TG2"},
    {"id": 7, "machine_id": 5, "name": "33MW TG-3 kWh", "type": "ACCUMULATOR", "register_address": "30007", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-TG3"},
    {"id": 8, "machine_id": 5, "name": "30MW TG-4 kWh", "type": "ACCUMULATOR", "register_address": "30008", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-TG4"},
    {"id": 9, "machine_id": 5, "name": "40MW TG-5 kWh", "type": "ACCUMULATOR", "register_address": "30009", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-TG5"},

    # SMS-1 Furnace Parameters (10 - 17, machine_id = 2)
    {"id": 10, "machine_id": 2, "name": "SMS-1 Fur-1 kWh", "type": "ACCUMULATOR", "register_address": "30010", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SMS1-F1"},
    {"id": 11, "machine_id": 2, "name": "SMS-1 Fur-2 kWh", "type": "ACCUMULATOR", "register_address": "30011", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SMS1-F2"},
    {"id": 12, "machine_id": 2, "name": "SMS-1 Fur-3 kWh", "type": "ACCUMULATOR", "register_address": "30012", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SMS1-F3"},
    {"id": 13, "machine_id": 2, "name": "SMS-1 Fur-4 kWh", "type": "ACCUMULATOR", "register_address": "30013", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SMS1-F4"},
    {"id": 14, "machine_id": 2, "name": "SMS-1 Fur-5 kWh", "type": "ACCUMULATOR", "register_address": "30014", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SMS1-F5"},
    {"id": 15, "machine_id": 2, "name": "SMS-1 Aux-1 kWh", "type": "ACCUMULATOR", "register_address": "30015", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SMS1-A1"},
    {"id": 16, "machine_id": 2, "name": "SMS-1 Aux-2 kWh", "type": "ACCUMULATOR", "register_address": "30016", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SMS1-A2"},
    {"id": 17, "machine_id": 2, "name": "SMS-1 Sint kWh", "type": "ACCUMULATOR", "register_address": "30017", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SMS1-SINT"},

    # SAF Shop Parameters (18 - 20, machine_id = 6)
    {"id": 18, "machine_id": 6, "name": "SAF-1(2x9Mva) kWh", "type": "ACCUMULATOR", "register_address": "30018", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SAF1"},
    {"id": 19, "machine_id": 6, "name": "SAF-2(2x9Mva) kWh", "type": "ACCUMULATOR", "register_address": "30019", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SAF2"},
    {"id": 20, "machine_id": 6, "name": "SAF-3(2x4.5Mva) kWh", "type": "ACCUMULATOR", "register_address": "30020", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SAF3"},

    # Rolling Mills Parameters (21 - 23, machine_id = 7)
    {"id": 21, "machine_id": 7, "name": "RMD kWh", "type": "ACCUMULATOR", "register_address": "30021", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-RMD"},
    {"id": 22, "machine_id": 7, "name": "SRM kWh", "type": "ACCUMULATOR", "register_address": "30022", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SRM"},
    {"id": 23, "machine_id": 7, "name": "WRM kWh", "type": "ACCUMULATOR", "register_address": "30023", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-WRM"},

    # SMS-2 Furnace Parameters (24 - 35, 40 - 41, machine_id = 3)
    {"id": 24, "machine_id": 3, "name": "SMS-2 Fur-1 kWh", "type": "ACCUMULATOR", "register_address": "30024", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SMS2-F1"},
    {"id": 25, "machine_id": 3, "name": "SMS-2 Fur-2 kWh", "type": "ACCUMULATOR", "register_address": "30025", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SMS2-F2"},
    {"id": 26, "machine_id": 3, "name": "SMS-2 Fur-3 kWh", "type": "ACCUMULATOR", "register_address": "30026", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SMS2-F3"},
    {"id": 27, "machine_id": 3, "name": "SMS-2 Fur-4 kWh", "type": "ACCUMULATOR", "register_address": "30027", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SMS2-F4"},
    {"id": 28, "machine_id": 3, "name": "SMS-2 Fur-5 kWh", "type": "ACCUMULATOR", "register_address": "30028", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SMS2-F5"},
    {"id": 29, "machine_id": 3, "name": "SMS-2 Fur-6 kWh", "type": "ACCUMULATOR", "register_address": "30029", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SMS2-F6"},
    {"id": 30, "machine_id": 3, "name": "SMS-2 Fur-7 kWh", "type": "ACCUMULATOR", "register_address": "30030", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SMS2-F7"},
    {"id": 31, "machine_id": 3, "name": "SMS-2 Fur-8 kWh", "type": "ACCUMULATOR", "register_address": "30031", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SMS2-F8"},
    {"id": 32, "machine_id": 3, "name": "SMS-2 Fur-9 kWh", "type": "ACCUMULATOR", "register_address": "30032", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SMS2-F9"},
    {"id": 33, "machine_id": 3, "name": "SMS-2 Fur-10 kWh", "type": "ACCUMULATOR", "register_address": "30033", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SMS2-F10"},
    {"id": 34, "machine_id": 3, "name": "SMS-2 Fur-11 kWh", "type": "ACCUMULATOR", "register_address": "30034", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SMS2-F11"},
    {"id": 35, "machine_id": 3, "name": "SMS-2 Fur-12 kWh", "type": "ACCUMULATOR", "register_address": "30035", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SMS2-F12"},
    {"id": 40, "machine_id": 3, "name": "SMS-2 Aux-1 kWh", "type": "ACCUMULATOR", "register_address": "30040", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SMS2-A1"},
    {"id": 41, "machine_id": 3, "name": "SMS-2 Aux-2 kWh", "type": "ACCUMULATOR", "register_address": "30041", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SMS2-A2"},

    # SMS-4 Furnace Details (36 - 39, 42 - 48, machine_id = 4)
    {"id": 36, "machine_id": 4, "name": "SMS-4 Fur-1 kWh", "type": "ACCUMULATOR", "register_address": "30036", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SMS4-F1"},
    {"id": 37, "machine_id": 4, "name": "SMS-4 Fur-2 kWh", "type": "ACCUMULATOR", "register_address": "30037", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SMS4-F2"},
    {"id": 38, "machine_id": 4, "name": "SMS-4 Fur-3 kWh", "type": "ACCUMULATOR", "register_address": "30038", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SMS4-F3"},
    {"id": 39, "machine_id": 4, "name": "SMS-4 Fur-4 kWh", "type": "ACCUMULATOR", "register_address": "30039", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SMS4-F4"},
    {"id": 42, "machine_id": 4, "name": "SMS-4 Sint-1 kWh", "type": "ACCUMULATOR", "register_address": "30042", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SMS4-SINT1"},
    {"id": 43, "machine_id": 4, "name": "SMS-4 Sint-2 kWh", "type": "ACCUMULATOR", "register_address": "30043", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SMS4-SINT2"},
    {"id": 44, "machine_id": 4, "name": "SMS-4 Aux kWh", "type": "ACCUMULATOR", "register_address": "30044", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SMS4-AUX"},
    {"id": 45, "machine_id": 4, "name": "SMS-4 TR2MVA kWh", "type": "ACCUMULATOR", "register_address": "30045", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SMS4-TR2"},
    {"id": 46, "machine_id": 4, "name": "SMS-4 TR6MVA kWh", "type": "ACCUMULATOR", "register_address": "30046", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SMS4-TR6"},
    {"id": 47, "machine_id": 4, "name": "SMS-4 TR3.6MVA kWh", "type": "ACCUMULATOR", "register_address": "30047", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SMS4-TR36"},
    {"id": 48, "machine_id": 4, "name": "SMS-4 TR5MVA kWh", "type": "ACCUMULATOR", "register_address": "30048", "unit": "kWh", "min": 0.0, "max": 10000000.0, "sn": "SN-SMS4-TR5"}
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
        password_hash="$2b$12$g7G0jnTp45zk0JcN1uCMjO34TnMmj//Wu2NjNCva2Z76HqumX3t7.",
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
    plant = Plant(id=1, name="Shyam Metaliks & Energy Ltd.", location="West Bengal, India", timezone="IST", description="Integrated steel and ferro alloys plant", status="ACTIVE")
    db.add(plant)
    db.commit()
    
    # Seed Departments
    departments = [
        Department(id=1, plant_id=1, name="Power Distribution", description="Substations and distribution parameters"),
        Department(id=2, plant_id=1, name="Steel Melting Shop (SMS)", description="Electric Arc Furnace shops"),
        Department(id=3, plant_id=1, name="Ferro Alloys (SAF)", description="Submerged Arc Furnace shops"),
        Department(id=4, plant_id=1, name="Rolling Mills", description="Rolling Mill mills")
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
        Machine(id=5, department_id=1, name="Turbines", type="TURBINES", rated_capacity=63000.0, status="RUNNING"),
        Machine(id=6, department_id=3, name="SAF-Shop", type="FERRO_ALLOYS", rated_capacity=18000.0, status="RUNNING"),
        Machine(id=7, department_id=4, name="Rolling-Mills", type="ROLLING_MILLS", rated_capacity=20000.0, status="RUNNING")
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
