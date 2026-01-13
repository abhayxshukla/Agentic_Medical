"""
Medical Terminology Dictionary
Provides accurate medical term translations across multiple languages.
"""
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Medical terminology dictionary
MEDICAL_TERMS = {
    "en": {
        "chest pain": "chest pain",
        "headache": "headache",
        "fever": "fever",
        "cough": "cough",
        "nausea": "nausea",
        "vomiting": "vomiting",
        "diarrhea": "diarrhea",
        "dizziness": "dizziness",
        "shortness of breath": "shortness of breath",
        "heart attack": "heart attack",
        "stroke": "stroke",
        "emergency": "emergency",
        "hospital": "hospital",
        "doctor": "doctor",
        "medicine": "medicine",
        "prescription": "prescription"
    },
    "hi": {
        "chest pain": "सीने में दर्द",
        "headache": "सिरदर्द",
        "fever": "बुखार",
        "cough": "खांसी",
        "nausea": "मतली",
        "vomiting": "उल्टी",
        "diarrhea": "दस्त",
        "dizziness": "चक्कर आना",
        "shortness of breath": "सांस लेने में तकलीफ",
        "heart attack": "दिल का दौरा",
        "stroke": "स्ट्रोक",
        "emergency": "आपातकाल",
        "hospital": "अस्पताल",
        "doctor": "डॉक्टर",
        "medicine": "दवा",
        "prescription": "प्रिस्क्रिप्शन"
    },
    "ta": {
        "chest pain": "மார்பு வலி",
        "headache": "தலைவலி",
        "fever": "காய்ச்சல்",
        "cough": "இருமல்",
        "nausea": "குமட்டல்",
        "vomiting": "வாந்தி",
        "diarrhea": "வயிற்றுப்போக்கு",
        "dizziness": "தலைச்சுற்றல்",
        "shortness of breath": "மூச்சுத் திணறல்",
        "heart attack": "இதய நோய்",
        "stroke": "பக்கவாதம்",
        "emergency": "அவசரம்",
        "hospital": "மருத்துவமனை",
        "doctor": "மருத்துவர்",
        "medicine": "மருந்து",
        "prescription": "மருந்து பரிந்துரை"
    },
    "te": {
        "chest pain": "ఛాతీ నొప్పి",
        "headache": "తలనొప్పి",
        "fever": "జ్వరం",
        "cough": "దగ్గు",
        "nausea": "వికారం",
        "vomiting": "వాంతి",
        "diarrhea": "అతిసారం",
        "dizziness": "తలతిరగడం",
        "shortness of breath": "ఊపిరి తీసుకోవడంలో ఇబ్బంది",
        "heart attack": "గుండెపోటు",
        "stroke": "స్ట్రోక్",
        "emergency": "అత్యవసరం",
        "hospital": "ఆసుపత్రి",
        "doctor": "డాక్టర్",
        "medicine": "మందు",
        "prescription": "ప్రిస్క్రిప్షన్"
    }
}


def translate_medical_term(term: str, target_lang: str, source_lang: str = "en") -> str:
    """
    Translate medical term to target language.
    
    Args:
        term: Medical term to translate
        target_lang: Target language code
        source_lang: Source language code (default: en)
        
    Returns:
        Translated term or original if not found
    """
    term_lower = term.lower().strip()
    
    # If source is English, look up directly
    if source_lang == "en":
        if term_lower in MEDICAL_TERMS.get("en", {}):
            return MEDICAL_TERMS.get(target_lang, {}).get(term_lower, term)
    
    # If target is English, reverse lookup
    if target_lang == "en":
        for lang_code, terms in MEDICAL_TERMS.items():
            if lang_code != "en":
                for eng_term, translated_term in terms.items():
                    if translated_term.lower() == term_lower:
                        return eng_term
        return term
    
    # Cross-language translation via English
    if source_lang != "en":
        # First translate to English
        eng_term = None
        for eng_term_key, translated_term in MEDICAL_TERMS.get(source_lang, {}).items():
            if translated_term.lower() == term_lower:
                eng_term = eng_term_key
                break
        
        if eng_term:
            # Then translate to target language
            return MEDICAL_TERMS.get(target_lang, {}).get(eng_term, term)
    
    return term


def get_medical_terms_for_language(lang_code: str) -> Dict[str, str]:
    """Get all medical terms for a specific language."""
    return MEDICAL_TERMS.get(lang_code, {})


def enhance_translation_with_medical_terms(text: str, target_lang: str) -> str:
    """
    Enhance translation by replacing medical terms with dictionary terms.
    
    Args:
        text: Translated text
        target_lang: Target language
        
    Returns:
        Enhanced text with proper medical terminology
    """
    terms = MEDICAL_TERMS.get(target_lang, {})
    
    # Replace common medical terms
    enhanced_text = text
    for eng_term, translated_term in terms.items():
        # Case-insensitive replacement
        import re
        pattern = re.compile(re.escape(eng_term), re.IGNORECASE)
        enhanced_text = pattern.sub(translated_term, enhanced_text)
    
    return enhanced_text
