from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from ..services.auth.auth_service import SECRET_KEY, ALGORITHM

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = None):
    if not credentials:
        raise HTTPException(status_code=401, detail="Token required")
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

class AuthMiddleware:
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        # Add authentication middleware logic here
        await self.app(scope, receive, send)
