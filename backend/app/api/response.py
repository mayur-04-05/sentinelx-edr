from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime
from backend.app.database import get_db
from backend.app import models, schemas
from backend.app.security import rbac

router = APIRouter(prefix="/response", tags=["response"])

@router.get("", response_model=List[schemas.ResponseActionResponse])
def list_response_actions(
    agent_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(rbac.allow_any)
):
    query = db.query(models.ResponseAction)
    if agent_id:
        query = query.filter(models.ResponseAction.agent_id == agent_id)
    return query.order_by(models.ResponseAction.timestamp.desc()).all()

@router.post("", response_model=schemas.ResponseActionResponse, status_code=status.HTTP_201_CREATED)
def trigger_response_action(
    action_in: schemas.ResponseActionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(rbac.allow_analyst)
):
    # Ensure agent exists
    agent = db.query(models.Agent).filter(models.Agent.id == action_in.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    # Prevent destructive system-critical process kills
    if action_in.action_type == "TERMINATE_PROCESS":
        pid = action_in.details.get("pid")
        proc_name = action_in.details.get("process_name", "").lower()
        if not pid:
            raise HTTPException(status_code=400, detail="PID is required for process termination")
        # Simple critical list
        critical_processes = ["system", "idle", "csrss.exe", "wininit.exe", "services.exe", "lsass.exe", "svchost.exe"]
        if proc_name in critical_processes:
            raise HTTPException(status_code=400, detail="Cannot terminate critical system process")
            
    new_action = models.ResponseAction(
        agent_id=action_in.agent_id,
        action_type=action_in.action_type,
        details=action_in.details,
        status="PENDING",
        analyst=current_user.username
    )
    db.add(new_action)
    db.commit()
    db.refresh(new_action)
    
    # Audit log
    audit_entry = models.AuditLog(
        username=current_user.username,
        action=f"RESPONSE_{action_in.action_type}_REQUESTED",
        target=f"agent_id={action_in.agent_id}, details={action_in.details}",
        result="SUCCESS"
    )
    db.add(audit_entry)
    db.commit()
    
    return new_action

@router.get("/pending/{agent_id}", response_model=List[schemas.ResponseActionResponse])
def get_pending_actions(
    agent_id: str,
    db: Session = Depends(get_db)
):
    # Agent checks for pending containment actions. No auth token required for the agent endpoint,
    # but we validate the agent exists.
    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not registered")
        
    return db.query(models.ResponseAction).filter(
        models.ResponseAction.agent_id == agent_id,
        models.ResponseAction.status == "PENDING"
    ).all()

@router.patch("/{action_id}", response_model=schemas.ResponseActionResponse)
def update_action_result(
    action_id: int,
    action_update: schemas.ResponseActionUpdate,
    db: Session = Depends(get_db)
):
    # Agent reports the execution result of a containment action
    action = db.query(models.ResponseAction).filter(models.ResponseAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Response Action not found")
        
    action.status = action_update.status
    if action_update.result_message:
        action.result_message = action_update.result_message
        
    db.commit()
    db.refresh(action)
    
    # Log execution result in audit logs
    audit_entry = models.AuditLog(
        username="agent_transport",
        action=f"RESPONSE_{action.action_type}_COMPLETED",
        target=f"action_id={action_id}, status={action.status}",
        result=action.status
    )
    db.add(audit_entry)
    db.commit()
    
    return action
