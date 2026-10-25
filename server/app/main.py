"""
Industrial Energy Intelligence Platform (IEIP)
Part 2: Server Application Entrypoint (FastAPI)
"""
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session
from sqlalchemy import text

from server.app.config import settings
from server.app.database import engine, Base, SessionLocal, get_db
from server.app.models import User
from server.app.schemas import HealthResponse
from server.app.auth import get_password_hash
from server.app.routers.auth import router as auth_router, limiter
from server.app.routers.live import router as live_router
from server.app.routers.history import router as history_router
from server.app.routers.alarms import router as alarms_router
from server.app.routers.ws import router as ws_router
from server.app.services.broadcaster import broadcaster
from server.app.services.alarm_engine import alarm_engine

def seed_admin_user_if_needed():
    """Initializes administrator user on first startup if no users exist in the database."""
    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        if user_count == 0:
            print(f"[STARTUP]: No users found. Creating initial admin user '{settings.ADMIN_USERNAME}'...")
            admin_user = User(
                username=settings.ADMIN_USERNAME,
                password_hash=get_password_hash(settings.ADMIN_PASSWORD),
                role="admin"
            )
            db.add(admin_user)
            db.commit()
            print(f"[STARTUP]: Initial admin user '{settings.ADMIN_USERNAME}' created successfully.")
    except Exception as e:
        print(f"[STARTUP WARNING]: Could not check or seed admin user: {e}")
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    print("=" * 70)
    print("      IEIP INDUSTRIAL ENERGY SERVER (PART 2 - FASTAPI)")
    print("=" * 70)
    print(f"[STARTUP]: Database Target -> {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'Configured'}")
    print(f"[STARTUP]: CORS Origins -> {settings.cors_origin_list}")
    print(f"[STARTUP]: WS Push Interval -> {settings.WS_PUSH_INTERVAL_SECONDS}s")

    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"[STARTUP WARNING]: Could not auto-create tables: {e}")

    seed_admin_user_if_needed()

    # Launch background supervisory workers
    broadcaster_task = asyncio.create_task(broadcaster.broadcast_loop())
    alarm_task = asyncio.create_task(alarm_engine.run_loop())

    yield

    # Shutdown actions
    broadcaster_task.cancel()
    alarm_task.cancel()
    print("[SHUTDOWN]: Server background tasks terminated.")

app = FastAPI(
    title="IEIP Industrial Energy Server",
    description="Dedicated Telemetry API & Real-time WebSocket Control Service",
    version="2.0.0",
    lifespan=lifespan
)

# SlowAPI rate-limiter attachment
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration strictly from CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Health endpoint (no authentication required)
@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """Public health verification endpoint."""
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    return HealthResponse(
        status="ONLINE" if db_ok else "DEGRADED",
        db_ok=db_ok,
        server_time=datetime.now().isoformat()
    )

# Include domain routers
app.include_router(auth_router)
app.include_router(live_router)
app.include_router(history_router)
app.include_router(alarms_router)
app.include_router(ws_router)
