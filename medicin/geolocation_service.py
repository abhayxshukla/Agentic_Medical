from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from geopy.extra.rate_limiter import RateLimiter
import requests
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Initialize geocoder with rate limiting
geolocator = Nominatim(user_agent="medical_intake_agent_v1")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)


def find_nearby_hospitals_overpass(
    pin_code: str, 
    specialty: Optional[str] = None, 
    radius_km: float = 10
) -> Dict:
    """
    Find nearby hospitals/clinics using Overpass API (OpenStreetMap) + geopy.
    No dataset required - queries OSM in real-time.
    
    Args:
        pin_code: Indian PIN code (6 digits)
        specialty: Medical specialty (e.g., 'gastroenterology', 'cardiology')
        radius_km: Search radius in kilometers
    
    Returns:
        Dict with status, hospitals list, and metadata
    """
    try:
        # Step 1: Geocode PIN to coordinates
        logger.info(f"Geocoding PIN: {pin_code}")
        user_location = geocode(f"{pin_code}, India")
        
        if not user_location:
            return {
                "status": "error",
                "message": f"Unable to locate PIN code: {pin_code}",
                "hospitals": []
            }
        
        lat, lon = user_location.latitude, user_location.longitude
        logger.info(f"PIN {pin_code} geocoded to: ({lat}, {lon})")
        
        # Step 2: Query Overpass API for hospitals/clinics
        radius_meters = int(radius_km * 1000)
        overpass_url = "http://overpass-api.de/api/interpreter"
        
        overpass_query = f"""
        [out:json][timeout:25];
        (
          node["amenity"="hospital"](around:{radius_meters},{lat},{lon});
          node["amenity"="clinic"](around:{radius_meters},{lat},{lon});
          node["amenity"="doctors"](around:{radius_meters},{lat},{lon});
          way["amenity"="hospital"](around:{radius_meters},{lat},{lon});
          way["amenity"="clinic"](around:{radius_meters},{lat},{lon});
        );
        out center;
        """
        
        logger.info(f"Querying Overpass API for hospitals within {radius_km}km...")
        response = requests.get(
            overpass_url, 
            params={'data': overpass_query}, 
            timeout=30
        )
        
        if response.status_code != 200:
            return {
                "status": "error",
                "message": f"Overpass API error: {response.status_code}",
                "hospitals": []
            }
        
        data = response.json()
        
        # Step 3: Process results and calculate distances
        hospitals = []
        user_coords = (lat, lon)
        
        for element in data.get('elements', []):
            # Get coordinates (center for ways, direct lat/lon for nodes)
            if 'center' in element:
                hosp_coords = (element['center']['lat'], element['center']['lon'])
            elif 'lat' in element and 'lon' in element:
                hosp_coords = (element['lat'], element['lon'])
            else:
                continue
            
            # Calculate geodesic distance
            distance = geodesic(user_coords, hosp_coords).km
            
            # Get details from tags
            tags = element.get('tags', {})
            name = tags.get('name', 'Unnamed Healthcare Facility')
            amenity_type = tags.get('amenity', 'hospital')
            
            # Build address
            address_parts = []
            if tags.get('addr:full'):
                address_parts.append(tags['addr:full'])
            else:
                if tags.get('addr:street'):
                    address_parts.append(tags['addr:street'])
                if tags.get('addr:city'):
                    address_parts.append(tags['addr:city'])
            
            address = ', '.join(address_parts) if address_parts else 'Address not available'
            
            # Get contact info
            phone = tags.get('phone', tags.get('contact:phone', 'N/A'))
            website = tags.get('website', tags.get('contact:website', 'N/A'))
            
            # Check specialty match (if provided)
            specialty_match = True
            if specialty:
                specialty_lower = specialty.lower()
                healthcare_specialty = tags.get('healthcare:speciality', '').lower()
                description = tags.get('description', '').lower()
                
                # Simple keyword matching
                if specialty_lower not in name.lower() and \
                   specialty_lower not in healthcare_specialty and \
                   specialty_lower not in description:
                    specialty_match = False
            
            hospitals.append({
                'name': name,
                'type': amenity_type.title(),
                'address': address,
                'phone': phone,
                'website': website,
                'distance_km': round(distance, 2),
                'coordinates': {
                    'latitude': hosp_coords[0],
                    'longitude': hosp_coords[1]
                },
                'specialty_match': specialty_match
            })
        
        # Sort by distance
        hospitals = sorted(hospitals, key=lambda x: x['distance_km'])
        
        # Filter by specialty if provided (prioritize matches, but include others)
        if specialty:
            specialty_matches = [h for h in hospitals if h['specialty_match']]
            other_hospitals = [h for h in hospitals if not h['specialty_match']]
            hospitals = specialty_matches + other_hospitals
        
        # Limit to top 5
        hospitals = hospitals[:5]
        
        logger.info(f"Found {len(hospitals)} hospitals near PIN {pin_code}")
        
        return {
            "status": "success",
            "pin_code": pin_code,
            "location": {
                "latitude": lat,
                "longitude": lon,
                "address": user_location.address
            },
            "radius_km": radius_km,
            "specialty_filter": specialty,
            "hospitals": hospitals,
            "total_found": len(data.get('elements', []))
        }
        
    except requests.Timeout:
        logger.error("Overpass API timeout")
        return {
            "status": "error",
            "message": "Request timeout. Please try again.",
            "hospitals": []
        }
    except Exception as e:
        logger.error(f"Error in geolocation service: {e}")
        return {
            "status": "error",
            "message": f"Geolocation error: {str(e)}",
            "hospitals": []
        }


