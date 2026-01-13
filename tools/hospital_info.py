"""
Hospital Information Module
Provides additional hospital information like operating hours, services, etc.
"""
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, time
import json

logger = logging.getLogger(__name__)

# Sample operating hours (in production, this would come from database)
DEFAULT_OPERATING_HOURS = {
    "monday": {"open": "09:00", "close": "18:00", "closed": False},
    "tuesday": {"open": "09:00", "close": "18:00", "closed": False},
    "wednesday": {"open": "09:00", "close": "18:00", "closed": False},
    "thursday": {"open": "09:00", "close": "18:00", "closed": False},
    "friday": {"open": "09:00", "close": "18:00", "closed": False},
    "saturday": {"open": "09:00", "close": "14:00", "closed": False},
    "sunday": {"closed": True}
}

EMERGENCY_HOURS = {
    "monday": {"open": "00:00", "close": "23:59", "closed": False},
    "tuesday": {"open": "00:00", "close": "23:59", "closed": False},
    "wednesday": {"open": "00:00", "close": "23:59", "closed": False},
    "thursday": {"open": "00:00", "close": "23:59", "closed": False},
    "friday": {"open": "00:00", "close": "23:59", "closed": False},
    "saturday": {"open": "00:00", "close": "23:59", "closed": False},
    "sunday": {"open": "00:00", "close": "23:59", "closed": False}
}


def get_operating_hours(hospital_type: str, emergency_services: bool = False) -> Dict[str, Any]:
    """
    Get operating hours for a hospital.
    
    Args:
        hospital_type: Type of hospital ('emergency', 'general', 'specialty')
        emergency_services: Whether hospital has 24/7 emergency services
    
    Returns:
        Dict with operating hours for each day
    """
    if emergency_services or hospital_type == "emergency":
        return EMERGENCY_HOURS.copy()
    return DEFAULT_OPERATING_HOURS.copy()


def is_hospital_open(hospital_type: str, emergency_services: bool = False) -> Dict[str, Any]:
    """
    Check if hospital is currently open.
    
    Args:
        hospital_type: Type of hospital
        emergency_services: Whether hospital has 24/7 emergency services
    
    Returns:
        Dict with 'is_open', 'current_status', and 'next_open_time'
    """
    if emergency_services or hospital_type == "emergency":
        return {
            "is_open": True,
            "current_status": "Open 24/7",
            "next_open_time": None,
            "emergency_available": True
        }
    
    hours = get_operating_hours(hospital_type, emergency_services)
    now = datetime.now()
    current_day = now.strftime("%A").lower()
    current_time = now.time()
    
    # Check today's hours
    today_hours = hours.get(current_day, {})
    
    if today_hours.get("closed", False):
        # Find next open day
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        current_idx = days.index(current_day)
        
        for i in range(1, 8):
            next_day_idx = (current_idx + i) % 7
            next_day = days[next_day_idx]
            next_hours = hours.get(next_day, {})
            
            if not next_hours.get("closed", False):
                return {
                    "is_open": False,
                    "current_status": "Closed",
                    "next_open_time": f"{next_day.capitalize()} {next_hours.get('open', '09:00')}",
                    "emergency_available": False
                }
        
        return {
            "is_open": False,
            "current_status": "Closed",
            "next_open_time": "Check with hospital",
            "emergency_available": False
        }
    
    # Parse open/close times
    try:
        open_time_str = today_hours.get("open", "09:00")
        close_time_str = today_hours.get("close", "18:00")
        
        open_time = datetime.strptime(open_time_str, "%H:%M").time()
        close_time = datetime.strptime(close_time_str, "%H:%M").time()
        
        is_open = open_time <= current_time <= close_time
        
        if is_open:
            return {
                "is_open": True,
                "current_status": f"Open until {close_time_str}",
                "next_open_time": None,
                "emergency_available": False
            }
        else:
            if current_time < open_time:
                return {
                    "is_open": False,
                    "current_status": f"Opens at {open_time_str}",
                    "next_open_time": f"Today at {open_time_str}",
                    "emergency_available": False
                }
            else:
                # Find next open day
                days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
                current_idx = days.index(current_day)
                
                for i in range(1, 8):
                    next_day_idx = (current_idx + i) % 7
                    next_day = days[next_day_idx]
                    next_hours = hours.get(next_day, {})
                    
                    if not next_hours.get("closed", False):
                        return {
                            "is_open": False,
                            "current_status": f"Closed (closes at {close_time_str})",
                            "next_open_time": f"{next_day.capitalize()} {next_hours.get('open', '09:00')}",
                            "emergency_available": False
                        }
                
                return {
                    "is_open": False,
                    "current_status": "Closed",
                    "next_open_time": "Check with hospital",
                    "emergency_available": False
                }
                
    except Exception as e:
        logger.error(f"Error parsing hours: {e}")
        return {
            "is_open": True,  # Default to open if parsing fails
            "current_status": "Check with hospital",
            "next_open_time": None,
            "emergency_available": False
        }


