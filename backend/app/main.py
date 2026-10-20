import sys
import asyncio

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.router import router
from backend.app.websocket_manager import ws_manager
from backend.app.database import SessionLocal

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Enable CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    try:
        loop = asyncio.get_event_loop()
        def handle_async_exception(loop, context):
            exc = context.get("exception")
            if isinstance(exc, (ConnectionResetError, ConnectionAbortedError, OSError)):
                return
            # Silence default connection-drop noise
        loop.set_exception_handler(handle_async_exception)
    except Exception:
        pass

    db = SessionLocal()
    try:
        from backend.app.seeder import init_and_seed_db
        init_and_seed_db(db)
    except Exception as e:
        print(f"[STARTUP ERROR]: Database initialization failed: {e}")
    finally:
        db.close()

# Register API routes
app.include_router(router, prefix=settings.API_V1_STR)

# Persistent WS connection route
@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Maintain socket link
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