def format_hospitals_for_chat(geo_result: Dict) -> str:
    """
    Format geolocation results for chat engine response.
    """
    if geo_result['status'] != 'success':
        return f"❌ {geo_result['message']}"
    
    hospitals = geo_result['hospitals']
    
    if not hospitals:
        specialty = geo_result.get('specialty_filter', '')
        specialty_text = f" for {specialty}" if specialty else ""
        return (
            f"No hospitals or clinics found within {geo_result['radius_km']}km "
            f"of PIN code {geo_result['pin_code']}{specialty_text}. "
            "You may need to expand your search radius or try a nearby PIN code."
        )
    
    # Build formatted response
    specialty = geo_result.get('specialty_filter', '')
    specialty_text = f" specializing in {specialty}" if specialty else ""
    
    result = f"📍 Found {len(hospitals)} healthcare facilities{specialty_text} near PIN {geo_result['pin_code']}:\n\n"
    
    for idx, hospital in enumerate(hospitals, 1):
        result += f"{idx}. **{hospital['name']}** ({hospital['type']})\n"
        result += f"   📍 {hospital['address']}\n"
        result += f"   📞 {hospital['phone']}\n"
        if hospital['website'] != 'N/A':
            result += f"   🌐 {hospital['website']}\n"
        result += f"   📏 Distance: {hospital['distance_km']} km\n\n"
    
    return result


def extract_specialty_from_symptoms(symptoms_text: str) -> Optional[str]:
    """
    Extract medical specialty from symptoms or prescription analysis.
    Simple keyword matching - can be enhanced with LLM.
    """
    symptoms_lower = symptoms_text.lower()
    
    specialty_keywords = {
        'cardiology': ['heart', 'cardiac', 'chest pain', 'blood pressure', 'hypertension'],
        'gastroenterology': ['stomach', 'gastric', 'digestion', 'acidity', 'ulcer', 'abdomen'],
        'dermatology': ['skin', 'rash', 'acne', 'dermatitis', 'eczema'],
        'orthopedics': ['bone', 'joint', 'fracture', 'arthritis', 'back pain'],
        'neurology': ['headache', 'migraine', 'nerve', 'neurological', 'seizure'],
        'ophthalmology': ['eye', 'vision', 'sight', 'cataract'],
        'ent': ['ear', 'nose', 'throat', 'hearing', 'sinus'],
        'pulmonology': ['lung', 'breathing', 'asthma', 'cough', 'respiratory'],
        'endocrinology': ['diabetes', 'thyroid', 'hormone'],
        'nephrology': ['kidney', 'renal', 'urinary']
    }
    
    for specialty, keywords in specialty_keywords.items():
        if any(keyword in symptoms_lower for keyword in keywords):
            logger.info(f"Detected specialty: {specialty}")
            return specialty
    
    return None
