from fastapi import Request
from fastapi.responses import JSONResponse
from jose import jwt, JWTError
from app.core.config import settings

async def check_token_middleware(request: Request, call_next):
    # Cho phép các route auth hoặc public không cần token
    if request.url.path.startswith("/auth") or request.url.path.startswith("/public"):
        return await call_next(request)

    token = request.headers.get("Authorization")
    if token is None:
        return JSONResponse(status_code=401, content={"detail": "Token missing"})

    try:
        jwt.decode(token.split(" ")[1], settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except (JWTError, IndexError):
        return JSONResponse(status_code=401, content={"detail": "Invalid token"})

    response = await call_next(request)
    return response
