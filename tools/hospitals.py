"""
Hospital Search Tools
Queries PostGIS database for nearest hospitals and specialists.
Uses GEOGRAPHY(Point, 4326) for accurate distance calculations.
"""
import logging
import os
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
import urllib.parse

logger = logging.getLogger(__name__)

# Database configuration
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')

encoded_password = urllib.parse.quote_plus(DB_PASSWORD) if DB_PASSWORD else ""
connection_string = f"postgresql+psycopg2://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def get_db_engine():
    """Create database engine with connection pooling."""
    return create_engine(
        connection_string,
        poolclass=NullPool,
        pool_pre_ping=True
    )


def _get_mock_hospitals(lat: float, lon: float, hospital_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return mock hospital data when database is not available."""
    import math
    
    mock_hospitals = [
        {
            "id": 1,
            "name": "AIIMS Delhi",
            "address": "Ansari Nagar, New Delhi, Delhi 110029",
            "lat": 28.5673,
            "lon": 77.2088,
            "type": "emergency",
            "specialty": None,
            "phone": "+91-11-26588500",
            "emergency_services": True
        },
        {
            "id": 2,
            "name": "Apollo Hospital",
            "address": "Sarita Vihar, New Delhi, Delhi 110076",
            "lat": 28.5245,
            "lon": 77.2905,
            "type": "emergency",
            "specialty": None,
            "phone": "+91-11-26925858",
            "emergency_services": True
        },
        {
            "id": 3,
            "name": "Max Super Speciality Hospital",
            "address": "Saket, New Delhi, Delhi 110017",
            "lat": 28.5275,
            "lon": 77.2190,
            "type": "emergency",
            "specialty": None,
            "phone": "+91-11-26515050",
            "emergency_services": True
        },
        {
            "id": 4,
            "name": "Fortis Escorts Heart Institute",
            "address": "Okhla Road, New Delhi, Delhi 110025",
            "lat": 28.5450,
            "lon": 77.2800,
            "type": "specialty",
            "specialty": "cardiology",
            "phone": "+91-11-47135000",
            "emergency_services": True
        },
        {
            "id": 5,
            "name": "Indraprastha Apollo Hospitals",
            "address": "Sarita Vihar, New Delhi, Delhi 110076",
            "lat": 28.5245,
            "lon": 77.2905,
            "type": "general",
            "specialty": None,
            "phone": "+91-11-26925858",
            "emergency_services": False
        }
    ]
    
    # Filter by type if specified
    if hospital_type:
        mock_hospitals = [h for h in mock_hospitals if h['type'] == hospital_type]
    
    # Calculate distances (simple haversine)
    def haversine_distance(lat1, lon1, lat2, lon2):
        R = 6371  # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return R * c
    
    # Add distances and sort
    for hospital in mock_hospitals:
        hospital['distance_km'] = round(haversine_distance(lat, lon, hospital['lat'], hospital['lon']), 2)
    
    # Sort by distance
    mock_hospitals.sort(key=lambda x: x['distance_km'])
    
    return mock_hospitals


def find_nearest_hospitals(
    lat: float,
    lon: float,
    radius_km: float = 5.0,
    hospital_type: Optional[str] = None,
    specialty: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Find nearest hospitals using PostGIS spatial queries.
    Falls back to mock data if database is not available.
    
    Args:
        lat: Latitude
        lon: Longitude
        radius_km: Search radius in kilometers (default: 5km)
        hospital_type: Filter by type ('emergency', 'general', 'specialty')
        specialty: Filter by medical specialty (e.g., 'cardiology', 'orthopedics')
        limit: Maximum number of results
    
    Returns:
        List of hospital dictionaries with name, location, distance, and type
    """
    if not all([lat, lon]):
        logger.error("Latitude and longitude are required")
        return []
    
    try:
        # Check if database credentials are available
        if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_NAME]):
            logger.warning("Database credentials not set, using mock data")
            return _get_mock_hospitals(lat, lon, hospital_type)
        
        engine = get_db_engine()
        
        # Build base query with PostGIS geography functions
        base_query = """
            SELECT 
                id,
                name,
                address,
                ST_Y(location::geometry) as lat,
                ST_X(location::geometry) as lon,
                ST_Distance(
                    location::geography,
                    ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
                ) / 1000.0 as distance_km,
                type,
                specialty,
                phone,
                emergency_services
            FROM hospitals
            WHERE 
                ST_DWithin(
                    location::geography,
                    ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                    :radius_meters
                )
        """
        
        # Add filters
        if hospital_type:
            base_query += " AND type = :hospital_type"
        if specialty:
            base_query += " AND specialty = :specialty"
        
        # Order by distance and limit
        base_query += " ORDER BY distance_km ASC LIMIT :limit"
        
        query = text(base_query)
        
        # Convert radius from km to meters for ST_DWithin
        radius_meters = radius_km * 1000
        
        params = {
            "lat": lat,
            "lon": lon,
            "radius_meters": radius_meters,
            "limit": limit
        }
        
        if hospital_type:
            params["hospital_type"] = hospital_type
        if specialty:
            params["specialty"] = specialty
        
        with engine.connect() as conn:
            result = conn.execute(query, params)
            rows = result.fetchall()
            
            hospitals = []
            for row in rows:
                hospitals.append({
                    "id": row.id,
                    "name": row.name,
                    "address": row.address,
                    "lat": float(row.lat),
                    "lon": float(row.lon),
                    "distance_km": round(float(row.distance_km), 2),
                    "type": row.type,
                    "specialty": row.specialty,
                    "phone": row.phone,
                    "emergency_services": row.emergency_services
                })
            
            logger.info(f"Found {len(hospitals)} hospitals within {radius_km}km of ({lat}, {lon})")
            return hospitals
            
    except Exception as e:
        logger.error(f"Error querying hospitals: {e}")
        logger.warning("Database query failed, falling back to mock data")
        # Fallback to mock data if database query fails
        try:
            return _get_mock_hospitals(lat, lon, hospital_type)
        except Exception as fallback_error:
            logger.error(f"Fallback also failed: {fallback_error}")
            return []


