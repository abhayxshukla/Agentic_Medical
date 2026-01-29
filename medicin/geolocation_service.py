from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from geopy.extra.rate_limiter import RateLimiter
import googlemaps
import os
from typing import List, Dict, Optional
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Initialize Google Maps client
gmaps = googlemaps.Client(key=os.getenv('GOOGLE_MAPS_API_KEY'))

# Initialize geocoder with rate limiting (backup)
geolocator = Nominatim(user_agent="medical_intake_agent_v1")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)


def find_nearby_hospitals_google(
    pin_code: str,
    specialty: Optional[str] = None,
    radius_km: float = 10,
    include_clinics: bool = True
) -> Dict:
    """
    Find nearby hospitals/clinics using Google Maps Places API.
    Returns only essential info: name, address, rating, and business hours.
    
    Args:
        pin_code: Indian PIN code (6 digits)
        specialty: Medical specialty (e.g., 'cardiology', 'gastroenterology')
        radius_km: Search radius in kilometers (max 50km for Places API)
        include_clinics: Whether to include clinics and smaller healthcare facilities
    
    Returns:
        Dict with status, hospitals list with minimal essential data
    """
    try:
        # Step 1: Geocode PIN to coordinates using Google Geocoding API
        logger.info(f"Geocoding PIN: {pin_code}")
        
        geocode_result = gmaps.geocode(f"{pin_code}, India")
        
        if not geocode_result:
            return {
                "status": "error",
                "message": f"Unable to locate PIN code: {pin_code}",
                "hospitals": []
            }
        
        location = geocode_result[0]['geometry']['location']
        lat, lon = location['lat'], location['lng']
        formatted_address = geocode_result[0]['formatted_address']
        
        logger.info(f"PIN {pin_code} geocoded to: ({lat}, {lon})")
        
        # Step 2: Search for hospitals using Places API
        radius_meters = int(radius_km * 1000)
        
        # Build search query based on specialty
        if specialty:
            query = f"{specialty} hospital near {pin_code}"
        else:
            query = "hospital"
        
        # Use Places API Text Search - request only needed fields
        search_params = {
            'query': query,
            'location': (lat, lon),
            'radius': radius_meters,
            'type': 'hospital'
        }
        
        logger.info(f"Searching Google Places for hospitals within {radius_km}km...")
        places_result = gmaps.places(**search_params)
        
        hospitals = []
        user_coords = (lat, lon)
        
        # Step 3: Process each place - get only essential details
        for place in places_result.get('results', []):
            place_id = place['place_id']
            
            # Get place_types from search results (not from details)
            place_types = place.get('types', [])
            
            # Filter out non-hospitals if include_clinics is False
            if not include_clinics and 'hospital' not in place_types:
                continue
            
            # Get detailed information - ONLY request valid fields
            place_details = gmaps.place(
                place_id=place_id,
                fields=[
                    'name',
                    'formatted_address',
                    'rating',
                    'user_ratings_total',
                    'opening_hours',
                    'geometry',
                    'business_status'
                    # 'types' is NOT a valid field for place() - removed
                ]
            )
            
            details = place_details.get('result', {})
            
            # Get coordinates
            place_location = details['geometry']['location']
            hosp_coords = (place_location['lat'], place_location['lng'])
            
            # Calculate actual distance
            distance = geodesic(user_coords, hosp_coords).km
            
            # Skip if beyond radius
            if distance > radius_km:
                continue
            
            # Extract opening hours
            opening_hours = None
            is_open_now = None
            if 'opening_hours' in details:
                opening_hours = details['opening_hours'].get('weekday_text', [])
                is_open_now = details['opening_hours'].get('open_now', None)
            
            # Check specialty match
            specialty_match = True
            if specialty:
                specialty_lower = specialty.lower()
                name_lower = details.get('name', '').lower()
                address_lower = details.get('formatted_address', '').lower()
                # Use types from search results, not details
                types_str = ' '.join(place_types).lower()
                
                if specialty_lower not in name_lower and \
                   specialty_lower not in address_lower and \
                   specialty_lower not in types_str:
                    specialty_match = False
            
            # Build minimal hospital data object
            hospital_data = {
                'place_id': place_id,
                'name': details.get('name', 'Unnamed Healthcare Facility'),
                'type': 'Hospital' if 'hospital' in place_types else 'Clinic',
                'address': details.get('formatted_address', 'Address not available'),
                'distance_km': round(distance, 2),
                'rating': details.get('rating', 0),
                'total_ratings': details.get('user_ratings_total', 0),
                'is_open_now': is_open_now,
                'opening_hours': opening_hours,
                'business_status': details.get('business_status', 'UNKNOWN'),
                'coordinates': {
                    'latitude': hosp_coords[0],
                    'longitude': hosp_coords[1]
                },
                'google_maps_url': f"https://www.google.com/maps/place/?q=place_id:{place_id}",
                'specialty_match': specialty_match
            }
            
            hospitals.append(hospital_data)
        
        # Sort by specialty match first, then by rating, then by distance
        if specialty:
            hospitals = sorted(
                hospitals,
                key=lambda x: (
                    not x['specialty_match'],  # specialty matches first
                    -x['rating'],  # higher rating first
                    x['distance_km']  # closer distance first
                )
            )
        else:
            # Sort by rating and distance
            hospitals = sorted(
                hospitals,
                key=lambda x: (-x['rating'], x['distance_km'])
            )
        
        # Limit to top 10
        hospitals = hospitals[:10]
        
        logger.info(f"Found {len(hospitals)} hospitals near PIN {pin_code}")
        
        return {
            "status": "success",
            "pin_code": pin_code,
            "location": {
                "latitude": lat,
                "longitude": lon,
                "address": formatted_address
            },
            "radius_km": radius_km,
            "specialty_filter": specialty,
            "hospitals": hospitals,
            "total_found": len(places_result.get('results', []))
        }
        
    except googlemaps.exceptions.ApiError as e:
        logger.error(f"Google Maps API error: {e}")
        return {
            "status": "error",
            "message": f"Google Maps API error: {str(e)}",
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
    Shows only: name, address, rating, hours, distance.
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
        result += f"   ⭐ Rating: {hospital['rating']}/5 ({hospital['total_ratings']} reviews)\n"
        
        if hospital['is_open_now'] is not None:
            status = "🟢 Open Now" if hospital['is_open_now'] else "🔴 Closed"
            result += f"   {status}\n"
        
        # Show today's hours if available
        if hospital['opening_hours'] and len(hospital['opening_hours']) > 0:
            from datetime import datetime
            today_idx = datetime.now().weekday()
            if today_idx < len(hospital['opening_hours']):
                result += f"   🕐 {hospital['opening_hours'][today_idx]}\n"
        
        result += f"   📏 Distance: {hospital['distance_km']} km\n"
        result += f"   🗺️ [View on Google Maps]({hospital['google_maps_url']})\n\n"
    
    return result


def extract_specialty_from_symptoms_llm(symptoms_text: str, llm_instance) -> Optional[str]:
    """
    LLM-based specialty extraction optimized for GPT-5.
    Deterministic, closed-set, medical-safe classification.
    """

    specialty_prompt = f"""
You are a medical triage classification engine.

TASK:
Classify the medical information below into ONE medical specialty.

STRICT RULES:
- Choose ONLY from the allowed list
- Output EXACTLY one specialty
- Output ONLY the specialty name
- No explanations
- No punctuation
- No markdown
- Lowercase only
- If unclear, output "general medicine"

PRIORITY RULES:
- Cancer, tumor, malignancy, chemotherapy, radiotherapy → oncology
- Severe infection, fungal infection, sepsis, IV antimicrobials → infectious disease
- If multiple specialties apply → choose the MOST critical one

ALLOWED SPECIALTIES:
infectious disease
oncology
cardiology
gastroenterology
dermatology
orthopedics
neurology
ophthalmology
ent
pulmonology
endocrinology
nephrology
gynecology
pediatrics
psychiatry
general medicine

MEDICAL INFORMATION:
<<<
{symptoms_text}
>>>

FINAL ANSWER:
"""

    try:
        response = llm_instance.complete(
            specialty_prompt,
            max_tokens=8  # 🔥 Important: forces single-label output
        )
    except Exception as e:
        logger.error(f"LLM specialty extraction error: {e}")
        return "general medicine"

    specialty = str(response).strip().lower()
    specialty = specialty.replace(".", "").strip()

    valid_specialties = {
        'infectious disease',
        'oncology',
        'cardiology',
        'gastroenterology',
        'dermatology',
        'orthopedics',
        'neurology',
        'ophthalmology',
        'ent',
        'pulmonology',
        'endocrinology',
        'nephrology',
        'gynecology',
        'pediatrics',
        'psychiatry',
        'general medicine'
    }

    if specialty in valid_specialties:
        logger.info(f"LLM detected specialty: {specialty}")
        return specialty

    logger.warning(f"Unrecognized LLM output '{specialty}', defaulting to general medicine")
    return "general medicine"





def extract_specialty_from_symptoms_hybrid(symptoms_text: str, llm_instance, use_llm: bool = True) -> Optional[str]:
    """
    Hybrid approach: Try LLM first, fallback to keyword matching.
    
    Args:
        symptoms_text: User's symptoms or prescription text
        llm_instance: Your Groq LLM instance
        use_llm: Whether to use LLM (set False to use keywords only)
    
    Returns:
        Detected specialty
    """
    if use_llm:
        try:
            specialty = extract_specialty_from_symptoms_llm(symptoms_text, llm_instance)
            if specialty:
                return specialty
        except Exception as e:
            logger.warning(f"LLM specialty extraction failed, falling back to keywords: {e}")
    
    # Fallback to enhanced keyword matching
    symptoms_lower = symptoms_text.lower()
    
    specialty_keywords = {
        'infectious disease': [
            'fungal', 'bacterial', 'viral', 'infection', 'sepsis', 
            'amphotericin', 'antifungal', 'antibiotic', 'antimicrobial',
            'isavuconazole', 'fluconazole', 'voriconazole'
        ],
        'oncology': [
            'cancer', 'tumor', 'tumour', 'chemotherapy', 'radiation',
            'oncology', 'oncologist', 'malignancy', 'carcinoma', 'sarcoma',
            'leukemia', 'lymphoma', 'metastasis'
        ],
        'cardiology': [
            'heart', 'cardiac', 'chest pain', 'blood pressure', 
            'hypertension', 'palpitation', 'ecg', 'angioplasty'
        ],
        'gastroenterology': [
            'stomach', 'gastric', 'digestion', 'acidity', 'ulcer', 
            'abdomen', 'intestine', 'liver', 'ibs', 'crohn'
        ],
        'dermatology': [
            'skin', 'rash', 'acne', 'dermatitis', 'eczema', 'psoriasis',
            'dermatologist'
        ],
        'orthopedics': [
            'bone', 'joint', 'fracture', 'arthritis', 'back pain', 
            'spine', 'orthopedic', 'ligament', 'tendon'
        ],
        'neurology': [
            'headache', 'migraine', 'nerve', 'neurological', 'seizure', 
            'brain', 'stroke', 'parkinson', 'alzheimer'
        ],
        'ophthalmology': [
            'eye', 'vision', 'sight', 'cataract', 'glaucoma', 
            'retina', 'ophthalmologist'
        ],
        'ent': [
            'ear', 'nose', 'throat', 'hearing', 'sinus', 'tonsil',
            'ent specialist'
        ],
        'pulmonology': [
            'lung', 'breathing', 'asthma', 'cough', 'respiratory', 
            'bronchitis', 'copd', 'pneumonia'
        ],
        'endocrinology': [
            'diabetes', 'thyroid', 'hormone', 'insulin', 'endocrine',
            'pituitary', 'adrenal'
        ],
        'nephrology': [
            'kidney', 'renal', 'urinary', 'dialysis', 'nephrologist',
            'creatinine'
        ],
        'gynecology': [
            'pregnancy', 'menstrual', 'ovarian', 'uterus', 'gynae',
            'gynecologist', 'pcos', 'menopause'
        ],
        'pediatrics': [
            'child', 'infant', 'baby', 'pediatric', 'vaccination',
            'pediatrician', 'newborn'
        ]
    }
    
    # Check for specialty keywords (prioritize specific ones first)
    # Check infectious disease and oncology first as they're often missed
    for specialty in ['infectious disease', 'oncology']:
        keywords = specialty_keywords.get(specialty, [])
        if any(keyword in symptoms_lower for keyword in keywords):
            logger.info(f"Keyword detected specialty: {specialty}")
            return specialty
    
    # Then check other specialties
    for specialty, keywords in specialty_keywords.items():
        if specialty not in ['infectious disease', 'oncology']:  # Already checked
            if any(keyword in symptoms_lower for keyword in keywords):
                logger.info(f"Keyword detected specialty: {specialty}")
                return specialty
    
    logger.info("No specific specialty detected, using general medicine")
    return "general medicine"




