from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Apply in routes:
# @router.post("/login")
# @limiter.limit("5/minute")   ← 5 login attempts per minute per IP
# async def login(request: Request, ...):