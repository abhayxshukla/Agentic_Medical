"""
Document Location Extractor
Extracts location information from medical documents using OCR and NLP.
"""
import logging
import re
from typing import Optional, Dict, List, Tuple, Any
from tools.geolocation import geocode_address

logger = logging.getLogger(__name__)

# Common location patterns in medical documents
LOCATION_PATTERNS = [
    r'\b(?:Address|Location|City|Area|Place)[\s:]+([A-Za-z\s,]+)',
    r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*(?:India|IN|Delhi|Mumbai|Bangalore|Chennai|Hyderabad|Kolkata|Pune)',
    r'\b(Delhi|Mumbai|Bangalore|Chennai|Hyderabad|Kolkata|Pune|Ahmedabad|Jaipur|Lucknow)',
    r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Road|Street|Avenue|Lane|Nagar|Colony)',
    r'PIN[:\s]+(\d{6})',  # PIN codes can help identify location
]

# Indian city names
INDIAN_CITIES = [
    'Delhi', 'Mumbai', 'Bangalore', 'Chennai', 'Hyderabad', 'Kolkata',
    'Pune', 'Ahmedabad', 'Jaipur', 'Lucknow', 'Surat', 'Kanpur',
    'Nagpur', 'Indore', 'Thane', 'Bhopal', 'Visakhapatnam', 'Patna',
    'Vadodara', 'Ghaziabad', 'Ludhiana', 'Agra', 'Nashik', 'Faridabad',
    'Meerut', 'Rajkot', 'Varanasi', 'Srinagar', 'Amritsar', 'Chandigarh'
]


def extract_location_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract location information from document text.
    
    Args:
        text: Extracted text from OCR/document
        
    Returns:
        Dict with location information or None
    """
    if not text:
        return None
    
    text_upper = text.upper()
    locations_found = []
    
    # Pattern 1: Look for city names
    for city in INDIAN_CITIES:
        if city.upper() in text_upper:
            locations_found.append({
                'type': 'city',
                'name': city,
                'confidence': 'high'
            })
    
    # Pattern 2: Look for address patterns
    for pattern in LOCATION_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            location_text = match.group(1) if match.groups() else match.group(0)
            if location_text and len(location_text.strip()) > 2:
                locations_found.append({
                    'type': 'address',
                    'text': location_text.strip(),
                    'confidence': 'medium'
                })
    
    # Pattern 3: Look for PIN codes (can help identify area)
    pin_matches = re.findall(r'\b(\d{6})\b', text)
    if pin_matches:
        for pin in pin_matches[:3]:  # Take first 3 PIN codes
            locations_found.append({
                'type': 'pin',
                'code': pin,
                'confidence': 'medium'
            })
    
    if not locations_found:
        return None
    
    # Return the most confident location
    high_confidence = [loc for loc in locations_found if loc.get('confidence') == 'high']
    if high_confidence:
        return high_confidence[0]
    
    return locations_found[0]


def geocode_extracted_location(location_info: Dict[str, Any]) -> Optional[Tuple[float, float, str]]:
    """
    Geocode extracted location information.
    
    Args:
        location_info: Location dict from extract_location_from_text
        
    Returns:
        Tuple of (lat, lon, formatted_address) or None
    """
    if not location_info:
        return None
    
    try:
        if location_info['type'] == 'city':
            # Try geocoding city name
            address = f"{location_info['name']}, India"
            result = geocode_address(address)
            if result and result.get('valid'):
                return (
                    result['lat'],
                    result['lon'],
                    result.get('formatted_address', address)
                )
        
        elif location_info['type'] == 'address':
            # Try geocoding address
            address = f"{location_info['text']}, India"
            result = geocode_address(address)
            if result and result.get('valid'):
                return (
                    result['lat'],
                    result['lon'],
                    result.get('formatted_address', address)
                )
        
        elif location_info['type'] == 'pin':
            # PIN code lookup (simplified - would need PIN database)
            # For now, try common city associations
            pin = location_info['code']
            # Common PIN ranges (simplified)
            pin_ranges = {
                '110': 'Delhi',
                '400': 'Mumbai',
                '560': 'Bangalore',
                '600': 'Chennai',
                '500': 'Hyderabad',
                '700': 'Kolkata'
            }
            
            for prefix, city in pin_ranges.items():
                if pin.startswith(prefix):
                    address = f"{city}, India"
                    result = geocode_address(address)
                    if result and result.get('valid'):
                        return (
                            result['lat'],
                            result['lon'],
                            result.get('formatted_address', address)
                        )
    
    except Exception as e:
        logger.error(f"Error geocoding location: {e}")
    
    return None


def extract_location_from_document(document_text: str) -> Optional[Dict[str, Any]]:
    """
    Complete pipeline: Extract and geocode location from document.
    
    Args:
        document_text: Full text extracted from document
        
    Returns:
        Dict with location data including lat/lon if geocoded successfully
    """
    if not document_text:
        return None
    
    # Extract location information
    location_info = extract_location_from_text(document_text)
    
    if not location_info:
        logger.info("No location information found in document")
        return None
    
    logger.info(f"Found location in document: {location_info}")
    
    # Try to geocode
    geocode_result = geocode_extracted_location(location_info)
    
    if geocode_result:
        lat, lon, address = geocode_result
        return {
            'lat': lat,
            'lon': lon,
            'address': address,
            'source': 'document',
            'extracted_info': location_info,
            'geocoded': True
        }
    else:
        # Return location info even if geocoding failed
        return {
            'source': 'document',
            'extracted_info': location_info,
            'geocoded': False
        }
