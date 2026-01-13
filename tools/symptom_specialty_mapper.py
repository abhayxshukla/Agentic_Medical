"""
Symptom to Specialty Mapper
Maps user symptoms to appropriate medical specialties.
"""
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

# Symptom keywords mapped to specialties
SYMPTOM_SPECIALTY_MAP = {
    # Cardiology
    "cardiology": ["chest pain", "heart", "cardiac", "palpitation", "irregular heartbeat", 
                   "shortness of breath", "chest tightness", "heart attack", "angina"],
    
    # Orthopedics
    "orthopedics": ["bone", "fracture", "joint pain", "back pain", "knee pain", "shoulder pain",
                    "hip pain", "arthritis", "spine", "disc", "ligament", "tendon"],
    
    # Neurology
    "neurology": ["headache", "migraine", "seizure", "dizziness", "vertigo", "numbness",
                  "tingling", "memory loss", "confusion", "stroke", "epilepsy"],
    
    # Gastroenterology
    "gastroenterology": ["stomach", "abdominal pain", "nausea", "vomiting", "diarrhea",
                        "constipation", "indigestion", "acid reflux", "ulcer", "liver"],
    
    # Dermatology
    "dermatology": ["rash", "skin", "itching", "acne", "eczema", "psoriasis", "allergy",
                   "hives", "dermatitis", "mole", "wart"],
    
    # Ophthalmology
    "ophthalmology": ["eye", "vision", "blurred vision", "eye pain", "red eye", "dry eyes",
                     "cataract", "glaucoma", "conjunctivitis"],
    
    # ENT (Ear, Nose, Throat)
    "ent": ["ear", "nose", "throat", "sinus", "hearing", "tinnitus", "sore throat",
           "tonsillitis", "earache", "nasal congestion"],
    
    # Urology
    "urology": ["urinary", "kidney", "bladder", "urination", "kidney stone", "uti",
               "prostate", "urinary tract"],
    
    # Gynecology
    "gynecology": ["menstrual", "period", "pregnancy", "ovarian", "uterine", "vaginal",
                  "menopause", "fertility"],
    
    # Pediatrics
    "pediatrics": ["child", "baby", "infant", "toddler", "pediatric", "children"],
    
    # Psychiatry
    "psychiatry": ["anxiety", "depression", "stress", "mental health", "panic", "mood",
                  "sleep disorder", "insomnia"],
    
    # Endocrinology
    "endocrinology": ["diabetes", "thyroid", "hormone", "blood sugar", "insulin", "metabolism"],
    
    # Pulmonology
    "pulmonology": ["lung", "asthma", "cough", "breathing", "respiratory", "pneumonia",
                   "bronchitis", "copd"]
}


def map_symptoms_to_specialty(user_input: str) -> Optional[str]:
    """
    Map user symptoms to appropriate medical specialty.
    
    Args:
        user_input: User's symptom description
        
    Returns:
        Specialty name or None if no match found
    """
    if not user_input:
        return None
    
    user_input_lower = user_input.lower()
    
    # Count matches for each specialty
    specialty_scores = {}
    
    for specialty, keywords in SYMPTOM_SPECIALTY_MAP.items():
        score = 0
        for keyword in keywords:
            if keyword in user_input_lower:
                score += 1
        
        if score > 0:
            specialty_scores[specialty] = score
    
    # Return specialty with highest score
    if specialty_scores:
        best_specialty = max(specialty_scores, key=specialty_scores.get)
        logger.info(f"Mapped symptoms '{user_input[:50]}...' to specialty: {best_specialty}")
        return best_specialty
    
    return None


def get_suggested_specialties(user_input: str, limit: int = 3) -> List[str]:
    """
    Get multiple suggested specialties based on symptoms.
    
    Args:
        user_input: User's symptom description
        limit: Maximum number of suggestions
        
    Returns:
        List of suggested specialties
    """
    if not user_input:
        return []
    
    user_input_lower = user_input.lower()
    specialty_scores = {}
    
    for specialty, keywords in SYMPTOM_SPECIALTY_MAP.items():
        score = 0
        for keyword in keywords:
            if keyword in user_input_lower:
                score += 1
        
        if score > 0:
            specialty_scores[specialty] = score
    
    # Sort by score and return top specialties
    sorted_specialties = sorted(specialty_scores.items(), key=lambda x: x[1], reverse=True)
    return [spec for spec, _ in sorted_specialties[:limit]]


# Human-readable specialty names
SPECIALTY_NAMES = {
    "cardiology": "Cardiology (Heart)",
    "orthopedics": "Orthopedics (Bones & Joints)",
    "neurology": "Neurology (Brain & Nerves)",
    "gastroenterology": "Gastroenterology (Digestive)",
    "dermatology": "Dermatology (Skin)",
    "ophthalmology": "Ophthalmology (Eyes)",
    "ent": "ENT (Ear, Nose, Throat)",
    "urology": "Urology (Urinary)",
    "gynecology": "Gynecology (Women's Health)",
    "pediatrics": "Pediatrics (Children)",
    "psychiatry": "Psychiatry (Mental Health)",
    "endocrinology": "Endocrinology (Hormones)",
    "pulmonology": "Pulmonology (Lungs)"
}


def get_specialty_display_name(specialty: str) -> str:
    """Get human-readable specialty name."""
    return SPECIALTY_NAMES.get(specialty, specialty.title())
