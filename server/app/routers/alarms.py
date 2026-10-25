"""
IEIP Alarms Console & Notifications Router
Endpoints:
  - GET /alarms
  - PUT /alarms/{alarm_id}/acknowledge
  - GET /notifications
  - PUT /notifications/{note_id}/read
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.database import get_db
from backend.app.auth import get_current_user, RoleChecker
from backend.app.models import User, Alarm, Notification
from backend.app.schemas import AlarmOut, AlarmAcknowledge, NotificationOut
from backend.app.services.kpi_engine import log_audit

router = APIRouter(tags=["Alarms & Notifications"])


# -----------------------------------------------------
# ALARMS CONSOLE API
# -----------------------------------------------------
@router.get("/alarms", response_model=List[AlarmOut])
def get_alarms(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Alarm)
    if status:
        query = query.filter(Alarm.status == status)
    if severity:
        query = query.filter(Alarm.severity == severity)
    return query.order_by(desc(Alarm.time)).all()


@router.put("/alarms/{alarm_id}/acknowledge")
def acknowledge_alarm(
    alarm_id: int,
    payload: AlarmAcknowledge,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    RoleChecker(["Admin", "Plant Manager", "Engineer", "Operator"])(user, db)
    alarm = db.query(Alarm).filter(Alarm.id == alarm_id).first()
    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm not found.")

    alarm.status = "ACKNOWLEDGED"
    alarm.acknowledged_by = payload.acknowledged_by
    alarm.comments = payload.comments
    db.commit()

    client_host = request.client.host if request.client else "127.0.0.1"
    log_audit(db, "ACKNOWLEDGE_ALARM", f"User acknowledged alarm #{alarm_id}: {payload.comments}", user.id, client_host)
    return {"status": "success", "alarm_id": alarm_id, "state": "ACKNOWLEDGED"}


# -----------------------------------------------------
# NOTIFICATIONS INBOX API
# -----------------------------------------------------
@router.get("/notifications", response_model=List[NotificationOut])
def get_notifications(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Notification).filter(Notification.user_id == user.id).order_by(desc(Notification.created_at)).all()


@router.put("/notifications/{note_id}/read")
def mark_notification_read(note_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    note = db.query(Notification).filter(Notification.id == note_id, Notification.user_id == user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Notification not found")
    note.read = True
    db.commit()
    return {"status": "success"}
