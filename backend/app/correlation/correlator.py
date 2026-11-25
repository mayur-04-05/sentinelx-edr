import datetime
from sqlalchemy.orm import Session
from backend.app import models
from backend.app.logger import logger

# Import logger inside if needed, else define it
import logging
logger = logging.getLogger("sentinelx-correlation")

def correlate_alert_to_incident(alert: models.Alert, db: Session) -> models.Incident:
    """
    Correlates an alert to an existing open incident on the same agent within 15 minutes,
    or creates a new incident if none matches.
    """
    now = datetime.datetime.utcnow()
    correlation_window = now - datetime.timedelta(minutes=15)
    
    # 1. Search for existing incident on the same agent that is active
    incident = db.query(models.Incident).filter(
        models.Incident.agent_id == alert.agent_id,
        models.Incident.status.in_(["NEW", "INVESTIGATING"]),
        models.Incident.last_seen >= correlation_window
      ).order_by(models.Incident.last_seen.desc()).first()
      
    if incident:
        # Correlation found! Link alert to existing incident
        alert.incident_id = incident.id
        incident.last_seen = now
        
        # Risk score calculation: additive with decay or simply max score (capped at 100)
        # We will use additive model: add 50% of the new alert's score to the incident, capped at 100
        new_score = int(incident.risk_score + (alert.risk_score * 0.5))
        incident.risk_score = min(new_score, 100)
        
        # Dynamically escalate severity based on score
        if incident.risk_score >= 76:
            incident.severity = "CRITICAL"
        elif incident.risk_score >= 51:
            incident.severity = "HIGH"
        elif incident.risk_score >= 26:
            incident.severity = "MEDIUM"
        else:
            incident.severity = "LOW"
            
        logger.info(f"Correlated alert {alert.id} ({alert.title}) into existing Incident INC-{incident.id}")
    else:
        # Create a new Incident
        incident = models.Incident(
            title=f"Suspicious activity on {alert.agent_id[:8]} - {alert.title}",
            severity=alert.severity,
            risk_score=alert.risk_score,
            status="NEW",
            first_seen=alert.timestamp,
            last_seen=alert.timestamp,
            agent_id=alert.agent_id,
            analyst_notes="Automatically created by correlation engine."
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)
        
        # Link alert to the newly created incident
        alert.incident_id = incident.id
        logger.info(f"Created new Incident INC-{incident.id} for alert {alert.id} ({alert.title})")
        
    db.commit()
    db.refresh(incident)
    return incident