def find_emergency_hospitals(
    lat: float,
    lon: float,
    radius_km: float = 5.0,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Find nearest emergency hospitals (prioritized for critical cases).
    
    Args:
        lat: Latitude
        lon: Longitude
        radius_km: Search radius in kilometers
        limit: Maximum number of results
    
    Returns:
        List of emergency hospitals sorted by distance
    """
    return find_nearest_hospitals(
        lat=lat,
        lon=lon,
        radius_km=radius_km,
        hospital_type="emergency",
        limit=limit
    )


def find_specialists(
    lat: float,
    lon: float,
    specialty: str,
    radius_km: float = 5.0,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Find nearest specialists for non-critical cases.
    
    Args:
        lat: Latitude
        lon: Longitude
        specialty: Medical specialty (e.g., 'cardiology', 'orthopedics')
        radius_km: Search radius in kilometers
        limit: Maximum number of results
    
    Returns:
        List of specialists sorted by distance
    """
    return find_nearest_hospitals(
        lat=lat,
        lon=lon,
        radius_km=radius_km,
        specialty=specialty,
        limit=limit
    )


def ensure_hospitals_table():
    """
    Create hospitals table with PostGIS support if it doesn't exist.
    This should be run as a migration script, not on every request.
    """
    try:
        engine = get_db_engine()
        
        with engine.connect() as conn:
            # Enable PostGIS extension
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            conn.commit()
            
            # Create hospitals table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS hospitals (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    address TEXT,
                    location GEOGRAPHY(Point, 4326) NOT NULL,
                    type VARCHAR(50) NOT NULL CHECK (type IN ('emergency', 'general', 'specialty')),
                    specialty VARCHAR(100),
                    phone VARCHAR(20),
                    emergency_services BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            # Create spatial index for fast queries
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_hospitals_location 
                ON hospitals USING GIST (location);
            """))
            
            # Create indexes for filtering
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_hospitals_type 
                ON hospitals (type);
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_hospitals_specialty 
                ON hospitals (specialty);
            """))
            
            conn.commit()
            logger.info("Hospitals table created/verified successfully")
            
    except Exception as e:
        logger.error(f"Error creating hospitals table: {e}")
        raise
