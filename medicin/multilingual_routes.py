"""
Multilingual API Routes
FastAPI endpoints for multilingual medical assistance.
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from tools.language import detect_language, get_language_name
from tools.translation import translate_to_english, translate_from_english
from tools.medical_terminology import enhance_translation_with_medical_terms, translate_medical_term
from agents.models import AgentState
from agents.decision_agent import classify_severity

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/multilingual", tags=["multilingual"])

# Emergency disclaimer templates (will be translated)
EMERGENCY_DISCLAIMER_EN = (
    "⚠️ IMPORTANT: This is not a medical diagnosis. "
    "For emergencies, call 112 (India) or your local emergency number immediately. "
    "Always consult with qualified healthcare professionals for proper diagnosis and treatment."
)


class MultilingualTestRequest(BaseModel):
    """Request model for multilingual test endpoint."""
    message: str = Field(..., description="User message in any supported language")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "मेरे पिता को सीने में दर्द हो रहा है"
            }
        }


class MultilingualTestResponse(BaseModel):
    """Response model for multilingual test endpoint."""
    detected_language: str = Field(..., description="Detected ISO language code")
    language_name: str = Field(..., description="Human-readable language name")
    english_text: str = Field(..., description="Translated English text")
    translated_response: str = Field(..., description="Response translated back to user's language")
    severity: str = Field(..., description="Detected severity (critical/non_critical)")
    emergency: bool = Field(False, description="Emergency flag")


@router.post("/test", response_model=MultilingualTestResponse)
async def multilingual_test_endpoint(request: MultilingualTestRequest):
    """
    Test endpoint for multilingual support.
    
    Flow:
    1. Detect language from user input
    2. Translate to English
    3. Process with backend logic (severity classification)
    4. Translate response back to user's language
    5. Handle emergency cases with special care
    
    Args:
        request: User message in any supported language
    
    Returns:
        MultilingualTestResponse with translations and analysis
    """
    try:
        message = request.message.strip()
        
        if not message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Step 1: Detect language
        detected_lang = detect_language(message)
        language_name = get_language_name(detected_lang)
        
        logger.info(f"Detected language: {detected_lang} ({language_name})")
        
        # Step 2: Translate to English
        english_text = translate_to_english(message, detected_lang)
        logger.info(f"Translated to English: {english_text}")
        
        # Step 3: Process with backend logic
        severity = classify_severity(english_text)
        is_emergency = severity == "critical"
        
        # Step 4: Generate response (simplified for test)
        if is_emergency:
            response_en = (
                "🚨 This appears to be a critical medical situation. "
                "Please seek immediate medical attention. "
                "Call 112 for emergency assistance. "
                "This is not a medical diagnosis."
            )
        else:
            response_en = (
                "I understand your concern. "
                "For non-urgent medical questions, I recommend consulting with a healthcare professional. "
                "This is not a medical diagnosis."
            )
        
        # Step 5: Translate response back to user's language
        # For emergency cases, use simple structure and preserve critical info
        if is_emergency:
            # Emergency handling: lock language, simple structure
            translated_response = translate_from_english(response_en, detected_lang)
            
            # Enhance with medical terminology
            translated_response = enhance_translation_with_medical_terms(translated_response, detected_lang)
            
            # Ensure emergency number is preserved
            if "112" not in translated_response:
                # Add emergency number in user's language
                emergency_msg = translate_from_english("Call 112 for emergency", detected_lang)
                translated_response = f"{translated_response}\n\n{emergency_msg}"
        else:
            translated_response = translate_from_english(response_en, detected_lang)
            # Enhance with medical terminology
            translated_response = enhance_translation_with_medical_terms(translated_response, detected_lang)
        
        logger.info(f"Translated response to {detected_lang}: {translated_response[:50]}...")
        
        return MultilingualTestResponse(
            detected_language=detected_lang,
            language_name=language_name,
            english_text=english_text,
            translated_response=translated_response,
            severity=severity,
            emergency=is_emergency
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in multilingual test endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/supported-languages")
async def get_supported_languages():
    """Get list of supported languages."""
    from tools.language import SUPPORTED_LANGUAGES
    
    return {
        "supported_languages": [
            {"code": code, "name": name}
            for code, name in SUPPORTED_LANGUAGES.items()
        ],
        "total": len(SUPPORTED_LANGUAGES)
    }


@router.post("/translate-medical-term")
async def translate_medical_term_endpoint(
    term: str,
    target_lang: str,
    source_lang: str = "en"
):
    """Translate a medical term to target language."""
    try:
        translated = translate_medical_term(term, target_lang, source_lang)
        return {
            "original_term": term,
            "translated_term": translated,
            "source_language": source_lang,
            "target_language": target_lang
        }
    except Exception as e:
        logger.error(f"Error translating medical term: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def multilingual_health():
    """Health check for multilingual endpoints."""
    return {
        "status": "healthy",
        "service": "Multilingual API",
        "version": "1.0.0"
    }
