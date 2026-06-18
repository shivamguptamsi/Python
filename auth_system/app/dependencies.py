from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis
from app.auth import decode_token
from app.models import User, UserRole, async_session   # ← import async_session here
from config import settings

bearer = HTTPBearer()
redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

async def get_db():
    async with async_session() as session:
        yield session

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if await redis_client.get(f"blocklist:{token}"):
        raise credentials_exception

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise credentials_exception

    user = await db.get(User, payload["sub"])
    if not user or not user.is_active:
        raise credentials_exception
    return user

def require_role(role: UserRole):
    def checker(current_user: User = Depends(get_current_user)):
        if current_user.role != role:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return checker

require_admin = require_role(UserRole.admin)