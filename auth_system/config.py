from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./auth.db"
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    EMAIL_VERIFY_EXPIRE_HOURS: int = 24
    RESET_TOKEN_EXPIRE_HOURS: int = 1

    MAIL_USERNAME: str = "theshivam.7700@gmail.com"
    MAIL_PASSWORD: str = "yhwtpxxjsugiaqwq"
    MAIL_FROM: str = "noreply@yourapp.com"
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 587

    REDIS_URL: str = "redis://localhost:6379"
    FRONTEND_URL: str = "http://localhost:3000"

    class Config:
        env_file = ".env"

settings = Settings()