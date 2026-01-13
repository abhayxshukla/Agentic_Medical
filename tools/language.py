"""
Language Detection Module
Auto-detects language from user input without relying on frontend.
"""
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Supported Indian languages with their ISO codes
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'hi': 'Hindi',
    'ta': 'Tamil',
    'te': 'Telugu',
    'bn': 'Bengali',
    'mr': 'Marathi',
    'gu': 'Gujarati',
    'kn': 'Kannada',
    'ml': 'Malayalam',
    'pa': 'Punjabi',
    'or': 'Odia',
    'ur': 'Urdu'
}

# Unicode ranges for Indian scripts
LANGUAGE_SCRIPTS = {
    'hi': (0x0900, 0x097F),  # Devanagari (Hindi, Marathi, etc.)
    'ta': (0x0B80, 0x0BFF),  # Tamil
    'te': (0x0C00, 0x0C7F),  # Telugu
    'bn': (0x0980, 0x09FF),  # Bengali
    'gu': (0x0A80, 0x0AFF),  # Gujarati
    'kn': (0x0C80, 0x0CFF),  # Kannada
    'ml': (0x0D00, 0x0D7F),  # Malayalam
    'pa': (0x0A00, 0x0A7F),  # Gurmukhi (Punjabi)
    'or': (0x0B00, 0x0B7F),  # Odia
    'ur': (0x0600, 0x06FF),  # Arabic (Urdu)
}

# Common words/phrases for quick detection
LANGUAGE_KEYWORDS = {
    'hi': ['है', 'में', 'को', 'का', 'से', 'हो', 'रहा', 'दर्द', 'बुखार'],
    'ta': ['ஆகும்', 'இல்', 'உள்ள', 'வேண்டும்', 'வலி', 'காய்ச்சல்'],
    'te': ['ఉంది', 'లో', 'కు', 'నుండి', 'నొప్పి', 'జ్వరం'],
    'bn': ['হয়', 'এ', 'কে', 'থেকে', 'ব্যথা', 'জ্বর'],
    'mr': ['आहे', 'मध्ये', 'ला', 'पासून', 'वेदना', 'ताप'],
}


def detect_language(text: str) -> str:
    """
    Auto-detect language from text input.
    Returns ISO language code (e.g., 'en', 'hi', 'ta', 'bn').
    
    Strategy:
    1. Check for Unicode script ranges (most reliable)
    2. Check for language-specific keywords
    3. Default to English if no match
    
    Args:
        text: Input text to analyze
    
    Returns:
        ISO language code (default: 'en')
    """
    if not text or not text.strip():
        logger.warning("Empty text provided for language detection")
        return 'en'
    
    text = text.strip()
    
    # Step 1: Check Unicode script ranges (most reliable)
    script_counts = {}
    
    for lang_code, (start, end) in LANGUAGE_SCRIPTS.items():
        count = sum(1 for char in text if start <= ord(char) <= end)
        if count > 0:
            script_counts[lang_code] = count
    
    if script_counts:
        # Return language with most matching characters
        detected = max(script_counts.items(), key=lambda x: x[1])[0]
        logger.info(f"Detected language via Unicode: {detected} ({script_counts[detected]} matching chars)")
        return detected
    
    # Step 2: Check for language-specific keywords
    keyword_scores = {}
    
    for lang_code, keywords in LANGUAGE_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > 0:
            keyword_scores[lang_code] = score
    
    if keyword_scores:
        detected = max(keyword_scores.items(), key=lambda x: x[1])[0]
        logger.info(f"Detected language via keywords: {detected} (score: {keyword_scores[detected]})")
        return detected
    
    # Step 3: Check if text contains mostly ASCII (likely English)
    ascii_ratio = sum(1 for char in text if ord(char) < 128) / len(text) if text else 0
    
    if ascii_ratio > 0.8:
        logger.info("Detected language: English (ASCII characters)")
        return 'en'
    
    # Step 4: Try langdetect library if available (fallback)
    try:
        import langdetect
        from langdetect import DetectorFactory
        
        # Set seed for consistent results
        DetectorFactory.seed = 0
        
        detected = langdetect.detect(text)
        
        # Map langdetect codes to our supported languages
        lang_map = {
            'hi': 'hi',
            'ta': 'ta',
            'te': 'te',
            'bn': 'bn',
            'mr': 'mr',
            'gu': 'gu',
            'kn': 'kn',
            'ml': 'ml',
            'pa': 'pa',
            'or': 'or',
            'ur': 'ur'
        }
        
        if detected in lang_map:
            logger.info(f"Detected language via langdetect: {detected}")
            return lang_map[detected]
        
        # Default to English
        logger.info(f"langdetect returned {detected}, defaulting to English")
        return 'en'
        
    except ImportError:
        logger.warning("langdetect not available, using default detection")
    except Exception as e:
        logger.warning(f"langdetect error: {e}, defaulting to English")
    
    # Final fallback: English
    logger.info("Could not detect language, defaulting to English")
    return 'en'


def is_english(text: str) -> bool:
    """
    Quick check if text is likely English.
    
    Args:
        text: Text to check
    
    Returns:
        True if text appears to be English
    """
    return detect_language(text) == 'en'


def get_language_name(lang_code: str) -> str:
    """
    Get human-readable language name from ISO code.
    
    Args:
        lang_code: ISO language code
    
    Returns:
        Language name or code if not found
    """
    return SUPPORTED_LANGUAGES.get(lang_code, lang_code)
