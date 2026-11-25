from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime
from backend.app.database import get_db
from backend.app import models, schemas
from backend.app.security import rbac

router = APIRouter(prefix="/incidents", tags=["incidents"])

@router.get("", response_model=List[schemas.IncidentResponse])
def list_incidents(
    agent_id: Optional[str] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(rbac.allow_any)
):
    query = db.query(models.Incident)
    if agent_id:
        query = query.filter(models.Incident.agent_id == agent_id)
    if status:
        query = query.filter(models.Incident.status == status)
    if severity:
        query = query.filter(models.Incident.severity == severity)
    return query.order_by(models.Incident.last_seen.desc()).limit(limit).all()

@router.get("/{incident_id}", response_model=schemas.IncidentResponse)
def get_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(rbac.allow_any)
):
    incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident

@router.patch("/{incident_id}", response_model=schemas.IncidentResponse)
def update_incident(
    incident_id: int,
    incident_update: schemas.IncidentUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(rbac.allow_analyst) # Only Analyst/Admin can update incidents
):
    incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    if incident_update.status:
        # Validate status value
        valid_statuses = ["NEW", "INVESTIGATING", "CONTAINED", "RESOLVED", "FALSE_POSITIVE"]
        if incident_update.status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")
        
        # Log status change in Audit Log
        audit_entry = models.AuditLog(
            username=current_user.username,
            action="INCIDENT_STATUS_CHANGED",
            target=f"incident_id={incident_id}, from={incident.status}, to={incident_update.status}",
            result="SUCCESS"
        )
        db.add(audit_entry)
        incident.status = incident_update.status
        
    if incident_update.analyst_notes is not None:
        incident.analyst_notes = incident_update.analyst_notes
        
    incident.updated_by = current_user.username
    incident.updated_at = datetime.datetime.utcnow()
    
    db.commit()
    db.refresh(incident)
    return incident

from backend.app.correlation.tree_builder import build_process_tree, compile_incident_timeline

@router.get("/{incident_id}/timeline")
def get_incident_timeline(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(rbac.allow_any)
):
    incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    return compile_incident_timeline(incident_id, db)

@router.get("/{incident_id}/process-tree")
def get_incident_process_tree(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(rbac.allow_any)
):
    incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    return build_process_tree(incident_id, db)
