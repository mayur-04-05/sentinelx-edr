from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.database import get_db
from backend.app import models, schemas
from backend.app.security import rbac

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("", response_model=List[schemas.AuditLogResponse])
def get_audit_logs(
    username: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(rbac.allow_analyst) # Only Analyst/Admin can view audit logs
):
    query = db.query(models.AuditLog)
    if username:
        query = query.filter(models.AuditLog.username == username)
    if action:
        query = query.filter(models.AuditLog.action == action)
    return query.order_by(models.AuditLog.timestamp.desc()).limit(limit).all()
