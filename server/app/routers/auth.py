"""
Authentication Endpoints
Login route with slowapi rate-limiting and JWT token generation.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from server.app.auth import create_access_token, get_current_user, verify_password
from server.app.database import get_db
from server.app.models import User
from server.app.schemas import LoginRequest, TokenResponse, UserOut

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(request: Request, credentials: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticates username and password against users table.
    Rate limited to 5 attempts per minute per IP address.
    """
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Issue JWT token with subject and role claims
    token_data = {"sub": user.username, "role": user.role}
    access_token = create_access_token(data=token_data)

    return TokenResponse(
        access_token=access_token, token_type="bearer", role=user.role, username=user.username
    )


@router.get("/me", response_model=UserOut)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Returns the authenticated user's profile and assigned role."""
    return current_user
