from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from .auth_handler import decode_token

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        if credentials:
            try:
                payload = decode_token(credentials.credentials)
                return payload
            except JWTError:
                raise HTTPException(status_code=403, detail="Invalid token")
        raise HTTPException(status_code=403, detail="Invalid authorization code")

