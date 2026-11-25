from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app import models
from backend.app.security import rbac
from backend.app.ai.assistant import analyze_incident_threat

router = APIRouter(prefix="/ai", tags=["ai"])

@router.get("/investigate/{incident_id}")
async def investigate_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(rbac.allow_any)
):
    incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    analysis = await analyze_incident_threat(incident_id, db)
    return analysis
