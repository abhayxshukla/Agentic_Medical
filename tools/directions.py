"""
Directions and Navigation
Provides turn-by-turn directions to hospitals.
"""
import logging
from typing import Dict, Optional, List, Any
import urllib.parse

logger = logging.getLogger(__name__)


def get_directions_url(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    mode: str = "driving"
) -> str:
    """
    Generate directions URL for various map services.
    
    Args:
        start_lat: Starting latitude
        start_lon: Starting longitude
        end_lat: Destination latitude
        end_lon: Destination longitude
        mode: Travel mode (driving, walking, transit)
        
    Returns:
        URL for directions
    """
    # Google Maps URL
    google_url = (
        f"https://www.google.com/maps/dir/"
        f"{start_lat},{start_lon}/"
        f"{end_lat},{end_lon}/"
        f"@{end_lat},{end_lon},15z"
    )
    
    # Alternative: OpenStreetMap with OSRM
    # osrm_url = f"http://router.project-osrm.org/route/v1/{mode}/{start_lon},{start_lat};{end_lon},{end_lat}"
    
    return google_url


def get_directions_info(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    mode: str = "driving"
) -> Dict[str, Any]:
    """
    Get directions information (distance, estimated time).
    
    Args:
        start_lat: Starting latitude
        start_lon: Starting longitude
        end_lat: Destination latitude
        end_lon: Destination longitude
        mode: Travel mode
        
    Returns:
        Directions information
    """
    # Calculate straight-line distance (Haversine)
    import math
    
    R = 6371  # Earth radius in km
    
    dlat = math.radians(end_lat - start_lat)
    dlon = math.radians(end_lon - start_lon)
    
    a = (
        math.sin(dlat / 2) ** 2 +
        math.cos(math.radians(start_lat)) *
        math.cos(math.radians(end_lat)) *
        math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    distance_km = R * c
    
    # Estimate time based on mode
    if mode == "walking":
        estimated_minutes = int(distance_km * 12)  # ~5 km/h walking speed
    elif mode == "transit":
        estimated_minutes = int(distance_km * 3)  # ~20 km/h average transit
    else:  # driving
        estimated_minutes = int(distance_km * 1.5)  # ~40 km/h average city speed
    
    return {
        "distance_km": round(distance_km, 2),
        "estimated_time_minutes": estimated_minutes,
        "estimated_time_formatted": f"{estimated_minutes} min",
        "mode": mode,
        "directions_url": get_directions_url(start_lat, start_lon, end_lat, end_lon, mode)
    }
