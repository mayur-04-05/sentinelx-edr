import pytest
import uuid
import datetime
from backend.app import models

pytestmark = pytest.mark.anyio

async def test_pdf_report_generation(client, db):
    # Setup agent
    agent_id = str(uuid.uuid4())
    agent = models.Agent(
        id=agent_id, hostname="report-host", os="Windows 11", agent_version="1.0.0"
    )
    db.add(agent)
    db.commit()

    # Create user for auth in client
    user_payload = {
        "username": "report_analyst",
        "password": "reportpassword123",
        "role": "Analyst"
    }
    client.post("/api/auth/register", json=user_payload)
    login_res = client.post("/api/auth/login", data={"username": "report_analyst", "password": "reportpassword123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create Incident
    incident = models.Incident(
        title="Malicious Activity on report-host",
        severity="CRITICAL",
        risk_score=90,
        status="NEW",
        first_seen=datetime.datetime.utcnow(),
        last_seen=datetime.datetime.utcnow(),
        agent_id=agent_id
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)

    # Request PDF report
    response = client.get(f"/api/reports/incident/{incident.id}", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
    # Check that bytes are actually PDF
    content = response.read()
    assert content.startswith(b"%PDF")
