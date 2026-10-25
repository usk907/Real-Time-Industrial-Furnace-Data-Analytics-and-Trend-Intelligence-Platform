"""
Tests for /api/live endpoint verifying 60 tags joined with metadata.
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from server.app.main import app
from server.app.auth import create_access_token
from server.app.models import FurnaceLatest, User
from server.app.database import Base, get_db
from server.app.routers.live import get_tag_metadata

# Isolated test database
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
Base.metadata.create_all(bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def setup_live_db():
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)

client = TestClient(app)

def test_live_telemetry_returns_60_tags():
    Base.metadata.create_all(bind=test_engine)
    meta_map = get_tag_metadata()
    assert len(meta_map) == 60, f"Expected 60 metadata tags, found {len(meta_map)}"

    db = TestingSessionLocal()
    try:
        now = datetime.now()
        # Seed test user
        if not db.query(User).filter(User.username == "test_admin").first():
            db.add(User(username="test_admin", password_hash="dummy", role="admin"))

        # Seed all 60 tags in furnace_latest
        for tag_name, meta in meta_map.items():
            db.add(FurnaceLatest(
                tag=tag_name,
                value=float(meta["start"]),
                ts=now
            ))
        db.commit()
    finally:
        db.close()

    # Query /api/live with valid JWT
    token = create_access_token({"sub": "test_admin", "role": "admin"})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/live", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert "tags" in data
    assert len(data["tags"]) == 60, f"Expected 60 live tags, got {len(data['tags'])}"

    # Validate structure of each tag
    first_tag = data["tags"][0]
    assert "tag" in first_tag
    assert "value" in first_tag
    assert "unit" in first_tag
    assert "status" in first_tag
    assert "ts" in first_tag
    assert "equipment" in first_tag

if __name__ == "__main__":
    pytest.main(["-v", __file__])
