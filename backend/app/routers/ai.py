"""
IEIP AI Operations Copilot Router
Endpoints:
  - POST /chat
  - POST /ai/query
"""
import os
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.auth import get_current_user
from backend.app.models import User, SystemSetting
from backend.app.services.ai_copilot import (
    ChatPayload,
    AIQueryPayload,
    process_copilot_chat,
    execute_ai_query
)

router = APIRouter(tags=["AI Copilot"])


@router.post("/chat")
def chat_with_gemini(
    payload: ChatPayload,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Interacts with the AI Control Room Copilot with live telemetry snapshot."""
    return process_copilot_chat(payload, db)


@router.post("/ai/query")
def run_ai_query(
    payload: AIQueryPayload,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Executes a natural language text-to-SQL query using the database schema."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        db_key = db.query(SystemSetting).filter(SystemSetting.key == "GEMINI_API_KEY").first()
        if db_key and db_key.value:
            api_key = db_key.value

    return execute_ai_query(payload.question, db, api_key)
