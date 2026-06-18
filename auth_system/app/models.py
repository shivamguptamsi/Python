from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.ext.asyncio import AsyncAttrs, create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, UTC
import uuid, enum
from config import settings

# ── Engine + Session ───────────────────────────────────
engine = create_async_engine(settings.DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# ── Base ───────────────────────────────────────────────
class Base(AsyncAttrs, DeclarativeBase):
    pass

# ── Enums ──────────────────────────────────────────────
class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"

# ── User Model ─────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id               = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email            = Column(String, unique=True, index=True, nullable=False)
    hashed_password  = Column(String, nullable=False)
    full_name        = Column(String)
    role             = Column(Enum(UserRole), default=UserRole.user)
    is_active        = Column(Boolean, default=False)
    is_verified      = Column(Boolean, default=False)
    created_at       = Column(DateTime, default=lambda: datetime.now(UTC))

    # Email verification
    verify_token         = Column(String, nullable=True)
    verify_token_expires = Column(DateTime, nullable=True)

    # Password reset
    reset_token          = Column(String, nullable=True)
    reset_token_expires  = Column(DateTime, nullable=True)