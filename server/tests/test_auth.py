"""
Tests for Server Authentication, JWT Token Validation, RBAC, and WebSocket Handshake.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from server.app.auth import create_access_token, get_password_hash
from server.app.database import Base, get_db
from server.app.main import app
from server.app.models import User

# Isolated in-memory test database for deterministic test runs
test_engine = create_engine(
    "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
Base.metadata.create_all(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_db():
    """Seeds test users in test database and attaches dependency override."""
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    db = TestingSessionLocal()
    try:
        # Admin user
        admin = db.query(User).filter(User.username == "test_admin").first()
        if not admin:
            admin = User(
                username="test_admin",
                password_hash=get_password_hash("AdminPass123!"),
                role="admin",
            )
            db.add(admin)

        # Viewer user
        viewer = db.query(User).filter(User.username == "test_viewer").first()
        if not viewer:
            viewer = User(
                username="test_viewer",
                password_hash=get_password_hash("ViewerPass123!"),
                role="viewer",
            )
            db.add(viewer)

        # Operator user
        operator = db.query(User).filter(User.username == "test_operator").first()
        if not operator:
            operator = User(
                username="test_operator",
                password_hash=get_password_hash("OperatorPass123!"),
                role="operator",
            )
            db.add(operator)

        db.commit()
    finally:
        db.close()

    yield
    app.dependency_overrides.pop(get_db, None)


def test_login_success():
    response = client.post(
        "/api/auth/login", json={"username": "test_admin", "password": "AdminPass123!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "admin"
    assert data["username"] == "test_admin"


def test_login_failure():
    response = client.post(
        "/api/auth/login", json={"username": "test_admin", "password": "WrongPassword"}
    )
    assert response.status_code == 401
    assert "Invalid username or password" in response.json()["detail"]


def test_token_required_on_protected_endpoints():
    # Without token
    res_live = client.get("/api/live")
    assert res_live.status_code in [401, 403]

    res_alarms = client.get("/api/alarms")
    assert res_alarms.status_code in [401, 403]

    # Health endpoint is public
    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    assert "status" in res_health.json()


def test_role_enforcement():
    # Generate token for viewer
    viewer_token = create_access_token({"sub": "test_viewer", "role": "viewer"})
    headers = {"Authorization": f"Bearer {viewer_token}"}

    # Viewer can access read-only live & alarms
    res_alarms = client.get("/api/alarms", headers=headers)
    assert res_alarms.status_code == 200

    # Viewer cannot acknowledge alarms (requires admin, manager, engineer, operator)
    res_ack = client.post("/api/alarms/1/ack", headers=headers)
    assert res_ack.status_code == 403
    assert "Operation not permitted" in res_ack.json()["detail"]

    # Operator token can acknowledge
    operator_token = create_access_token({"sub": "test_operator", "role": "operator"})
    headers_op = {"Authorization": f"Bearer {operator_token}"}
    res_ack_op = client.post("/api/alarms/1/ack", headers=headers_op)
    # May be 404 (if alarm 1 doesn't exist) or 200, but NOT 403 Forbidden!
    assert res_ack_op.status_code != 403


def test_websocket_rejects_bad_token():
    with pytest.raises(Exception):
        with client.websocket_connect("/api/ws?token=invalid_garbage_token") as ws:
            ws.receive_text()

    with pytest.raises(Exception):
        with client.websocket_connect("/api/ws") as ws:
            ws.receive_text()


if __name__ == "__main__":
    pytest.main(["-v", __file__])
