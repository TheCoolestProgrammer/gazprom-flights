from pydantic import BaseModel
from src.models.passenger import RequestStatus

class StatusUpdate(BaseModel):
    request_status: RequestStatus