from datetime import datetime, timedelta, timezone
from typing import Optional, List
import os
import redis
import bcrypt
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models import User, Role

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)

# Token blacklist (Redis with in-memory fallback)
in_memory_blacklist: set[str] = set()
redis_client = None
try:
    redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True, socket_connect_timeout=0.5)
    redis_client.ping()
except Exception:
    redis_client = None

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    return jwt.encode({**data, "exp": expire}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def blacklist_token(token: str, expire_seconds: int = 28800):
    try:
        if redis_client:
            return redis_client.setex(f"blacklist:{token}", expire_seconds, "true")
    except Exception:
        pass
    in_memory_blacklist.add(token)

def is_token_blacklisted(token: str) -> bool:
    try:
        if redis_client and redis_client.exists(f"blacklist:{token}"):
            return True
    except Exception:
        pass
    return token in in_memory_blacklist

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token or is_token_blacklisted(token):
        raise unauthorized
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise unauthorized
    except JWTError:
        raise unauthorized
        
    user = db.query(User).filter(User.username == username, User.is_active.is_(True)).first()
    if not user:
        raise unauthorized
    return user

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        role = db.query(Role).filter(Role.id == user.role_id).first()
        if not role or role.name not in self.allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Insufficient privileges")
        return user
