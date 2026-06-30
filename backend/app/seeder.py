from sqlalchemy.orm import Session
from backend.app.database import engine, Base
from backend.app.models import Role, User, Plant, Area, Equipment, Sensor

# Array of sensors configuration matching init-db.sql
SENSORS_CONFIG = [
    # Grid & Distribution (1 - 16, equipment_id = 1)
    {"id": 1, "equipment_id": 1, "name": "CB5214 kW", "type": "POWER", "register_address": "30001", "unit": "kW", "min": 0.0, "max": 50000.0},
    {"id": 2, "equipment_id": 1, "name": "CB14 kW", "type": "POWER", "register_address": "30002", "unit": "kW", "min": 0.0, "max": 50000.0},
    {"id": 3, "equipment_id": 1, "name": "CB52G4 kW", "type": "POWER", "register_address": "30003", "unit": "kW", "min": 0.0, "max": 30000.0},
    {"id": 4, "equipment_id": 1, "name": "CB52G14 kW", "type": "POWER", "register_address": "30004", "unit": "kW", "min": 0.0, "max": 30000.0},
    {"id": 5, "equipment_id": 1, "name": "CB52G24 kW", "type": "POWER", "register_address": "30005", "unit": "kW", "min": 0.0, "max": 30000.0},
    {"id": 6, "equipment_id": 1, "name": "SMS Allocated Power", "type": "POWER", "register_address": "30006", "unit": "kW", "min": 0.0, "max": 150000.0},
    {"id": 7, "equipment_id": 1, "name": "SMS Run. Power", "type": "POWER", "register_address": "30007", "unit": "kW", "min": 0.0, "max": 150000.0},
    {"id": 8, "equipment_id": 1, "name": "SMS-1 PR", "type": "SETPOINT", "register_address": "30008", "unit": "", "min": 0.0, "max": 5.0},
    {"id": 9, "equipment_id": 1, "name": "SMS-2 PR", "type": "SETPOINT", "register_address": "30009", "unit": "", "min": 0.0, "max": 5.0},
    {"id": 10, "equipment_id": 1, "name": "SMS-4 PR", "type": "SETPOINT", "register_address": "30010", "unit": "", "min": 0.0, "max": 5.0},
    {"id": 11, "equipment_id": 1, "name": "SMS-1 Max Set", "type": "SETPOINT", "register_address": "30011", "unit": "kW", "min": 0.0, "max": 100000.0},
    {"id": 12, "equipment_id": 1, "name": "SMS-1 Min Set", "type": "SETPOINT", "register_address": "30012", "unit": "kW", "min": 0.0, "max": 50000.0},
    {"id": 13, "equipment_id": 1, "name": "SMS-2 Max Set", "type": "SETPOINT", "register_address": "30013", "unit": "kW", "min": 0.0, "max": 100000.0},
    {"id": 14, "equipment_id": 1, "name": "SMS-2 Min Set", "type": "SETPOINT", "register_address": "30014", "unit": "kW", "min": 0.0, "max": 50000.0},
    {"id": 15, "equipment_id": 1, "name": "SMS-4 Max Set", "type": "SETPOINT", "register_address": "30015", "unit": "kW", "min": 0.0, "max": 100000.0},
    {"id": 16, "equipment_id": 1, "name": "SMS-4 Min Set", "type": "SETPOINT", "register_address": "30016", "unit": "kW", "min": 0.0, "max": 50000.0},

    # SMS-1 Furnace Parameters (17 - 19, equipment_id = 2)
    {"id": 17, "equipment_id": 2, "name": "SMS-1 Max Set", "type": "SETPOINT", "register_address": "31001", "unit": "kW", "min": 0.0, "max": 100000.0},
    {"id": 18, "equipment_id": 2, "name": "SMS-1 Avl. Power", "type": "POWER", "register_address": "31002", "unit": "kW", "min": 0.0, "max": 100000.0},
    {"id": 19, "equipment_id": 2, "name": "SMS-1 Run. Power", "type": "POWER", "register_address": "31003", "unit": "kW", "min": 0.0, "max": 100000.0},

    # SMS-4 Furnace Details (20 - 39, equipment_id = 4)
    {"id": 20, "equipment_id": 4, "name": "SMS-4 Max Set", "type": "SETPOINT", "register_address": "32001", "unit": "kW", "min": 0.0, "max": 50000.0},
    {"id": 21, "equipment_id": 4, "name": "SMS-4 Avl. Power", "type": "POWER", "register_address": "32002", "unit": "kW", "min": 0.0, "max": 50000.0},
    {"id": 22, "equipment_id": 4, "name": "SMS-4 Run. Power", "type": "POWER", "register_address": "32003", "unit": "kW", "min": 0.0, "max": 50000.0},
    {"id": 23, "equipment_id": 4, "name": "SMS-4 Utl. Factor(%)", "type": "KPI", "register_address": "32004", "unit": "%", "min": 0.0, "max": 100.0},
    {"id": 24, "equipment_id": 4, "name": "SMS-4 Fur-1 SP", "type": "SETPOINT", "register_address": "32005", "unit": "kW", "min": 0.0, "max": 10000.0},
    {"id": 25, "equipment_id": 4, "name": "SMS-4 Fur-1 kW", "type": "POWER", "register_address": "32006", "unit": "kW", "min": 0.0, "max": 10000.0},
    {"id": 26, "equipment_id": 4, "name": "SMS-4 Fur-1 PP%", "type": "POWER", "register_address": "32007", "unit": "%", "min": 0.0, "max": 100.0},
    {"id": 27, "equipment_id": 4, "name": "SMS-4 Fur-1 PR", "type": "SETPOINT", "register_address": "32008", "unit": "", "min": 1.0, "max": 4.0},
    {"id": 28, "equipment_id": 4, "name": "SMS-4 Fur-2 SP", "type": "SETPOINT", "register_address": "32009", "unit": "kW", "min": 0.0, "max": 10000.0},
    {"id": 29, "equipment_id": 4, "name": "SMS-4 Fur-2 kW", "type": "POWER", "register_address": "32010", "unit": "kW", "min": 0.0, "max": 10000.0},
    {"id": 30, "equipment_id": 4, "name": "SMS-4 Fur-2 PP%", "type": "POWER", "register_address": "32011", "unit": "%", "min": 0.0, "max": 100.0},
    {"id": 31, "equipment_id": 4, "name": "SMS-4 Fur-2 PR", "type": "SETPOINT", "register_address": "32012", "unit": "", "min": 1.0, "max": 4.0},
    {"id": 32, "equipment_id": 4, "name": "SMS-4 Fur-3 SP", "type": "SETPOINT", "register_address": "32013", "unit": "kW", "min": 0.0, "max": 10000.0},
    {"id": 33, "equipment_id": 4, "name": "SMS-4 Fur-3 kW", "type": "POWER", "register_address": "32014", "unit": "kW", "min": 0.0, "max": 10000.0},
    {"id": 34, "equipment_id": 4, "name": "SMS-4 Fur-3 PP%", "type": "POWER", "register_address": "32015", "unit": "%", "min": 0.0, "max": 100.0},
    {"id": 35, "equipment_id": 4, "name": "SMS-4 Fur-3 PR", "type": "SETPOINT", "register_address": "32016", "unit": "", "min": 1.0, "max": 4.0},
    {"id": 36, "equipment_id": 4, "name": "SMS-4 Fur-4 SP", "type": "SETPOINT", "register_address": "32017", "unit": "kW", "min": 0.0, "max": 10000.0},
    {"id": 37, "equipment_id": 4, "name": "SMS-4 Fur-4 kW", "type": "POWER", "register_address": "32018", "unit": "kW", "min": 0.0, "max": 10000.0},
    {"id": 38, "equipment_id": 4, "name": "SMS-4 Fur-4 PP%", "type": "POWER", "register_address": "32019", "unit": "%", "min": 0.0, "max": 100.0},
    {"id": 39, "equipment_id": 4, "name": "SMS-4 Fur-4 PR", "type": "SETPOINT", "register_address": "32020", "unit": "", "min": 1.0, "max": 4.0},

    # Turbine Generators (40 - 44, equipment_id = 5)
    {"id": 40, "equipment_id": 5, "name": "30MW TG-1 kW", "type": "POWER", "register_address": "33001", "unit": "kW", "min": 0.0, "max": 30000.0},
    {"id": 41, "equipment_id": 5, "name": "30MW TG-2 kW", "type": "POWER", "register_address": "33002", "unit": "kW", "min": 0.0, "max": 30000.0},
    {"id": 42, "equipment_id": 5, "name": "33MW TG-3 kW", "type": "POWER", "register_address": "33003", "unit": "kW", "min": 0.0, "max": 33000.0},
    {"id": 43, "equipment_id": 5, "name": "30MW TG-4 kW", "type": "POWER", "register_address": "33004", "unit": "kW", "min": 0.0, "max": 30000.0},
    {"id": 44, "equipment_id": 5, "name": "40MW TG-5 kW", "type": "POWER", "register_address": "33005", "unit": "kW", "min": 0.0, "max": 40000.0},

    # Consumption Accumulations (45 - 50, equipment_id = 1)
    {"id": 45, "equipment_id": 1, "name": "Grid Import kWh", "type": "ACCUMULATOR", "register_address": "34001", "unit": "kWh", "min": 0.0, "max": 1000000.0},
    {"id": 46, "equipment_id": 1, "name": "Grid Import kVah", "type": "ACCUMULATOR", "register_address": "34002", "unit": "kVah", "min": 0.0, "max": 1000000.0},
    {"id": 47, "equipment_id": 1, "name": "Avg. P.F.", "type": "KPI", "register_address": "34003", "unit": "", "min": 0.0, "max": 1.0},
    {"id": 48, "equipment_id": 1, "name": "Load Factor", "type": "KPI", "register_address": "34004", "unit": "", "min": 0.0, "max": 100.0},
    {"id": 49, "equipment_id": 1, "name": "Grid Export kWh", "type": "ACCUMULATOR", "register_address": "34005", "unit": "kWh", "min": 0.0, "max": 1000000.0},
    {"id": 50, "equipment_id": 1, "name": "Grid Export kVah", "type": "ACCUMULATOR", "register_address": "34006", "unit": "kVah", "min": 0.0, "max": 1000000.0}
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
        Role(id=1, name="Administrator", permissions=["read_all", "write_all", "manage_users", "acknowledge_alarms"]),
        Role(id=2, name="Plant Engineer", permissions=["read_all", "write_all", "acknowledge_alarms"]),
        Role(id=3, name="Operator", permissions=["read_all", "acknowledge_alarms"]),
        Role(id=4, name="Viewer", permissions=["read_all"])
    ]
    for r in roles:
        db.add(r)
    db.commit()
    
    # Seed default admin user (password: password123)
    admin = User(
        username="admin",
        email="admin@industrial-analytics.com",
        password_hash="$2b$12$4O6lXWjX47.dJp8Xy4eB2OnX4m9/k93lqGheUa1s9p9Qx.J/3aK62",
        role_id=1,
        is_active=True
    )
    db.add(admin)
    db.commit()
    
    # Seed Plant
    plant = Plant(id=1, name="Gary Steel Works", location="Gary, Indiana", status="ACTIVE")
    db.add(plant)
    db.commit()
    
    # Seed Areas
    areas = [
        Area(id=1, plant_id=1, name="Power Distribution", description="Substations and distribution parameters"),
        Area(id=2, plant_id=1, name="Steel Melting Shop (SMS)", description="Electric Arc Furnace shops")
    ]
    for a in areas:
        db.add(a)
    db.commit()
    
    # Seed Equipment
    equipment = [
        Equipment(id=1, area_id=1, name="Distribution-System", type="DISTRIBUTION", status="RUNNING"),
        Equipment(id=2, area_id=2, name="SMS-1", type="SMS_SHOP", status="RUNNING"),
        Equipment(id=3, area_id=2, name="SMS-2", type="SMS_SHOP", status="STOPPED"),
        Equipment(id=4, area_id=2, name="SMS-4", type="SMS_SHOP", status="RUNNING"),
        Equipment(id=5, area_id=1, name="Turbines", type="TURBINES", status="RUNNING")
    ]
    for eq in equipment:
        db.add(eq)
    db.commit()
    
    # Seed Sensors
    for s_conf in SENSORS_CONFIG:
        sensor = Sensor(
            id=s_conf["id"],
            equipment_id=s_conf["equipment_id"],
            name=s_conf["name"],
            type=s_conf["type"],
            register_address=s_conf["register_address"],
            unit=s_conf["unit"],
            nominal_min=s_conf["min"],
            nominal_max=s_conf["max"],
            is_active=True
        )
        db.add(sensor)
    db.commit()
    print("[DATABASE SEED]: Programmatic database seeding complete.")
