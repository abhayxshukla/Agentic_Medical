"""
Geolocation API Routes
FastAPI endpoints for agentic geolocation-based medical assistance.
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from agents.geo_agent import GeoAgent
from tools.hospital_details import get_hospital_details, search_hospitals_with_filters
from tools.directions import get_directions_info, get_directions_url

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/agent", tags=["agent"])

# Initialize geo agent
geo_agent = GeoAgent()


class GeolocationRequest(BaseModel):
    """Request model for geolocation endpoint."""
    user_input: str = Field(..., description="User's symptom description or medical query")
    location: Optional[dict] = Field(
        None,
        description="Location data. Can include 'lat', 'lon', or 'address'"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_input": "my father has chest pain",
                "location": {
                    "lat": 28.5355,
                    "lon": 77.3910
                }
            }
        }


class GeolocationResponse(BaseModel):
    """Response model for geolocation endpoint."""
    severity: str = Field(..., description="'critical' or 'non_critical'")
    action: str = Field(..., description="Action taken by agent")
    message: str = Field(..., description="Response message for user")
    hospitals: list = Field(default_factory=list, description="List of nearby hospitals")
    location: Optional[dict] = Field(None, description="Resolved location data")
    requires_location: bool = Field(False, description="Whether location is required")
    disclaimer: Optional[str] = Field(None, description="Safety disclaimer for critical cases")
    emergency_number: Optional[str] = Field(None, description="Emergency contact number")
    suggested_specialty: Optional[str] = Field(None, description="Suggested medical specialty based on symptoms")
    specialty_display: Optional[str] = Field(None, description="Human-readable specialty name")


@router.post("/geolocation", response_model=GeolocationResponse)
async def geolocation_endpoint(
    request_data: GeolocationRequest,
    request: Request
):
    """
    Main geolocation endpoint for agentic medical assistance.
    
    The agent will:
    1. Classify symptom severity (critical/non_critical)
    2. Resolve location from GPS, address, or IP
    3. Automatically request location if critical and missing
    4. Find nearest emergency hospitals for critical cases
    5. Find specialists for non-critical cases
    
    Args:
        request_data: User input and optional location
        request: FastAPI Request object (for IP geolocation)
    
    Returns:
        GeolocationResponse with severity, action, hospitals, and message
    """
    try:
        logger.info(f"Processing geolocation request: {request_data.user_input[:50]}...")
        
        # Process request through geo agent
        result = await geo_agent.process_request(
            user_input=request_data.user_input,
            location=request_data.location,
            request=request
        )
        
        # Handle errors
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Build response
        response = GeolocationResponse(
            severity=result.get("severity", "non_critical"),
            action=result.get("action", "general_consultation"),
            message=result.get("message", ""),
            hospitals=result.get("hospitals", []),
            location=result.get("location"),
            requires_location=result.get("requires_location", False),
            disclaimer=result.get("disclaimer"),
            emergency_number=result.get("emergency_number"),
            suggested_specialty=result.get("suggested_specialty"),
            specialty_display=result.get("specialty_display")
        )
        
        logger.info(f"Geolocation request processed: {response.action}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in geolocation endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/hospital/{hospital_id}")
async def get_hospital_details_endpoint(hospital_id: int):
    """Get detailed information about a specific hospital."""
    try:
        hospital = get_hospital_details(hospital_id)
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        return hospital
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting hospital details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/directions")
async def get_directions(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    mode: str = "driving"
):
    """Get directions from one location to another."""
    try:
        if mode not in ["driving", "walking", "transit"]:
            mode = "driving"
        
        directions = get_directions_info(start_lat, start_lon, end_lat, end_lon, mode)
        return directions
    except Exception as e:
        logger.error(f"Error getting directions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def advanced_hospital_search(
    lat: float,
    lon: float,
    radius_km: float = 5.0,
    hospital_type: Optional[str] = None,
    specialty: Optional[str] = None,
    min_rating: Optional[float] = None,
    languages: Optional[List[str]] = None,
    limit: int = 10
):
    """Advanced hospital search with multiple filters."""
    try:
        hospitals = search_hospitals_with_filters(
            lat=lat,
            lon=lon,
            radius_km=radius_km,
            hospital_type=hospital_type,
            specialty=specialty,
            min_rating=min_rating,
            languages=languages,
            limit=limit
        )
        return {
            "hospitals": hospitals,
            "count": len(hospitals),
            "filters_applied": {
                "radius_km": radius_km,
                "hospital_type": hospital_type,
                "specialty": specialty,
                "min_rating": min_rating,
                "languages": languages
            }
        }
    except Exception as e:
        logger.error(f"Error in advanced search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class GeocodeRequest(BaseModel):
    """Request model for geocoding endpoint."""
    address: str = Field(..., description="Address to geocode")


@router.post("/geocode")
async def geocode_endpoint(request_data: GeocodeRequest):
    """Geocode an address to coordinates."""
    try:
        from tools.geolocation import geocode_address
        result = geocode_address(request_data.address)
        if result and result.get("valid"):
            return {
                "lat": result["lat"],
                "lon": result["lon"],
                "address": result.get("formatted_address", request_data.address),
                "success": True
            }
        else:
            raise HTTPException(status_code=404, detail="Could not geocode address")
    except Exception as e:
        logger.error(f"Error geocoding address: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def agent_health():
    """Health check for agent endpoints."""
    return {
        "status": "healthy",
        "service": "Geolocation Agent API",
        "version": "1.0.0"
    }
