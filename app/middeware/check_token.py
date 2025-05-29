from fastapi import Request
from fastapi.responses import JSONResponse
from jose import jwt, JWTError, ExpiredSignatureError
from app.core.config import settings


async def check_token_middleware(request: Request, call_next):
    # Cho phép các route auth hoặc public không cần token
    if (
        request.url.path.startswith("/login")
        or request.url.path.startswith("/docs")
        or request.url.path.startswith("/openapi")
        or request.url.path.startswith("/realtime")
        or request.url.path.startswith("/")
        or request.url.path.startswith("/user/disconnect")
    ):
        return await call_next(request)

    token = request.headers.get("Authorization")
    if token is None:
        return JSONResponse(status_code=401, content={"detail": "Token missing"})

    try:
        # Xử lý token dạng "Bearer <token>"
        if not token.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid token format. Use 'Bearer <token>'"}
            )
        token = token.split(" ")[1]
        
        # Decode token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        # Kiểm tra token_type (nếu cần)
        if payload.get("token_type") != "access":
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid token type"}
            )

    except ExpiredSignatureError:
        return JSONResponse(
            status_code=401,
            content={"detail": "Token expired"}
        )
    except JWTError:
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid token"}
        )
    except IndexError:
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid token format"}
        )
        
    response = await call_next(request)
    return response
