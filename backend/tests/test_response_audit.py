import pytest
import datetime
import uuid
from backend.app import models

pytestmark = pytest.mark.anyio

async def test_response_action_lifecycle(client, db):
    # Setup agent
    agent_id = str(uuid.uuid4())
    agent = models.Agent(
        id=agent_id, hostname="resp-host", os="Windows 11", agent_version="1.0.0"
    )
    db.add(agent)
    db.commit()

    # Create analyst user to trigger action
    user_payload = {
        "username": "resp_analyst",
        "password": "resp_password123",
        "role": "Analyst"
    }
    client.post("/api/auth/register", json=user_payload)
    login_res = client.post("/api/auth/login", data={"username": "resp_analyst", "password": "resp_password123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Analyst requests process kill
    action_payload = {
        "agent_id": agent_id,
        "action_type": "TERMINATE_PROCESS",
        "details": {"pid": 7890, "process_name": "malicious.exe"}
    }
    
    res = client.post("/api/response", json=action_payload, headers=headers)
    assert res.status_code == 201
    action_data = res.json()
    action_id = action_data["id"]
    assert action_data["status"] == "PENDING"
    assert action_data["action_type"] == "TERMINATE_PROCESS"
    
    # Verify Audit Log was generated for requested action
    audit1 = db.query(models.AuditLog).filter(models.AuditLog.action == "RESPONSE_TERMINATE_PROCESS_REQUESTED").first()
    assert audit1 is not None
    assert "resp_analyst" in audit1.username
    assert "7890" in audit1.target

    # 2. Agent fetches pending actions
    res_pending = client.get(f"/api/response/pending/{agent_id}")
    assert res_pending.status_code == 200
    pending_list = res_pending.json()
    assert len(pending_list) == 1
    assert pending_list[0]["id"] == action_id

    # 3. Agent reports success execution
    res_update = client.patch(
        f"/api/response/{action_id}",
        json={"status": "SUCCESS", "result_message": "Terminated successfully"}
    )
    assert res_update.status_code == 200
    assert res_update.json()["status"] == "SUCCESS"
    assert res_update.json()["result_message"] == "Terminated successfully"

    # Verify Audit Log was generated for completed action
    audit2 = db.query(models.AuditLog).filter(models.AuditLog.action == "RESPONSE_TERMINATE_PROCESS_COMPLETED").first()
    assert audit2 is not None
    assert audit2.result == "SUCCESS"

    # 4. Read Audit logs list (restricted to analyst token)
    res_logs = client.get("/api/audit", headers=headers)
    assert res_logs.status_code == 200
    logs = res_logs.json()
    # verify both logs are present in results
    actions = [l["action"] for l in logs]
    assert "RESPONSE_TERMINATE_PROCESS_REQUESTED" in actions
    assert "RESPONSE_TERMINATE_PROCESS_COMPLETED" in actions

async def test_response_action_critical_protection(client, db):
    # Setup agent
    agent_id = str(uuid.uuid4())
    agent = models.Agent(
        id=agent_id, hostname="resp-host2", os="Windows 11", agent_version="1.0.0"
    )
    db.add(agent)
    db.commit()

    user_payload = {
        "username": "resp_analyst2",
        "password": "resp_password123",
        "role": "Analyst"
    }
    client.post("/api/auth/register", json=user_payload)
    login_res = client.post("/api/auth/login", data={"username": "resp_analyst2", "password": "resp_password123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to terminate protected critical process
    action_payload = {
        "agent_id": agent_id,
        "action_type": "TERMINATE_PROCESS",
        "details": {"pid": 4, "process_name": "lsass.exe"} # Protected!
    }
    
    res = client.post("/api/response", json=action_payload, headers=headers)
    assert res.status_code == 400
    assert "Cannot terminate critical system process" in res.json()["detail"]