def get_hospital_services(hospital_type: str, specialty: Optional[str] = None) -> List[str]:
    """
    Get list of services available at hospital.
    
    Args:
        hospital_type: Type of hospital
        specialty: Medical specialty if applicable
    
    Returns:
        List of available services
    """
    base_services = ["General Consultation", "Pharmacy", "Laboratory"]
    
    if hospital_type == "emergency":
        base_services.extend([
            "Emergency Services",
            "24/7 Emergency Care",
            "Ambulance Service",
            "Trauma Care",
            "ICU"
        ])
    
    if specialty:
        specialty_services = {
            "cardiology": ["ECG", "Echocardiography", "Cardiac Catheterization", "Cardiac Surgery"],
            "orthopedics": ["X-Ray", "MRI", "Orthopedic Surgery", "Physical Therapy"],
            "neurology": ["EEG", "CT Scan", "Neurological Consultation", "Neurosurgery"],
            "gastroenterology": ["Endoscopy", "Colonoscopy", "Gastrointestinal Surgery"],
            "dermatology": ["Skin Biopsy", "Dermatological Procedures", "Cosmetic Dermatology"],
            "ophthalmology": ["Eye Examination", "Cataract Surgery", "Retinal Procedures"],
            "ent": ["Audiometry", "ENT Surgery", "Hearing Tests"],
            "urology": ["Urological Procedures", "Kidney Stone Treatment", "Urological Surgery"],
            "gynecology": ["Gynecological Consultation", "Ultrasound", "Obstetric Care"],
            "pediatrics": ["Pediatric Consultation", "Vaccination", "Child Health Services"],
            "psychiatry": ["Psychiatric Consultation", "Counseling", "Mental Health Services"],
            "endocrinology": ["Diabetes Management", "Thyroid Treatment", "Hormone Therapy"],
            "pulmonology": ["Pulmonary Function Tests", "Respiratory Therapy", "Lung Procedures"]
        }
        
        if specialty.lower() in specialty_services:
            base_services.extend(specialty_services[specialty.lower()])
    
    return base_services


def format_hospital_info(
    hospital: Dict[str, Any],
    include_directions: bool = False,
    start_lat: Optional[float] = None,
    start_lon: Optional[float] = None
) -> Dict[str, Any]:
    """
    Format comprehensive hospital information.
    
    Args:
        hospital: Hospital dict from database
        include_directions: Whether to include directions
        start_lat: Starting latitude for directions
        start_lon: Starting longitude for directions
    
    Returns:
        Enhanced hospital dict with additional information
    """
    enhanced = hospital.copy()
    
    # Add operating status
    status = is_hospital_open(
        hospital.get("type", "general"),
        hospital.get("emergency_services", False)
    )
    enhanced["operating_status"] = status
    
    # Add services
    services = get_hospital_services(
        hospital.get("type", "general"),
        hospital.get("specialty")
    )
    enhanced["services"] = services
    
    # Add operating hours
    hours = get_operating_hours(
        hospital.get("type", "general"),
        hospital.get("emergency_services", False)
    )
    enhanced["operating_hours"] = hours
    
    # Add Google Maps URL
    if hospital.get("lat") and hospital.get("lon"):
        try:
            from tools.directions import get_google_maps_url
            enhanced["maps_url"] = get_google_maps_url(
                hospital["lat"],
                hospital["lon"],
                hospital.get("name", "")
            )
        except ImportError:
            # Fallback if directions module not available
            enhanced["maps_url"] = f"https://www.google.com/maps?q={hospital['lat']},{hospital['lon']}"
    
    # Add directions if requested
    if include_directions and start_lat and start_lon:
        try:
            from tools.directions import get_directions
            directions = get_directions(
                start_lat,
                start_lon,
                hospital.get("lat"),
                hospital.get("lon")
            )
            if directions:
                enhanced["directions"] = directions
        except ImportError:
            pass
    
    return enhanced
