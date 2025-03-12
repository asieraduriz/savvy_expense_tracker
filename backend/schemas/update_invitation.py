from pydantic import BaseModel

from backend.models.base import InvitationStatus

class UpdateInvitation(BaseModel):
    status: InvitationStatus