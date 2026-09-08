import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_user_registration_and_login_flow():
    unique_id = uuid.uuid4().hex[:8]
    test_email = f"testuser_{unique_id}@seo-platform.com"
    test_password = "SecurePassword123!"

    # 1. Register new user
    response = client.post(
        "/api/v1/auth/register",
        json={"email": test_email, "password": test_password},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == test_email
    assert "id" in data
    assert data["role"] == "user"

    # 2. Attempt duplicate registration (should fail)
    dup_response = client.post(
        "/api/v1/auth/register",
        json={"email": test_email, "password": test_password},
    )
    assert dup_response.status_code == 400
    assert "already exists" in dup_response.json()["detail"]

    # 3. Invalid login attempt
    wrong_login = client.post(
        "/api/v1/auth/login",
        json={"email": test_email, "password": "WrongPassword!"},
    )
    assert wrong_login.status_code == 401

    # 4. Successful login attempt
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": test_email, "password": test_password},
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    token = token_data["access_token"]

    # 5. Access protected route without token (should fail)
    unauth_response = client.get("/api/v1/auth/me")
    assert unauth_response.status_code == 401

    # 6. Access protected route with valid token
    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    user_profile = me_response.json()
    assert user_profile["email"] == test_email
    assert user_profile["id"] == data["id"]
