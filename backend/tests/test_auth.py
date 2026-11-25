def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_register_user(client):
    # Register admin (since it is the first user)
    payload = {
        "username": "admin_test",
        "password": "securepassword123",
        "role": "Admin"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "admin_test"
    assert data["role"] == "Admin"
    assert "hashed_password" not in data

def test_register_duplicate_username(client):
    payload = {
        "username": "user1",
        "password": "password",
        "role": "Analyst"
    }
    r1 = client.post("/api/auth/register", json=payload)
    assert r1.status_code == 201
    
    # Try again
    r2 = client.post("/api/auth/register", json=payload)
    assert r2.status_code == 400
    assert "already registered" in r2.json()["detail"]

def test_login_success(client):
    # Register first
    register_payload = {
        "username": "analyst1",
        "password": "mypassword",
        "role": "Analyst"
    }
    client.post("/api/auth/register", json=register_payload)
    
    # Login
    login_payload = {
        "username": "analyst1",
        "password": "mypassword"
    }
    response = client.post("/api/auth/login", data=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["username"] == "analyst1"
    assert data["role"] == "Admin"  # Note: since analyst1 was the first registered user in the conftest DB, it is escalated to Admin

def test_login_incorrect_password(client):
    # Register
    register_payload = {
        "username": "analyst2",
        "password": "mypassword",
        "role": "Analyst"
    }
    client.post("/api/auth/register", json=register_payload)
    
    # Login with wrong pwd
    login_payload = {
        "username": "analyst2",
        "password": "wrongpassword"
    }
    response = client.post("/api/auth/login", data=login_payload)
    assert response.status_code == 400
    assert "Incorrect username or password" in response.json()["detail"]
