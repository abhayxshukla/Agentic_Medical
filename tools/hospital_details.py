"""
Hospital Details and Enhanced Information
Provides detailed hospital information, ratings, services, and availability.
"""
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy import text
from tools.hospitals import get_db_engine

logger = logging.getLogger(__name__)


def get_hospital_details(hospital_id: int) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a specific hospital.
    
    Args:
        hospital_id: Hospital ID
        
    Returns:
        Detailed hospital information or None
    """
    try:
        engine = get_db_engine()
        
        query = text("""
            SELECT 
                id,
                name,
                address,
                ST_Y(location::geometry) as lat,
                ST_X(location::geometry) as lon,
                type,
                specialty,
                phone,
                emergency_services,
                created_at
            FROM hospitals
            WHERE id = :hospital_id
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query, {"hospital_id": hospital_id})
            row = result.fetchone()
            
            if not row:
                return None
            
            hospital = {
                "id": row.id,
                "name": row.name,
                "address": row.address,
                "lat": float(row.lat),
                "lon": float(row.lon),
                "type": row.type,
                "specialty": row.specialty,
                "phone": row.phone,
                "emergency_services": row.emergency_services,
                "created_at": str(row.created_at) if row.created_at else None,
                # Additional fields (can be extended with ratings table)
                "rating": 4.5,  # Placeholder - would come from ratings table
                "reviews_count": 0,  # Placeholder
                "services": _get_hospital_services(row.type, row.specialty),
                "hours": _get_default_hours(row.type),
                "languages_spoken": _get_languages_spoken(row.type),
                "insurance_accepted": _get_insurance_info(),
                "amenities": _get_amenities(row.type)
            }
            
            return hospital
            
    except Exception as e:
        logger.error(f"Error getting hospital details: {e}")
        return None


def _get_hospital_services(hospital_type: str, specialty: Optional[str]) -> List[str]:
    """Get list of services offered by hospital."""
    services = {
        "emergency": [
            "Emergency Care",
            "Trauma Center",
            "Ambulance Service",
            "24/7 Emergency",
            "Critical Care",
            "Intensive Care Unit (ICU)"
        ],
        "specialty": {
            "cardiology": [
                "Cardiac Surgery",
                "Cardiac Catheterization",
                "Echocardiography",
                "Stress Testing",
                "Cardiac Rehabilitation"
            ],
            "orthopedics": [
                "Joint Replacement",
                "Sports Medicine",
                "Physical Therapy",
                "Orthopedic Surgery",
                "Fracture Care"
            ],
            "neurology": [
                "Neurological Consultation",
                "EEG",
                "MRI/CT Scan",
                "Stroke Care",
                "Epilepsy Treatment"
            ]
        },
        "general": [
            "General Medicine",
            "Outpatient Services",
            "Laboratory Services",
            "Radiology",
            "Pharmacy"
        ]
    }
    
    if hospital_type == "specialty" and specialty:
        return services.get("specialty", {}).get(specialty, services["general"])
    return services.get(hospital_type, services["general"])


def _get_default_hours(hospital_type: str) -> Dict[str, str]:
    """Get default operating hours."""
    if hospital_type == "emergency":
        return {
            "monday": "24 Hours",
            "tuesday": "24 Hours",
            "wednesday": "24 Hours",
            "thursday": "24 Hours",
            "friday": "24 Hours",
            "saturday": "24 Hours",
            "sunday": "24 Hours"
        }
    else:
        return {
            "monday": "9:00 AM - 6:00 PM",
            "tuesday": "9:00 AM - 6:00 PM",
            "wednesday": "9:00 AM - 6:00 PM",
            "thursday": "9:00 AM - 6:00 PM",
            "friday": "9:00 AM - 6:00 PM",
            "saturday": "9:00 AM - 2:00 PM",
            "sunday": "Closed"
        }


def _get_languages_spoken(hospital_type: str) -> List[str]:
    """Get languages typically spoken at hospital."""
    # Major hospitals typically support multiple languages
    return ["English", "Hindi", "Tamil", "Telugu", "Bengali", "Marathi"]


def _get_insurance_info() -> List[str]:
    """Get insurance providers accepted."""
    return [
        "Cash",
        "Credit Card",
        "Debit Card",
        "Insurance Accepted",
        "TPA Accepted"
    ]


def _get_amenities(hospital_type: str) -> List[str]:
    """Get hospital amenities."""
    base_amenities = [
        "Parking Available",
        "Wheelchair Accessible",
        "Pharmacy",
        "Cafeteria",
        "WiFi"
    ]
    
    if hospital_type == "emergency":
        base_amenities.extend([
            "Ambulance Service",
            "Helipad",
            "Blood Bank"
        ])
    
    return base_amenities


def search_hospitals_with_filters(
    lat: float,
    lon: float,
    radius_km: float = 5.0,
    hospital_type: Optional[str] = None,
    specialty: Optional[str] = None,
    min_rating: Optional[float] = None,
    services: Optional[List[str]] = None,
    languages: Optional[List[str]] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Advanced hospital search with multiple filters.
    
    Args:
        lat: Latitude
        lon: Longitude
        radius_km: Search radius
        hospital_type: Filter by type
        specialty: Filter by specialty
        min_rating: Minimum rating
        services: Required services
        languages: Languages spoken
        limit: Maximum results
        
    Returns:
        Filtered list of hospitals
    """
    # This would integrate with the existing find_nearest_hospitals
    # and add additional filtering logic
    from tools.hospitals import find_nearest_hospitals
    
    hospitals = find_nearest_hospitals(
        lat=lat,
        lon=lon,
        radius_km=radius_km,
        hospital_type=hospital_type,
        specialty=specialty,
        limit=limit * 2  # Get more to filter
    )
    
    # Apply additional filters
    filtered = []
    for hospital in hospitals:
        # Add rating (placeholder - would come from database)
        hospital["rating"] = 4.0 + (hospital.get("id", 0) % 5) * 0.1
        
        # Filter by rating
        if min_rating and hospital["rating"] < min_rating:
            continue
        
        # Filter by languages (placeholder check)
        if languages:
            hospital_languages = _get_languages_spoken(hospital.get("type", "general"))
            if not any(lang.lower() in [l.lower() for l in hospital_languages] for lang in languages):
                continue
        
        filtered.append(hospital)
        
        if len(filtered) >= limit:
            break
    
    return filtered
