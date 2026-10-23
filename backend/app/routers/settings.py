"""
IEIP Settings & Security Audit Logs Router
Endpoints:
  - GET  /settings
  - POST /settings
  - GET  /audit-logs
"""
from typing import List
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.database import get_db
from backend.app.auth import get_current_user, RoleChecker
from backend.app.models import User, SystemSetting, AuditLog
from backend.app.schemas import SystemSettingOut, AuditLogOut
from backend.app.services.kpi_engine import log_audit

router = APIRouter(tags=["Settings & Audit"])


@router.get("/settings", response_model=List[SystemSettingOut])
def get_system_settings(db: Session = Depends(get_db)):
    return db.query(SystemSetting).all()


@router.post("/settings")
def update_system_settings(
    payload: dict,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    RoleChecker(["Admin", "Plant Manager"])(user, db)

    updated = []
    for k, v in payload.items():
        setting = db.query(SystemSetting).filter(SystemSetting.key == k).first()
        if setting:
            setting.value = str(v)
            updated.append(k)
        else:
            new_setting = SystemSetting(key=k, value=str(v))
            db.add(new_setting)
            updated.append(k)

    db.commit()
    client_host = request.client.host if request.client else "127.0.0.1"
    log_audit(db, "UPDATE_SETTINGS", f"Updated limit configurations: {', '.join(updated)}", user.id, client_host)
    return {"status": "success", "updated_settings": updated}


@router.get("/audit-logs", response_model=List[AuditLogOut])
def get_audit_logs(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin", "Plant Manager"])(user, db)
    return db.query(AuditLog).order_by(desc(AuditLog.time)).limit(100).all()
