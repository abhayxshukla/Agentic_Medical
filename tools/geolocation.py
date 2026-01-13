"""
Geolocation Tools
Provides functions for location detection and geocoding.
Uses Nominatim (OpenStreetMap) for geocoding - no API key required.
"""
import logging
import time
from typing import Optional, Dict, Tuple, Any
from geopy.geocoders import Nominatim  # type: ignore[import]
from geopy.exc import GeocoderTimedOut, GeocoderServiceError  # type: ignore[import]
import requests
from fastapi import Request

logger = logging.getLogger(__name__)

# Initialize Nominatim geocoder
geocoder = Nominatim(user_agent="medical_assistant/1.0")


def get_location_from_gps(lat: float, lon: float) -> Dict[str, Any]:
    """
    Validate and return GPS coordinates.
    
    Args:
        lat: Latitude (-90 to 90)
        lon: Longitude (-180 to 180)
    
    Returns:
        Dict with validated coordinates and source
    """
    try:
        # Validate coordinates
        if not (-90 <= lat <= 90):
            raise ValueError(f"Invalid latitude: {lat}")
        if not (-180 <= lon <= 180):
            raise ValueError(f"Invalid longitude: {lon}")
        
        logger.info(f"GPS location received: ({lat}, {lon})")
        
        return {
            "lat": lat,
            "lon": lon,
            "source": "gps",
            "valid": True
        }
    except Exception as e:
        logger.error(f"Error validating GPS coordinates: {e}")
        return {
            "lat": None,
            "lon": None,
            "source": "gps",
            "valid": False,
            "error": str(e)
        }


def geocode_address(address: str, max_retries: int = 3) -> Optional[Dict[str, Any]]:
    """
    Convert address string to latitude/longitude using Nominatim.
    
    Args:
        address: Address string (e.g., "Delhi, India" or "123 Main St, Mumbai")
        max_retries: Maximum retry attempts for geocoding
    
    Returns:
        Dict with lat, lon, and formatted address, or None if failed
    """
    if not address or not address.strip():
        logger.warning("Empty address provided for geocoding")
        return None
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Geocoding address (attempt {attempt + 1}/{max_retries}): {address}")
            
            # Use geopy with timeout
            location = geocoder.geocode(
                address,
                timeout=10,
                exactly_one=True
            )
            
            if location:
                result = {
                    "lat": location.latitude,
                    "lon": location.longitude,
                    "formatted_address": location.address,
                    "source": "manual",
                    "valid": True
                }
                logger.info(f"Successfully geocoded: {address} -> ({result['lat']}, {result['lon']})")
                return result
            else:
                logger.warning(f"Could not geocode address: {address}")
                return None
                
        except GeocoderTimedOut:
            logger.warning(f"Geocoding timeout (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(1)  # Wait before retry
            continue
        except GeocoderServiceError as e:
            logger.error(f"Geocoding service error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during geocoding: {e}")
            return None
    
    logger.error(f"Failed to geocode address after {max_retries} attempts: {address}")
    return None


def get_location_from_ip(request: Request) -> Optional[Dict[str, Any]]:
    """
    Estimate location from IP address using a free geolocation service.
    
    Note: This is approximate and should only be used as a fallback.
    For production, consider using a more reliable IP geolocation service.
    
    Args:
        request: FastAPI Request object
    
    Returns:
        Dict with estimated lat, lon, or None if failed
    """
    try:
        # Get client IP
        client_ip = request.client.host if request.client else None
        
        # Handle forwarded headers (common in production)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        if not client_ip or client_ip == "127.0.0.1":
            logger.warning("Cannot geolocate localhost IP")
            return None
        
        logger.info(f"Attempting IP geolocation for: {client_ip}")
        
        # Use ip-api.com (free, no API key required, rate limited)
        # Alternative: ipapi.co, ipgeolocation.io
        response = requests.get(
            f"http://ip-api.com/json/{client_ip}",
            timeout=5,
            params={"fields": "status,lat,lon,city,country"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                result = {
                    "lat": data.get("lat"),
                    "lon": data.get("lon"),
                    "city": data.get("city"),
                    "country": data.get("country"),
                    "source": "ip",
                    "valid": True,
                    "accuracy": "low"  # IP geolocation is approximate
                }
                logger.info(f"IP geolocation successful: ({result['lat']}, {result['lon']})")
                return result
        
        logger.warning(f"IP geolocation failed for {client_ip}")
        return None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during IP geolocation: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during IP geolocation: {e}")
        return None


def reverse_geocode(lat: float, lon: float) -> Optional[str]:
    """
    Convert coordinates to address string.
    
    Args:
        lat: Latitude
        lon: Longitude
    
    Returns:
        Formatted address string or None
    """
    try:
        location = geocoder.reverse((lat, lon), timeout=10, exactly_one=True)
        if location:
            return location.address
        return None
    except Exception as e:
        logger.error(f"Reverse geocoding failed: {e}")
        return None
