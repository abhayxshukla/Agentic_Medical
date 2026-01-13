"""
Translation Module
Translates text between English and Indian languages.
Uses IndicTrans2 (AI4Bharat) as primary, Google Translate as fallback.
"""
import logging
import re
import os
from typing import Optional, Dict
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

# Supported languages
SUPPORTED_LANGUAGES = ['en', 'hi', 'ta', 'te', 'bn', 'mr', 'gu', 'kn', 'ml', 'pa', 'or', 'ur']

# Emergency keywords that should NOT be translated
EMERGENCY_KEYWORDS = [
    '112', '911', 'emergency', 'ambulance', 'hospital', 'doctor',
    'critical', 'urgent', 'immediate', 'help', 'assistance'
]

# Numbers pattern (preserve all numbers)
NUMBER_PATTERN = re.compile(r'\d+')


class TranslationEngine:
    """
    Translation engine with IndicTrans2 primary and Google Translate fallback.
    """
    
    def __init__(self):
        self.indic_trans = None
        self.google_translator = None
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Initialize translation engines."""
        # Try IndicTrans2 (AI4Bharat)
        # Note: IndicTrans2 requires model download and setup
        # For now, we'll use Google Translate as primary
        try:
            # Attempt to import IndicTrans2
            # This requires: pip install indic-trans
            # And model download from AI4Bharat
            try:
                from indicTrans.transliteration import xliterator
                from indicTrans.translation import indic2indic, indic2en, en2indic
                
                self.indic_trans = {
                    'xliterator': xliterator,
                    'indic2indic': indic2indic,
                    'indic2en': indic2en,
                    'en2indic': en2indic
                }
                logger.info("✅ IndicTrans2 initialized successfully")
            except ImportError:
                logger.warning("⚠️ IndicTrans2 not installed. Install with: pip install indic-trans")
                logger.info("Using Google Translate as primary translator")
                self.indic_trans = None
        except Exception as e:
            logger.warning(f"⚠️ IndicTrans2 initialization failed: {e}")
            logger.info("Falling back to Google Translate")
            self.indic_trans = None
        
        # Try Google Translate as fallback
        try:
            from googletrans import Translator
            self.google_translator = Translator()
            logger.info("✅ Google Translate initialized successfully")
        except ImportError:
            logger.warning("⚠️ Google Translate not available")
            self.google_translator = None
        except Exception as e:
            logger.warning(f"⚠️ Google Translate initialization failed: {e}")
            self.google_translator = None
    
    def translate_to_english(self, text: str, source_lang: str) -> str:
        """
        Translate text to English.
        
        Args:
            text: Source text
            source_lang: Source language ISO code
        
        Returns:
            Translated English text
        """
        if source_lang == 'en':
            return text
        
        if not text or not text.strip():
            return text
        
        # Preserve numbers and emergency keywords
        preserved = self._preserve_special_content(text)
        
        try:
            # Try IndicTrans2 first (if available)
            if self.indic_trans and source_lang in ['hi', 'ta', 'te', 'bn', 'mr', 'gu', 'kn', 'ml', 'pa', 'or', 'ur']:
                try:
                    # IndicTrans2 API may vary, handle different call patterns
                    translator_func = self.indic_trans.get('indic2en')
                    if translator_func:
                        if callable(translator_func):
                            translated = translator_func(text, src=source_lang, tgt='en')
                        else:
                            # If it's a model object, use translate method
                            translated = translator_func.translate(text, src=source_lang, tgt='en')
                        
                        if translated and translated.strip():
                            result = self._restore_special_content(translated, preserved)
                            logger.info(f"✅ IndicTrans2 translated {source_lang} → en")
                            return result
                except Exception as e:
                    logger.warning(f"IndicTrans2 translation failed: {e}, trying Google Translate")
            
            # Fallback to Google Translate
            if self.google_translator:
                try:
                    translated = self.google_translator.translate(
                        text,
                        src=source_lang,
                        dest='en'
                    )
                    if translated and translated.text:
                        result = self._restore_special_content(translated.text, preserved)
                        logger.info(f"✅ Google Translate translated {source_lang} → en")
                        return result
                except Exception as e:
                    logger.error(f"Google Translate error: {e}")
            
            logger.warning(f"Translation failed for {source_lang} → en, returning original")
            return text
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text
    
    def translate_from_english(self, text: str, target_lang: str) -> str:
        """
        Translate English text to target language.
        
        Args:
            text: English text
            target_lang: Target language ISO code
        
        Returns:
            Translated text in target language
        """
        if target_lang == 'en':
            return text
        
        if not text or not text.strip():
            return text
        
        # Preserve numbers and emergency keywords
        preserved = self._preserve_special_content(text)
        
        try:
            # Try IndicTrans2 first (if available)
            if self.indic_trans and target_lang in ['hi', 'ta', 'te', 'bn', 'mr', 'gu', 'kn', 'ml', 'pa', 'or', 'ur']:
                try:
                    # IndicTrans2 API may vary, handle different call patterns
                    translator_func = self.indic_trans.get('en2indic')
                    if translator_func:
                        if callable(translator_func):
                            translated = translator_func(text, src='en', tgt=target_lang)
                        else:
                            # If it's a model object, use translate method
                            translated = translator_func.translate(text, src='en', tgt=target_lang)
                        
                        if translated and translated.strip():
                            result = self._restore_special_content(translated, preserved)
                            logger.info(f"✅ IndicTrans2 translated en → {target_lang}")
                            return result
                except Exception as e:
                    logger.warning(f"IndicTrans2 translation failed: {e}, trying Google Translate")
            
            # Fallback to Google Translate
            if self.google_translator:
                try:
                    translated = self.google_translator.translate(
                        text,
                        src='en',
                        dest=target_lang
                    )
                    if translated and translated.text:
                        result = self._restore_special_content(translated.text, preserved)
                        logger.info(f"✅ Google Translate translated en → {target_lang}")
                        return result
                except Exception as e:
                    logger.error(f"Google Translate error: {e}")
            
            logger.warning(f"Translation failed for en → {target_lang}, returning original")
            return text
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text
    
    def _preserve_special_content(self, text: str) -> Dict[str, str]:
        """
        Preserve numbers and emergency keywords before translation.
        
        Args:
            text: Original text
        
        Returns:
            Dict mapping placeholders to original content
        """
        preserved = {}
        result = text
        
        # Preserve numbers
        numbers = NUMBER_PATTERN.findall(text)
        for i, num in enumerate(numbers):
            placeholder = f"__NUMBER_{i}__"
            preserved[placeholder] = num
            result = result.replace(num, placeholder, 1)
        
        # Preserve emergency keywords (case-insensitive)
        text_lower = result.lower()
        for keyword in EMERGENCY_KEYWORDS:
            if keyword.lower() in text_lower:
                # Find all occurrences
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                matches = pattern.finditer(result)
                for j, match in enumerate(matches):
                    placeholder = f"__EMERGENCY_{keyword.upper()}_{j}__"
                    preserved[placeholder] = match.group()
                    result = result[:match.start()] + placeholder + result[match.end():]
                    # Recalculate after replacement
                    matches = pattern.finditer(result)
        
        return preserved
    
    def _restore_special_content(self, translated: str, preserved: Dict[str, str]) -> str:
        """
        Restore preserved numbers and emergency keywords after translation.
        
        Args:
            translated: Translated text with placeholders
            preserved: Dict of placeholders to original content
        
        Returns:
            Text with restored content
        """
        result = translated
        for placeholder, original in preserved.items():
            result = result.replace(placeholder, original)
        return result


# Global translation engine instance
_translation_engine = None


def get_translation_engine() -> TranslationEngine:
    """Get or create global translation engine instance."""
    global _translation_engine
    if _translation_engine is None:
        _translation_engine = TranslationEngine()
    return _translation_engine


def translate_to_english(text: str, source_lang: str) -> str:
    """
    Translate text to English.
    
    Args:
        text: Source text
        source_lang: Source language ISO code
    
    Returns:
        Translated English text
    """
    engine = get_translation_engine()
    return engine.translate_to_english(text, source_lang)


def translate_from_english(text: str, target_lang: str) -> str:
    """
    Translate English text to target language.
    
    Args:
        text: English text
        target_lang: Target language ISO code
    
    Returns:
        Translated text in target language
    """
    engine = get_translation_engine()
    return engine.translate_from_english(text, target_lang)
