"""
Geolocation Agent
Orchestrates geolocation tools and hospital search based on agent state.
"""
import logging
from typing import Dict, Optional, List, Any
from agents.models import AgentState
from agents.decision_agent import process_agent_state, determine_action
from tools.geolocation import (
    get_location_from_gps,
    geocode_address,
    get_location_from_ip
)
from tools.hospitals import (
    find_emergency_hospitals,
    find_specialists,
    find_nearest_hospitals
)
from tools.symptom_specialty_mapper import map_symptoms_to_specialty, get_specialty_display_name
from fastapi import Request

logger = logging.getLogger(__name__)


class GeoAgent:
    """
    Agent that handles geolocation and hospital search operations.
    """
    
    def __init__(self):
        self.safety_disclaimer = (
            "⚠️ IMPORTANT: This is not a medical diagnosis. "
            "For emergencies, call 112 (India) or your local emergency number immediately. "
            "Always consult with qualified healthcare professionals for proper diagnosis and treatment."
        )
    
    async def process_request(
        self,
        user_input: str,
        location: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for geolocation agent processing.
        
        Args:
            user_input: User's symptom description
            location: Optional location dict with 'lat', 'lon', or 'address'
            request: Optional FastAPI Request for IP geolocation
        
        Returns:
            Dict with severity, action, hospitals, and response message
        """
        try:
            # Step 1: Determine location
            lat, lon, location_source = await self._resolve_location(location, request)
            
            # Step 2: Process agent state (classify severity, determine action)
            state = process_agent_state(
                user_input=user_input,
                lat=lat,
                lon=lon,
                location_source=location_source
            )
            
            # Step 3: Execute action
            result = await self._execute_action(state)
            
            # Step 4: Add safety disclaimer for critical cases
            if state.severity == "critical":
                result["disclaimer"] = self.safety_disclaimer
                result["emergency_number"] = "112"
            
            result["severity"] = state.severity
            result["action"] = state.action
            result["location"] = {
                "lat": state.lat,
                "lon": state.lon,
                "source": state.location_source
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in geo agent processing: {e}")
            return {
                "error": str(e),
                "severity": "critical",  # Default to critical on error
                "action": "error",
                "message": "An error occurred. For emergencies, call 112 immediately."
            }
    
    async def _resolve_location(
        self,
        location: Optional[Dict],
        request: Optional[Request]
    ) -> tuple:
        """
        Resolve location from various sources.
        
        Priority:
        1. GPS coordinates (lat/lon)
        2. Address (geocoded)
        3. IP address (fallback)
        
        Returns:
            Tuple of (lat, lon, location_source)
        """
        # Priority 1: GPS coordinates
        if location and "lat" in location and "lon" in location:
            gps_result = get_location_from_gps(location["lat"], location["lon"])
            if gps_result.get("valid"):
                return gps_result["lat"], gps_result["lon"], "gps"
        
        # Priority 2: Address geocoding
        if location and "address" in location:
            geocode_result = geocode_address(location["address"])
            if geocode_result and geocode_result.get("valid"):
                return geocode_result["lat"], geocode_result["lon"], "manual"
        
        # Priority 3: IP geolocation (fallback, approximate)
        if request:
            ip_result = get_location_from_ip(request)
            if ip_result and ip_result.get("valid"):
                logger.info("Using IP-based location (approximate)")
                return ip_result["lat"], ip_result["lon"], "ip"
        
        return None, None, None
    
    async def _execute_action(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute the action determined by the decision agent.
        
        Args:
            state: Agent state with action determined
        
        Returns:
            Dict with action results
        """
        if state.action == "request_location":
            return {
                "message": (
                    "🚨 This appears to be a critical medical situation. "
                    "To find the nearest emergency hospital, please share your location. "
                    "You can provide GPS coordinates or your address."
                ),
                "hospitals": [],
                "requires_location": True
            }
        
        elif state.action == "emergency_hospital_lookup":
            if not state.lat or not state.lon:
                return {
                    "message": "Location required for emergency hospital lookup.",
                    "hospitals": [],
                    "requires_location": True
                }
            
            hospitals = find_emergency_hospitals(
                lat=state.lat,
                lon=state.lon,
                radius_km=5.0,
                limit=5
            )
            
            if hospitals:
                message = (
                    f"🚨 Found {len(hospitals)} emergency hospital(s) nearby:\n\n"
                )
                for i, hospital in enumerate(hospitals, 1):
                    message += (
                        f"{i}. {hospital['name']}\n"
                        f"   📍 {hospital['address'] or 'Address not available'}\n"
                        f"   📏 {hospital['distance_km']} km away\n"
                        f"   📞 {hospital['phone'] or 'Phone not available'}\n\n"
                    )
                message += "Call 112 for immediate emergency assistance."
            else:
                message = (
                    "⚠️ No emergency hospitals found within 5km. "
                    "Please call 112 immediately for emergency assistance. "
                    "Expanding search radius..."
                )
                # Try larger radius
                hospitals = find_emergency_hospitals(
                    lat=state.lat,
                    lon=state.lon,
                    radius_km=10.0,
                    limit=5
                )
            
            return {
                "message": message,
                "hospitals": hospitals,
                "requires_location": False
            }
        
        elif state.action == "request_location_for_specialist":
            severity_msg = "serious" if state.severity == "serious" else "moderate"
            return {
                "message": (
                    f"⚠️ Based on your symptoms, this appears to be a {severity_msg} condition. "
                    "I recommend consulting with a specialist. "
                    "To find nearby specialists, please share your location. "
                    "You can provide GPS coordinates or your address."
                ),
                "hospitals": [],
                "requires_location": True
            }
        
        elif state.action == "specialist_lookup":
            if not state.lat or not state.lon:
                return {
                    "message": "Location required for specialist lookup.",
                    "hospitals": [],
                    "requires_location": True
                }
            
            # Map symptoms to specialty
            specialty = map_symptoms_to_specialty(state.user_input)
            specialty_display = get_specialty_display_name(specialty) if specialty else None
            
            # Find specialists - try specialty first, then general
            hospitals = []
            if specialty:
                hospitals = find_nearest_hospitals(
                    lat=state.lat,
                    lon=state.lon,
                    radius_km=10.0,  # Larger radius for specialists
                    specialty=specialty,
                    limit=10
                )
            
            # If no specialty-specific hospitals found, try general specialists
            if not hospitals:
                hospitals = find_nearest_hospitals(
                    lat=state.lat,
                    lon=state.lon,
                    radius_km=10.0,
                    hospital_type="specialty",
                    limit=10
                )
            
            # If still no results, try general hospitals
            if not hospitals:
                hospitals = find_nearest_hospitals(
                    lat=state.lat,
                    lon=state.lon,
                    radius_km=10.0,
                    limit=10
                )
            
            if hospitals:
                if specialty_display:
                    message = f"Based on your symptoms, I recommend consulting a {specialty_display} specialist.\n\n"
                    message += f"Found {len(hospitals)} nearby healthcare facility/facilities:\n\n"
                else:
                    message = f"Found {len(hospitals)} nearby healthcare facility/facilities:\n\n"
                
                for i, hospital in enumerate(hospitals, 1):
                    specialty_info = ""
                    if hospital.get('specialty'):
                        specialty_info = f"   🏥 Specialty: {get_specialty_display_name(hospital['specialty'])}\n"
                    elif specialty_display:
                        specialty_info = f"   🏥 Recommended: {specialty_display}\n"
                    
                    message += (
                        f"{i}. {hospital['name']}\n"
                        f"   📍 {hospital['address'] or 'Address not available'}\n"
                        f"   📏 {hospital['distance_km']:.2f} km away\n"
                        f"{specialty_info}"
                        f"   📞 {hospital['phone'] or 'Phone not available'}\n\n"
                    )
            else:
                message = "No healthcare facilities found nearby. Please try expanding your search area or consult a general practitioner."
            
            result = {
                "message": message,
                "hospitals": hospitals,
                "requires_location": False
            }
            
            # Add specialty information
            if specialty:
                result["suggested_specialty"] = specialty
                result["specialty_display"] = specialty_display
            
            return result
        
        else:  # general_consultation
            return {
                "message": (
                    "I understand your concern. For non-urgent medical questions, "
                    "I recommend consulting with a healthcare professional. "
                    "If you'd like, I can help you find nearby clinics or specialists "
                    "if you share your location."
                ),
                "hospitals": [],
                "requires_location": False
            }
