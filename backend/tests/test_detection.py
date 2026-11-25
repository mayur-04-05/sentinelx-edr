import pytest
import datetime
import uuid
import asyncio
from backend.app import models
from backend.app.detection.engine import run_detection_engine
from backend.app.correlation.correlator import correlate_alert_to_incident

# Mark test as using anyio/asyncio
pytestmark = pytest.mark.anyio

async def test_detection_engine_suspicious_path(db):
    # Setup test agent
    agent_id = str(uuid.uuid4())
    agent = models.Agent(
        id=agent_id,
        hostname="det-test-host",
        os="Windows 11",
        agent_version="1.0.0",
        risk_score=0
    )
    db.add(agent)
    db.commit()

    # Create telemetry event that matches RULE_SUSPICIOUS_PATH
    event = models.TelemetryEvent(
        agent_id=agent_id,
        event_type="PROCESS",
        timestamp=datetime.datetime.utcnow(),
        severity="LOW",
        metadata_json={
            "pid": 5000,
            "ppid": 1000,
            "name": "suspicious_malware.exe",
            "exe": "C:\\Users\\user\\Downloads\\temp\\suspicious_malware.exe",
            "cmdline": ["suspicious_malware.exe"],
            "username": "tester"
        }
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    # Run detection
    await run_detection_engine([event], db)

    # Check alert was created
    alert = db.query(models.Alert).filter(models.Alert.agent_id == agent_id).first()
    assert alert is not None
    assert alert.rule_name == "RULE_SUSPICIOUS_PATH"
    assert alert.severity == "HIGH"
    assert alert.risk_score == 25
    assert alert.mitre_technique == "T1036"
    assert "suspicious_malware.exe" in alert.evidence["process_name"]

    # Check agent's risk score updated
    db.refresh(agent)
    assert agent.risk_score == 25

    # Check incident was created and correlated
    incident = db.query(models.Incident).filter(models.Incident.agent_id == agent_id).first()
    assert incident is not None
    assert incident.risk_score == 25
    assert alert.incident_id == incident.id

async def test_detection_engine_cmdline_pattern(db):
    agent_id = str(uuid.uuid4())
    agent = models.Agent(
        id=agent_id,
        hostname="det-test-host2",
        os="Windows 11",
        agent_version="1.0.0",
        risk_score=0
    )
    db.add(agent)
    db.commit()

    event = models.TelemetryEvent(
        agent_id=agent_id,
        event_type="PROCESS",
        timestamp=datetime.datetime.utcnow(),
        severity="LOW",
        metadata_json={
            "pid": 5001,
            "ppid": 1000,
            "name": "powershell.exe",
            "exe": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
            "cmdline": ["powershell.exe", "-nop", "-noni", "-enc", "c3VzcGljaW91cw=="],
            "username": "tester"
        }
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    await run_detection_engine([event], db)

    alert = db.query(models.Alert).filter(models.Alert.agent_id == agent_id).first()
    assert alert is not None
    assert alert.rule_name == "RULE_CMDLINE_PATTERN"
    assert alert.risk_score == 20
    assert alert.mitre_technique == "T1059.001"

async def test_correlation_process_tree_and_timeline(client, db):
    # Setup agent
    agent_id = str(uuid.uuid4())
    agent = models.Agent(
        id=agent_id,
        hostname="corr-test-host",
        os="Windows 11",
        agent_version="1.0.0",
        risk_score=0
    )
    db.add(agent)
    db.commit()

    # Create user for auth in client
    user_payload = {
        "username": "corr_analyst",
        "password": "corrpassword123",
        "role": "Analyst"
    }
    client.post("/api/auth/register", json=user_payload)
    login_res = client.post("/api/auth/login", data={"username": "corr_analyst", "password": "corrpassword123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Ingest events representing explorer.exe (100) -> powershell.exe (200) -> suspicious.exe (300)
    t1 = datetime.datetime.utcnow() - datetime.timedelta(seconds=10)
    t2 = datetime.datetime.utcnow() - datetime.timedelta(seconds=5)
    t3 = datetime.datetime.utcnow()
    
    e1 = models.TelemetryEvent(
        agent_id=agent_id, event_type="PROCESS", timestamp=t1, severity="LOW",
        metadata_json={"pid": 100, "ppid": 999, "name": "explorer.exe", "exe": "C:\\Windows\\explorer.exe", "cmdline": ["explorer.exe"], "username": "user", "action": "SPAWN"}
    )
    e2 = models.TelemetryEvent(
        agent_id=agent_id, event_type="PROCESS", timestamp=t2, severity="LOW",
        metadata_json={"pid": 200, "ppid": 100, "name": "powershell.exe", "exe": "C:\\Windows\\System32\\powershell.exe", "cmdline": ["powershell.exe"], "username": "user", "action": "SPAWN"}
    )
    e3 = models.TelemetryEvent(
        agent_id=agent_id, event_type="PROCESS", timestamp=t3, severity="LOW",
        metadata_json={"pid": 300, "ppid": 200, "name": "suspicious.exe", "exe": "C:\\Users\\user\\Downloads\\temp\\suspicious.exe", "cmdline": ["suspicious.exe"], "username": "user", "action": "SPAWN"}
    )
    
    db.add_all([e1, e2, e3])
    db.commit()
    db.refresh(e1)
    db.refresh(e2)
    db.refresh(e3)

    # Trigger detection on the suspicious path to spawn alert/incident
    await run_detection_engine([e3], db)

    incident = db.query(models.Incident).filter(models.Incident.agent_id == agent_id).first()
    assert incident is not None
    incident_id = incident.id

    # 2. Query process tree
    res_tree = client.get(f"/api/incidents/{incident_id}/process-tree", headers=headers)
    assert res_tree.status_code == 200, f"Process tree call failed: {res_tree.text}"
    tree = res_tree.json()
    
    # explorer (100) -> powershell (200) -> suspicious (300)
    assert tree["pid"] == 100
    assert len(tree["children"]) > 0
    assert tree["children"][0]["pid"] == 200
    assert len(tree["children"][0]["children"]) > 0
    assert tree["children"][0]["children"][0]["pid"] == 300

    # 3. Query timeline
    res_timeline = client.get(f"/api/incidents/{incident_id}/timeline", headers=headers)
    assert res_timeline.status_code == 200
    timeline = res_timeline.json()
    assert len(timeline) > 0
    
    types = [item["type"] for item in timeline]
    assert "PROCESS_SPAWN" in types
    assert "ALERT" in types

