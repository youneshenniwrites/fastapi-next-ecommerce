from app.schemas.auth import Token

def test_register_login(client):
    # 1️⃣ Register a new user
    register_data = {"email": "test@example.com", "password": "password123"}
    response = client.post("/api/v1/auth/register", json=register_data)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

    # 2️⃣ Attempt login
    login_data = {"username": "test@example.com", "password": "password123"}
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

def test_login_wrong_password(client):
    # Attempt login with wrong password
    login_data = {"username": "test@example.com", "password": "wrongpassword"}
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"

def test_register_existing_email(client):
    # Attempt to register the same email again
    register_data = {"email": "test@example.com", "password": "password123"}
    response = client.post("/api/v1/auth/register", json=register_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"
