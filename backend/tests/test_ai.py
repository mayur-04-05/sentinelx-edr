import pytest
import uuid
import datetime
from backend.app import models

pytestmark = pytest.mark.anyio

async def test_ai_offline_analysis(client, db):
    # Setup agent
    agent_id = str(uuid.uuid4())
    agent = models.Agent(
        id=agent_id, hostname="ai-host", os="Windows 11", agent_version="1.0.0"
    )
    db.add(agent)
    db.commit()

    # Create user for auth in client
    user_payload = {
        "username": "ai_analyst",
        "password": "aipassword123",
        "role": "Analyst"
    }
    client.post("/api/auth/register", json=user_payload)
    login_res = client.post("/api/auth/login", data={"username": "ai_analyst", "password": "aipassword123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create Incident
    incident = models.Incident(
        title="Suspicious activity on ai-host",
        severity="HIGH",
        risk_score=50,
        status="NEW",
        first_seen=datetime.datetime.utcnow(),
        last_seen=datetime.datetime.utcnow(),
        agent_id=agent_id
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)

    # Create Alert linked to Incident
    alert = models.Alert(
        agent_id=agent_id,
        rule_name="RULE_SUSPICIOUS_PATH",
        title="Suspicious Path Execution",
        severity="HIGH",
        risk_score=25,
        description="Process executed from temp folder",
        evidence={"exe_path": "C:\\Windows\\Temp\\mal.exe"},
        incident_id=incident.id
    )
    db.add(alert)
    db.commit()

    # Request AI investigation
    response = client.get(f"/api/ai/investigate/{incident.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "suspicious_reasons" in data
    assert "recommendations" in data
    
    # Check that it extracted recommendations and reasons based on the path rule alert
    assert any("downloads" in r or "temp" in r for r in data["suspicious_reasons"])
    assert any("Isolate the endpoint" in rec for rec in data["recommendations"])
