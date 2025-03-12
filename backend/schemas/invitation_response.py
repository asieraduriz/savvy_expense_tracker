from pydantic import BaseModel


class InvitationResponse(BaseModel):
    id: str