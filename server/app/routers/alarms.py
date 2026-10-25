"""
Alarm Management Endpoints
Query alarms and acknowledge incidents with role-based authorization.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from server.app.database import get_db
from server.app.models import Alarm, User
from server.app.schemas import AlarmOut, AlarmAckResponse
from server.app.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/alarms", tags=["Alarms"])

ACK_ALLOWED_ROLES = ["admin", "manager", "engineer", "operator"]

@router.get("", response_model=List[AlarmOut])
def get_alarms(
    active: Optional[bool] = Query(None, description="Filter for active unresolved alarms"),
    limit: int = Query(100, ge=1, le=500, description="Max alarms to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns logged alarms.
    If active=true, only returns alarms that have not yet been resolved.
    """
    query = db.query(Alarm)
    if active is True:
        query = query.filter(Alarm.resolved_at.is_(None))
    elif active is False:
        query = query.filter(Alarm.resolved_at.is_not(None))

    alarms = query.order_by(desc(Alarm.ts)).limit(limit).all()
    return alarms

@router.post("/{alarm_id}/ack", response_model=AlarmAckResponse)
def acknowledge_alarm(
    alarm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ACK_ALLOWED_ROLES))
):
    """
    Acknowledges an alarm incident.
    Permitted roles: admin, manager, engineer, operator.
    """
    alarm = db.query(Alarm).filter(Alarm.id == alarm_id).first()
    if not alarm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alarm with ID {alarm_id} not found."
        )

    alarm.acknowledged = True
    alarm.acknowledged_by = current_user.username
    db.commit()

    return AlarmAckResponse(
        success=True,
        id=alarm.id,
        acknowledged_by=current_user.username,
        status="ACKNOWLEDGED"
    )
