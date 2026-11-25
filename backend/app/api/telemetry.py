from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.database import get_db
from backend.app import models, schemas
from backend.app.security import rbac

from backend.app.logger import logger
from backend.app.detection.engine import run_detection_engine

router = APIRouter(prefix="/telemetry", tags=["telemetry"])

@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_telemetry(
    events: List[schemas.TelemetryEventCreate],
    db: Session = Depends(get_db)
):
    if not events:
        return {"status": "ignored", "count": 0}
        
    # Check if agent exists
    agent_id = events[0].agent_id
    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not registered"
        )
    
    # Update agent last seen
    import datetime
    agent.last_seen = datetime.datetime.utcnow()
    agent.status = "ONLINE"
    
    db_events = []
    for event in events:
        db_event = models.TelemetryEvent(
            agent_id=event.agent_id,
            event_type=event.event_type,
            timestamp=event.timestamp,
            severity=event.severity,
            metadata_json=event.metadata_json
        )
        db_events.append(db_event)
        
    db.add_all(db_events)
    db.commit()
    
    for db_event in db_events:
        db.refresh(db_event)
    
    # Run the behavioral detection engine
    try:
        await run_detection_engine(db_events, db)
    except Exception as e:
        logger.error(f"Detection engine failed: {e}", exc_info=True)
        
    return {"status": "success", "count": len(db_events)}

@router.get("", response_model=List[schemas.TelemetryEventResponse])
def get_telemetry(
    agent_id: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(rbac.allow_any)
):
    query = db.query(models.TelemetryEvent)
    if agent_id:
        query = query.filter(models.TelemetryEvent.agent_id == agent_id)
    if event_type:
        query = query.filter(models.TelemetryEvent.event_type == event_type)
    return query.order_by(models.TelemetryEvent.timestamp.desc()).limit(limit).all()
