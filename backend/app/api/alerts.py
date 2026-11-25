from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.database import get_db
from backend.app import models, schemas
from backend.app.security import rbac

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("", response_model=List[schemas.AlertResponse])
def list_alerts(
    agent_id: Optional[str] = None,
    severity: Optional[str] = None,
    incident_id: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(rbac.allow_any)
):
    query = db.query(models.Alert)
    if agent_id:
        query = query.filter(models.Alert.agent_id == agent_id)
    if severity:
        query = query.filter(models.Alert.severity == severity)
    if incident_id:
        query = query.filter(models.Alert.incident_id == incident_id)
    return query.order_by(models.Alert.timestamp.desc()).limit(limit).all()

@router.get("/{alert_id}", response_model=schemas.AlertResponse)
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(rbac.allow_any)
):
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert
