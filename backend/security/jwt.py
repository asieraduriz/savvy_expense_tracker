from typing import Dict, Any, Optional
from fastapi import HTTPException
import jwt
import datetime

from backend.schemas.jwt import JWTPayload

SECRET_KEY = "636b56b04687f1789f464d4c648e255ee4a9b22d6ecbdd599fb0ca2c701e4ccc"

def generate_jwt(user_id: str) -> str:
    """Generates a JWT with user ID."""
    now = datetime.datetime.now(datetime.UTC)
    payload: JWTPayload = {
        'sub': str(user_id),
        'exp': now + datetime.timedelta(minutes=30),
        'iat': now
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

def _decode_jwt(token: str) -> Optional[JWTPayload]:
    """Decodes a JWT and returns the payload or None if invalid."""

    if not token.startswith("JWT "):
        #raise HTTPException(status_code=401, detail="Invalid authorization scheme")
        return None

    token = token[4:]
    try:
        decodedToken: JWTPayload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return JWTPayload(**decodedToken)
    except jwt.ExpiredSignatureError:
        print("Token has expired")
        return None
    except jwt.InvalidTokenError:
        print("Invalid token")
        return None
    except Exception as e:
        print("Unknown error", e)
        return None
    
def get_user_from_auth(token:str) -> Optional[str]:
    payload = _decode_jwt(token)
    if not payload:
        return HTTPException({"message": "Invalid token"}, status_code=401)

    return payload.sub