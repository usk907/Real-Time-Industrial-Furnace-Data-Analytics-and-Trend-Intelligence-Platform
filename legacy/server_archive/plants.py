"""
IEIP Plant Hierarchy & Asset Management Router
Endpoints:
  - /plants (CRUD)
  - /departments (CRUD)
  - /machines (CRUD)
  - /devices (CRUD)
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.auth import get_current_user, RoleChecker
from backend.app.models import User, Plant, Department, Machine, Device
from backend.app.schemas import (
    PlantCreate, PlantOut,
    DepartmentCreate, DepartmentOut,
    MachineCreate, MachineOut,
    DeviceCreate, DeviceOut
)
from backend.app.services.kpi_engine import log_audit

router = APIRouter(tags=["Plant Hierarchy & Assets"])


# -----------------------------------------------------
# PLANT MANAGEMENT (CRUD)
# -----------------------------------------------------
@router.get("/plants", response_model=List[PlantOut])
def get_plants(db: Session = Depends(get_db)):
    return db.query(Plant).all()


@router.post("/plants", response_model=PlantOut, status_code=status.HTTP_201_CREATED)
def create_plant(payload: PlantCreate, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin", "Plant Manager"])(user, db)
    plant = Plant(
        name=payload.name,
        location=payload.location,
        timezone=payload.timezone,
        description=payload.description,
        status=payload.status
    )
    db.add(plant)
    db.commit()
    db.refresh(plant)
    client_host = request.client.host if request.client else "127.0.0.1"
    log_audit(db, "CREATE_PLANT", f"Created plant {plant.name}", user.id, client_host)
    return plant


@router.put("/plants/{plant_id}", response_model=PlantOut)
def update_plant(plant_id: int, payload: PlantCreate, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin", "Plant Manager"])(user, db)
    plant = db.query(Plant).filter(Plant.id == plant_id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    plant.name = payload.name
    plant.location = payload.location
    plant.timezone = payload.timezone
    plant.description = payload.description
    plant.status = payload.status

    db.commit()
    db.refresh(plant)
    client_host = request.client.host if request.client else "127.0.0.1"
    log_audit(db, "UPDATE_PLANT", f"Updated plant {plant.name}", user.id, client_host)
    return plant


@router.delete("/plants/{plant_id}")
def delete_plant(plant_id: int, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin", "Plant Manager"])(user, db)
    plant = db.query(Plant).filter(Plant.id == plant_id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    name = plant.name
    db.delete(plant)
    db.commit()
    client_host = request.client.host if request.client else "127.0.0.1"
    log_audit(db, "DELETE_PLANT", f"Deleted plant {name}", user.id, client_host)
    return {"status": "success", "message": f"Deleted plant {name}"}


# -----------------------------------------------------
# DEPARTMENT MANAGEMENT (CRUD)
# -----------------------------------------------------
@router.get("/departments", response_model=List[DepartmentOut])
def get_departments(db: Session = Depends(get_db)):
    return db.query(Department).all()


@router.post("/departments", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
def create_department(payload: DepartmentCreate, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin", "Plant Manager"])(user, db)
    dept = Department(
        plant_id=payload.plant_id,
        name=payload.name,
        description=payload.description
    )
    db.add(dept)
    db.commit()
    db.refresh(dept)
    client_host = request.client.host if request.client else "127.0.0.1"
    log_audit(db, "CREATE_DEPARTMENT", f"Created department {dept.name}", user.id, client_host)
    return dept


@router.put("/departments/{dept_id}", response_model=DepartmentOut)
def update_department(dept_id: int, payload: DepartmentCreate, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin", "Plant Manager"])(user, db)
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    dept.plant_id = payload.plant_id
    dept.name = payload.name
    dept.description = payload.description

    db.commit()
    db.refresh(dept)
    client_host = request.client.host if request.client else "127.0.0.1"
    log_audit(db, "UPDATE_DEPARTMENT", f"Updated department {dept.name}", user.id, client_host)
    return dept


@router.delete("/departments/{dept_id}")
def delete_department(dept_id: int, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin", "Plant Manager"])(user, db)
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    name = dept.name
    db.delete(dept)
    db.commit()
    client_host = request.client.host if request.client else "127.0.0.1"
    log_audit(db, "DELETE_DEPARTMENT", f"Deleted department {name}", user.id, client_host)
    return {"status": "success", "message": f"Deleted department {name}"}


# -----------------------------------------------------
# MACHINE MANAGEMENT (CRUD)
# -----------------------------------------------------
@router.get("/machines", response_model=List[MachineOut])
def get_machines(db: Session = Depends(get_db)):
    return db.query(Machine).all()


@router.post("/machines", response_model=MachineOut, status_code=status.HTTP_201_CREATED)
def create_machine(payload: MachineCreate, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin", "Plant Manager", "Engineer"])(user, db)
    mach = Machine(
        department_id=payload.department_id,
        name=payload.name,
        type=payload.type,
        rated_capacity=payload.rated_capacity,
        status=payload.status
    )
    db.add(mach)
    db.commit()
    db.refresh(mach)
    client_host = request.client.host if request.client else "127.0.0.1"
    log_audit(db, "CREATE_MACHINE", f"Created machine {mach.name}", user.id, client_host)
    return mach


@router.put("/machines/{mach_id}", response_model=MachineOut)
def update_machine(mach_id: int, payload: MachineCreate, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin", "Plant Manager", "Engineer"])(user, db)
    mach = db.query(Machine).filter(Machine.id == mach_id).first()
    if not mach:
        raise HTTPException(status_code=404, detail="Machine not found")

    mach.department_id = payload.department_id
    mach.name = payload.name
    mach.type = payload.type
    mach.rated_capacity = payload.rated_capacity
    mach.status = payload.status

    db.commit()
    db.refresh(mach)
    client_host = request.client.host if request.client else "127.0.0.1"
    log_audit(db, "UPDATE_MACHINE", f"Updated machine {mach.name}", user.id, client_host)
    return mach


@router.delete("/machines/{mach_id}")
def delete_machine(mach_id: int, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin", "Plant Manager", "Engineer"])(user, db)
    mach = db.query(Machine).filter(Machine.id == mach_id).first()
    if not mach:
        raise HTTPException(status_code=404, detail="Machine not found")

    name = mach.name
    db.delete(mach)
    db.commit()
    client_host = request.client.host if request.client else "127.0.0.1"
    log_audit(db, "DELETE_MACHINE", f"Deleted machine {name}", user.id, client_host)
    return {"status": "success", "message": f"Deleted machine {name}"}


# -----------------------------------------------------
# DEVICE MANAGEMENT (CRUD)
# -----------------------------------------------------
@router.get("/devices", response_model=List[DeviceOut])
def get_devices(db: Session = Depends(get_db)):
    return db.query(Device).all()


@router.post("/devices", response_model=DeviceOut, status_code=status.HTTP_201_CREATED)
def create_device(payload: DeviceCreate, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin", "Plant Manager", "Engineer"])(user, db)
    dev = Device(
        machine_id=payload.machine_id,
        name=payload.name,
        type=payload.type,
        register_address=payload.register_address,
        unit=payload.unit,
        nominal_min=payload.nominal_min,
        nominal_max=payload.nominal_max,
        serial_number=payload.serial_number,
        firmware_version=payload.firmware_version,
        communication_status=payload.communication_status,
        is_active=payload.is_active
    )
    db.add(dev)
    db.commit()
    db.refresh(dev)
    client_host = request.client.host if request.client else "127.0.0.1"
    log_audit(db, "CREATE_DEVICE", f"Created device {dev.name}", user.id, client_host)
    return dev


@router.put("/devices/{dev_id}", response_model=DeviceOut)
def update_device(dev_id: int, payload: DeviceCreate, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin", "Plant Manager", "Engineer"])(user, db)
    dev = db.query(Device).filter(Device.id == dev_id).first()
    if not dev:
        raise HTTPException(status_code=404, detail="Device not found")

    dev.machine_id = payload.machine_id
    dev.name = payload.name
    dev.type = payload.type
    dev.register_address = payload.register_address
    dev.unit = payload.unit
    dev.nominal_min = payload.nominal_min
    dev.nominal_max = payload.nominal_max
    dev.serial_number = payload.serial_number
    dev.firmware_version = payload.firmware_version
    dev.communication_status = payload.communication_status
    dev.is_active = payload.is_active

    db.commit()
    db.refresh(dev)
    client_host = request.client.host if request.client else "127.0.0.1"
    log_audit(db, "UPDATE_DEVICE", f"Updated device {dev.name}", user.id, client_host)
    return dev


@router.delete("/devices/{dev_id}")
def delete_device(dev_id: int, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin", "Plant Manager", "Engineer"])(user, db)
    dev = db.query(Device).filter(Device.id == dev_id).first()
    if not dev:
        raise HTTPException(status_code=404, detail="Device not found")

    name = dev.name
    db.delete(dev)
    db.commit()
    client_host = request.client.host if request.client else "127.0.0.1"
    log_audit(db, "DELETE_DEVICE", f"Deleted device {name}", user.id, client_host)
    return {"status": "success", "message": f"Deleted device {name}"}
