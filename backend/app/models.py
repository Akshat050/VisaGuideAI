from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ChatRequest(BaseModel):
    message: str
    visa_type: str = "us_b1b2"
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    source: str
    cached: bool
    visa_type: str
