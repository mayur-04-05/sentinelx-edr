from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.database import get_db
from backend.app import models, schemas
from backend.app.security import rbac

router = APIRouter(prefix="/iocs", tags=["iocs"])

@router.get("", response_model=List[schemas.IOCResponse])
def list_iocs(
    value: Optional[str] = None,
    type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(rbac.allow_any)
):
    query = db.query(models.IOC)
    if value:
        query = query.filter(models.IOC.value.contains(value))
    if type:
        query = query.filter(models.IOC.type == type)
    if status:
        query = query.filter(models.IOC.status == status)
    return query.order_by(models.IOC.added_at.desc()).all()

@router.post("", response_model=schemas.IOCResponse, status_code=status.HTTP_201_CREATED)
def create_ioc(
    ioc_in: schemas.IOCCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(rbac.allow_analyst)
):
    existing = db.query(models.IOC).filter(models.IOC.value == ioc_in.value).first()
    if existing:
        raise HTTPException(status_code=400, detail="IOC already registered")
        
    ioc = models.IOC(
        value=ioc_in.value,
        type=ioc_in.type,
        status=ioc_in.status,
        description=ioc_in.description
    )
    db.add(ioc)
    db.commit()
    db.refresh(ioc)
    
    # Audit log
    audit_entry = models.AuditLog(
        username=current_user.username,
        action="IOC_CREATED",
        target=f"value={ioc.value}, type={ioc.type}",
        result="SUCCESS"
    )
    db.add(audit_entry)
    db.commit()
    
    return ioc

@router.patch("/{ioc_id}", response_model=schemas.IOCResponse)
def update_ioc(
    ioc_id: int,
    ioc_update: schemas.IOCUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(rbac.allow_analyst)
):
    ioc = db.query(models.IOC).filter(models.IOC.id == ioc_id).first()
    if not ioc:
        raise HTTPException(status_code=404, detail="IOC not found")
        
    ioc.status = ioc_update.status
    if ioc_update.description is not None:
        ioc.description = ioc_update.description
        
    db.commit()
    db.refresh(ioc)
    
    # Audit log
    audit_entry = models.AuditLog(
        username=current_user.username,
        action="IOC_UPDATED",
        target=f"ioc_id={ioc_id}, status={ioc.status}",
        result="SUCCESS"
    )
    db.add(audit_entry)
    db.commit()
    
    return ioc
