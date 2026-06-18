from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, UTC
from app import models, auth
from app import email as mail_service
from app.dependencies import get_db, get_current_user, redis_client
from app.schemas import RegisterRequest, LoginRequest, TokenResponse
from config import settings

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer()   # ← this was missing

# ── Register ───────────────────────────────────────────
@router.post("/register", status_code=201)
async def register(
    data: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    if not auth.validate_password_strength(data.password):
        raise HTTPException(400, "Password too weak")

    existing = await db.execute(select(models.User).where(models.User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Email already registered")

    token = auth.generate_secure_token()
    user = models.User(
        email=data.email,
        hashed_password=auth.hash_password(data.password),
        full_name=data.full_name,
        verify_token=token,
        verify_token_expires=datetime.now(UTC) + timedelta(hours=settings.EMAIL_VERIFY_EXPIRE_HOURS),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    background_tasks.add_task(mail_service.send_verification_email, user.email, token)

    # Return token so you can verify manually during testing
    return {
        "message": "Account created. Check your email to verify.",
        "debug_verify_token": token   # remove this in production!
    }
# ── Verify Email ───────────────────────────────────────
@router.get("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).where(models.User.verify_token == token))
    user = result.scalar_one_or_none()

    if not user or not user.verify_token_expires:
        raise HTTPException(400, "Invalid token")
    if datetime.now(UTC) > user.verify_token_expires.replace(tzinfo=UTC):
        raise HTTPException(400, "Token expired. Request a new verification email.")

    user.is_verified = True
    user.is_active = True
    user.verify_token = None
    user.verify_token_expires = None
    await db.commit()
    return {"message": "Email verified. You can now log in."}

# ── Login ──────────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).where(models.User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not auth.verify_password(data.password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")
    if not user.is_verified:
        raise HTTPException(403, "Email not verified")

    payload = {"sub": user.id, "role": user.role}
    return {
        "access_token": auth.create_access_token(payload),
        "refresh_token": auth.create_refresh_token(payload),
        "token_type": "bearer",
    }

# ── Refresh Token ──────────────────────────────────────
@router.post("/refresh", response_model=TokenResponse)
async def refresh(refresh_token: str, db: AsyncSession = Depends(get_db)):
    payload = auth.decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(401, "Invalid refresh token")

    user = await db.get(models.User, payload["sub"])
    if not user or not user.is_active:
        raise HTTPException(401, "User not found")

    new_payload = {"sub": user.id, "role": user.role}
    return {
        "access_token": auth.create_access_token(new_payload),
        "refresh_token": auth.create_refresh_token(new_payload),
        "token_type": "bearer",
    }

# ── Logout ─────────────────────────────────────────────
@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: models.User = Depends(get_current_user),
):
    token = credentials.credentials
    payload = auth.decode_token(token)
    ttl = int(payload["exp"] - datetime.now(UTC).timestamp())
    if ttl > 0:
        await redis_client.setex(f"blocklist:{token}", ttl, "1")
    return {"message": "Logged out"}

# ── Forgot Password ────────────────────────────────────
@router.post("/forgot-password")
async def forgot_password(
    email: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(models.User).where(models.User.email == email))
    user = result.scalar_one_or_none()
    if user and user.is_verified:
        token = auth.generate_secure_token()
        user.reset_token = token
        user.reset_token_expires = datetime.now(UTC) + timedelta(hours=settings.RESET_TOKEN_EXPIRE_HOURS)
        await db.commit()
        background_tasks.add_task(mail_service.send_password_reset_email, email, token)
    return {"message": "If that email exists, a reset link has been sent."}

# ── Reset Password ─────────────────────────────────────
@router.post("/reset-password")
async def reset_password(token: str, new_password: str, db: AsyncSession = Depends(get_db)):
    if not auth.validate_password_strength(new_password):
        raise HTTPException(400, "Password too weak")

    result = await db.execute(select(models.User).where(models.User.reset_token == token))
    user = result.scalar_one_or_none()
    if not user or datetime.now(UTC) > user.reset_token_expires.replace(tzinfo=UTC):
        raise HTTPException(400, "Invalid or expired reset token")

    user.hashed_password = auth.hash_password(new_password)
    user.reset_token = None
    user.reset_token_expires = None
    await db.commit()
    return {"message": "Password updated. You can now log in."}

# ── Get Current User ───────────────────────────────────
@router.get("/me")
async def get_me(current_user: models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "is_verified": current_user.is_verified,
    }