"""
Decision Agent
Classifies severity and determines required actions based on symptoms.
"""
import logging
from typing import Dict, Optional
from agents.models import AgentState
from llama_index.llms.groq import Groq
import os

logger = logging.getLogger(__name__)

# Initialize LLM for severity classification
llm = Groq(
    model="meta-llama/llama-4-maverick-17b-128e-instruct",
    api_key=os.getenv("GROQ_API_KEY")
)

# Critical symptom keywords (can be expanded)
CRITICAL_KEYWORDS = [
    "chest pain", "heart attack", "stroke", "unconscious", "severe bleeding",
    "difficulty breathing", "choking", "severe allergic reaction", "seizure",
    "severe burn", "poisoning", "severe head injury", "cardiac arrest"
]

# Serious symptom keywords
SERIOUS_KEYWORDS = [
    "persistent pain", "high fever", "severe headache", "chronic", "recurring",
    "worsening", "severe", "intense", "debilitating", "unable to function"
]

# Moderate symptom keywords
MODERATE_KEYWORDS = [
    "moderate", "intermittent", "manageable", "mild to moderate", "some discomfort"
]


def classify_severity(user_input: str) -> str:
    """
    Classify symptom severity into 4 levels: 'critical', 'serious', 'moderate', 'mild'.
    
    Uses LLM for intelligent classification, with keyword fallback.
    
    Args:
        user_input: User's symptom description
    
    Returns:
        'critical', 'serious', 'moderate', or 'mild'
    """
    try:
        user_lower = user_input.lower()
        
        # Quick keyword check for obvious critical cases
        if any(keyword in user_lower for keyword in CRITICAL_KEYWORDS):
            logger.info("Critical symptoms detected via keywords")
            return "critical"
        
        # Use LLM for nuanced classification
        prompt = f"""You are a medical triage assistant. Classify the following symptom description into one of these categories: "critical", "serious", "moderate", or "mild".

CRITICAL: Life-threatening conditions requiring immediate emergency care (e.g., chest pain, heart attack, stroke, unconsciousness, severe difficulty breathing, severe bleeding, cardiac arrest, severe allergic reactions, poisoning, severe burns).

SERIOUS: Conditions requiring prompt medical attention from a specialist (e.g., persistent severe pain, high fever lasting days, chronic conditions worsening, severe headaches, debilitating symptoms, conditions affecting daily function significantly).

MODERATE: Conditions that should be evaluated by a healthcare professional but are not urgent (e.g., moderate pain, intermittent symptoms, manageable discomfort, conditions that can wait a few days for consultation).

MILD: Minor symptoms that may resolve on their own or require basic self-care (e.g., mild cold symptoms, minor aches, routine questions, minor skin irritations).

User input: "{user_input}"

Respond with ONLY one word: "critical", "serious", "moderate", or "mild"
"""
        
        response = llm.complete(prompt)
        severity = response.text.strip().lower()
        
        # Parse response
        if "critical" in severity:
            logger.info(f"Severity classified as CRITICAL for: {user_input[:50]}...")
            return "critical"
        elif "serious" in severity:
            logger.info(f"Severity classified as SERIOUS for: {user_input[:50]}...")
            return "serious"
        elif "moderate" in severity:
            logger.info(f"Severity classified as MODERATE for: {user_input[:50]}...")
            return "moderate"
        else:
            logger.info(f"Severity classified as MILD for: {user_input[:50]}...")
            return "mild"
            
    except Exception as e:
        logger.error(f"Error classifying severity: {e}")
        # Default to serious for safety
        return "serious"


def determine_action(state: AgentState) -> str:
    """
    Determine the action the agent should take based on state.
    
    Logic:
    - If critical + no location → request_location
    - If critical + location → emergency_hospital_lookup
    - If serious/moderate + location → specialist_lookup (recommend specialist)
    - If serious/moderate + no location → request_location_for_specialist
    - If mild → general_consultation
    
    Args:
        state: Current agent state
    
    Returns:
        Action string
    """
    if state.severity == "critical":
        if not state.lat or not state.lon:
            logger.info("Critical case without location - requesting location")
            return "request_location"
        else:
            logger.info("Critical case with location - looking up emergency hospitals")
            return "emergency_hospital_lookup"
    elif state.severity in ["serious", "moderate"]:
        if state.lat and state.lon:
            logger.info(f"{state.severity.capitalize()} case with location - looking up specialists")
            return "specialist_lookup"
        else:
            logger.info(f"{state.severity.capitalize()} case without location - requesting location for specialist")
            return "request_location_for_specialist"
    else:  # mild
        logger.info("Mild case - general consultation")
        return "general_consultation"


def process_agent_state(user_input: str, lat: Optional[float] = None, 
                        lon: Optional[float] = None, location_source: Optional[str] = None) -> AgentState:
    """
    Process user input and create agent state with severity and action.
    
    Args:
        user_input: User's symptom description
        lat: Optional latitude
        lon: Optional longitude
        location_source: Source of location ('gps', 'ip', 'manual')
    
    Returns:
        AgentState with severity and action determined
    """
    severity = classify_severity(user_input)
    
    state = AgentState(
        user_input=user_input,
        severity=severity,
        lat=lat,
        lon=lon,
        location_source=location_source
    )
    
    state.action = determine_action(state)
    
    return state
