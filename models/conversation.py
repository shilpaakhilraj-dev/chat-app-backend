from pydantic import BaseModel
from typing import List

class ParticipantModel(BaseModel):
    id: str
    name: str
    email: str

class ConversationModel(BaseModel):
    participants: List[ParticipantModel]