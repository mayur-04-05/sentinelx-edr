import httpx
import uuid
import datetime

def test_agent_backend_integration():
    backend_url = "http://127.0.0.1:8000/api"
    agent_id = str(uuid.uuid4())
    
    # 1. Register agent
    register_payload = {
        "id": agent_id,
        "hostname": "test-host-integration",
        "os": "Windows 11 (Test Build)",
        "ip_address": "192.168.1.100",
        "username": "tester",
        "agent_version": "1.0.0"
    }
    
    res = httpx.post(f"{backend_url}/agents/register", json=register_payload)
    assert res.status_code == 200, f"Registration failed: {res.text}"
    agent_data = res.json()
    assert agent_data["id"] == agent_id
    assert agent_data["status"] == "ONLINE"
    
    # 2. Ingest telemetry
    telemetry_payload = [
        {
            "agent_id": agent_id,
            "event_type": "PROCESS",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "severity": "LOW",
            "metadata_json": {
                "pid": 9999,
                "ppid": 1111,
                "name": "integration_test.exe",
                "exe": "C:\\Windows\\Temp\\integration_test.exe",
                "cmdline": ["integration_test.exe", "--run-test"],
                "username": "tester",
                "create_time": datetime.datetime.utcnow().isoformat(),
                "sha256": "f2ca1bb6c7e907d06dafe4687e579fce76b377f93eec34b693bc2f57811af885",
                "status": "running",
                "action": "SPAWN"
            }
        }
    ]
    
    res_telemetry = httpx.post(f"{backend_url}/telemetry/ingest", json=telemetry_payload)
    assert res_telemetry.status_code == 202, f"Telemetry ingest failed: {res_telemetry.text}"
    assert res_telemetry.json()["count"] == 1
    
    # 3. Retrieve agent details using viewer token or direct query
    # (Since we don't have auth configured for listing agents in viewer mode unless we login,
    # let's login first or test registration again)
    # Let's register a test user to login and fetch lists
    user_payload = {
        "username": f"user_int_{uuid.uuid4().hex[:6]}",
        "password": "integrationpassword123",
        "role": "Analyst"
    }
    res_reg = httpx.post(f"{backend_url}/auth/register", json=user_payload)
    assert res_reg.status_code == 201
    
    # Login to get token
    login_data = {
        "username": user_payload["username"],
        "password": user_payload["password"]
    }
    res_login = httpx.post(f"{backend_url}/auth/login", data=login_data)
    assert res_login.status_code == 200
    token = res_login.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Verify agent listed
    res_agents = httpx.get(f"{backend_url}/agents", headers=headers)
    assert res_agents.status_code == 200
    agents = res_agents.json()
    assert any(a["id"] == agent_id for a in agents)
    
    # Verify telemetry listed
    res_tel_list = httpx.get(f"{backend_url}/telemetry?agent_id={agent_id}", headers=headers)
    assert res_tel_list.status_code == 200
    tel_list = res_tel_list.json()
    assert len(tel_list) > 0
    assert tel_list[0]["metadata_json"]["pid"] == 9999
    
    print("Integration test passed successfully!")
