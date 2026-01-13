"""
Agent State Models
Defines the state structure for the agentic medical assistant.
"""
from typing import Optional, Literal
from pydantic import BaseModel, Field


class AgentState(BaseModel):
    """
    Agent state that tracks conversation context, severity, location, and language.
    """
    user_input: str
    severity: Literal["critical", "serious", "moderate", "mild"] = "mild"
    lat: Optional[float] = Field(None, ge=-90, le=90, description="Latitude")
    lon: Optional[float] = Field(None, ge=-180, le=180, description="Longitude")
    location_source: Optional[Literal["gps", "ip", "manual"]] = None
    address: Optional[str] = None
    action: Optional[str] = None
    session_id: Optional[str] = None
    # Multilingual support
    user_language: Optional[str] = Field(None, description="ISO language code (e.g., 'en', 'hi', 'ta')")
    original_input: Optional[str] = Field(None, description="Original user input in their language")
    normalized_input: Optional[str] = Field(None, description="English translation of user input")
    emergency: Optional[bool] = Field(False, description="Emergency flag for special handling")

    class Config:
        json_schema_extra = {
            "example": {
                "user_input": "my father has chest pain",
                "severity": "critical",
                "lat": 28.5355,
                "lon": 77.3910,
                "location_source": "gps",
                "action": "emergency_hospital_lookup"
            }
        }
