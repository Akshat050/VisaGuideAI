from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    message: str

    # Keep optional so frontend doesn't accidentally lock everything to us_b1b2
    visa_type: Optional[str] = None

    # Route context (preferred)
    profile_id: Optional[str] = None
    source_country: Optional[str] = None
    destination_country: Optional[str] = None

    # Extra user context (optional but useful)
    residence_country: Optional[str] = None
    employment_status: Optional[str] = None

    # Session
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    source: str
    cached: bool

    # Optional for safety; backend can return "" if not relevant
    visa_type: Optional[str] = None
