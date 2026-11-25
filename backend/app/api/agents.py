from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import datetime
from backend.app.database import get_db
from backend.app import models, schemas
from backend.app.security import rbac

router = APIRouter(prefix="/agents", tags=["agents"])

@router.get("", response_model=List[schemas.AgentResponse])
def list_agents(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(rbac.allow_any)
):
    # Check heartbeat timeouts and update statuses to OFFLINE if needed
    now = datetime.datetime.utcnow()
    timeout_threshold = now - datetime.timedelta(seconds=90)  # 90 second tolerance
    
    overdue_agents = db.query(models.Agent).filter(
        models.Agent.last_seen < timeout_threshold,
        models.Agent.status == "ONLINE"
    ).all()
    
    for agent in overdue_agents:
        agent.status = "OFFLINE"
    if overdue_agents:
        db.commit()

    return db.query(models.Agent).all()

@router.get("/{agent_id}", response_model=schemas.AgentResponse)
def get_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(rbac.allow_any)
):
    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.post("/register", response_model=schemas.AgentResponse)
def register_agent(
    agent_in: schemas.AgentCreate,
    db: Session = Depends(get_db)
):
    agent = db.query(models.Agent).filter(models.Agent.id == agent_in.id).first()
    if agent:
        # Update existing agent information (heartbeat)
        agent.hostname = agent_in.hostname
        agent.os = agent_in.os
        agent.ip_address = agent_in.ip_address
        agent.username = agent_in.username
        agent.agent_version = agent_in.agent_version
        agent.last_seen = datetime.datetime.utcnow()
        agent.status = "ONLINE"
    else:
        # Register new agent
        agent = models.Agent(
            id=agent_in.id,
            hostname=agent_in.hostname,
            os=agent_in.os,
            ip_address=agent_in.ip_address,
            username=agent_in.username,
            agent_version=agent_in.agent_version,
            last_seen=datetime.datetime.utcnow(),
            status="ONLINE",
            risk_score=0
        )
        db.add(agent)
    
    db.commit()
    db.refresh(agent)
    return agent
