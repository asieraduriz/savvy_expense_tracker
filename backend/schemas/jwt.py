from pydantic import BaseModel
import datetime

class JWTPayload(BaseModel):
    sub: str
    exp: datetime.datetime
    iat: datetime.datetime