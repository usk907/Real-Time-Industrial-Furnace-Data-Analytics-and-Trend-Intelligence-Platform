"""
IEIP Authentication & User Management Router
Endpoints:
  - POST /auth/login
  - POST /auth/logout
  - POST /auth/forgot-password
  - POST /auth/reset-password
  - GET  /auth/me
  - GET  /users
  - POST /users
  - PUT  /users/{user_id}
  - DELETE /users/{user_id}
"""
import os
from datetime import timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.auth import (
    create_access_token,
    verify_password,
    get_password_hash,
    get_current_user,
    RoleChecker,
    blacklist_token
)
from backend.app.models import User, Role
from backend.app.schemas import (
    UserLogin,
    Token,
    UserCreate,
    UserUpdate,
    UserOut
)
from backend.app.services.kpi_engine import log_audit

router = APIRouter(tags=["Authentication & Users"])


class ResetPasswordPayload(BaseModel):
    token: str
    new_password: str


@router.post("/auth/login", response_model=Token)
def login(payload: UserLogin, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    role = db.query(Role).filter(Role.id == user.role_id).first()
    permissions = role.permissions if role else []

    token_data = {"sub": user.username, "role": role.name if role else "Viewer"}
    access_token = create_access_token(data=token_data)

    client_host = request.client.host if request.client else "127.0.0.1"
    log_audit(db, "LOGIN", f"User {user.username} logged in successfully", user.id, client_host)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": role.name if role else "Viewer",
        "permissions": permissions
    }


@router.post("/auth/logout")
def logout(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        blacklist_token(token)
    client_host = request.client.host if request.client else "127.0.0.1"
    log_audit(db, "LOGOUT", f"User {user.username} logged out", user.id, client_host)
    return {"status": "success", "message": "Successfully logged out"}


@router.post("/auth/forgot-password")
def forgot_password(payload: dict, db: Session = Depends(get_db)):
    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return {"status": "success", "message": "Password reset token sent to your email"}

    reset_token = create_access_token(data={"sub": user.username, "action": "reset-password"}, expires_delta=timedelta(minutes=15))
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
    reset_link = f"{frontend_url}/reset-password?token={reset_token}"
    print(f"[PASSWORD RESET LINK]: {reset_link}")

    return {"status": "success", "message": "Password reset token sent to your email", "reset_link_mock": reset_link}


@router.post("/auth/reset-password")
def reset_password(payload: ResetPasswordPayload, db: Session = Depends(get_db)):
    try:
        decoded = jwt.decode(payload.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    if decoded.get("action") != "reset-password":
        raise HTTPException(status_code=400, detail="Invalid reset token")

    username = decoded.get("sub")
    if not username:
        raise HTTPException(status_code=400, detail="Invalid reset token")

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = get_password_hash(payload.new_password)
    db.commit()
    return {"status": "success", "message": "Password updated successfully"}


@router.get("/auth/me")
def get_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.id == user.role_id).first()
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": role.name if role else "Viewer",
        "permissions": role.permissions if role else []
    }


@router.get("/users", response_model=List[UserOut])
def get_users(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin"])(user, db)
    return db.query(User).all()


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin"])(user, db)
    existing_user = db.query(User).filter((User.username == payload.username) | (User.email == payload.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    new_user = User(
        username=payload.username,
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        role_id=payload.role_id,
        is_active=payload.is_active
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    client_host = request.client.host if request.client else "127.0.0.1"
    log_audit(db, "CREATE_USER", f"Created user {new_user.username}", user.id, client_host)
    return new_user


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdate, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin"])(user, db)
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.email is not None:
        target.email = payload.email
    if payload.role_id is not None:
        target.role_id = payload.role_id
    if payload.is_active is not None:
        target.is_active = payload.is_active
    if payload.password is not None:
        target.password_hash = get_password_hash(payload.password)

    db.commit()
    db.refresh(target)
    client_host = request.client.host if request.client else "127.0.0.1"
    log_audit(db, "UPDATE_USER", f"Updated user {target.username}", user.id, client_host)
    return target


@router.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
def delete_user(user_id: int, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin"])(user, db)
    if user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own admin account")

    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    username = target.username
    db.delete(target)
    db.commit()
    client_host = request.client.host if request.client else "127.0.0.1"
    log_audit(db, "DELETE_USER", f"Deleted user {username}", user.id, client_host)
    return {"status": "success", "message": f"Deleted user {username}"}
