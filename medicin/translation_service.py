from deep_translator import GoogleTranslator
import logging

logger = logging.getLogger(__name__)

# Expanded language support - Google Translate supports 100+ languages
SUPPORTED_LANGUAGES = {
    # European
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'nl': 'Dutch',
    'pl': 'Polish',
    'ru': 'Russian',
    'uk': 'Ukrainian',
    'sv': 'Swedish',
    'no': 'Norwegian',
    'da': 'Danish',
    'fi': 'Finnish',
    'cs': 'Czech',
    'ro': 'Romanian',
    'hu': 'Hungarian',
    'tr': 'Turkish',
    'el': 'Greek',
    
    # Asian
    'zh-CN': 'Chinese (Simplified)',
    'zh-TW': 'Chinese (Traditional)',
    'ja': 'Japanese',
    'ko': 'Korean',
    'th': 'Thai',
    'vi': 'Vietnamese',
    'id': 'Indonesian',
    'ms': 'Malay',
    
    # Middle Eastern
    'ar': 'Arabic',
    'he': 'Hebrew',
    'fa': 'Persian',
    
    # Indian
    'hi': 'Hindi',
    'bn': 'Bengali',
    'ta': 'Tamil',
    'te': 'Telugu',
    'mr': 'Marathi',
    'gu': 'Gujarati',
    'kn': 'Kannada',
    'ml': 'Malayalam',
    'pa': 'Punjabi',
    'ur': 'Urdu',
    
    # African
    'sw': 'Swahili',
    'af': 'Afrikaans',
    'zu': 'Zulu',
    
    # Others
    'fil': 'Filipino',
    'am': 'Amharic',
    'ne': 'Nepali',
    'si': 'Sinhala',
    'my': 'Burmese',
    'km': 'Khmer',
    'lo': 'Lao'
}


class UniversalTranslator:
    """
    Deep Translator for 100+ languages
    Works with ANY language Google Cloud Vision detects
    More reliable than googletrans library
    """
    
    def __init__(self):
        logger.info("✅ Universal Translator initialized (100+ languages supported)")
    
    def translate_to_english(self, text: str, source_lang: str = 'auto') -> str:
        """
        Translate ANY language to English
        
        Args:
            text: Text in any language
            source_lang: Language code (or 'auto' for auto-detection)
        """
        if not text or len(text.strip()) < 3:
            return text
        
        # If already English, return as-is
        if source_lang == 'en':
            return text
        
        try:
            logger.info(f"Translating from {source_lang} to English...")
            
            # Use GoogleTranslator with source and target
            translator = GoogleTranslator(source=source_lang, target='en')
            
            # Split long text into chunks (Google Translate limit is 5000 chars)
            if len(text) > 4500:
                # Split by sentences or paragraphs
                chunks = self._split_text(text, 4500)
                translated_chunks = []
                
                for chunk in chunks:
                    translated = translator.translate(chunk)
                    translated_chunks.append(translated)
                
                translated = ' '.join(translated_chunks)
            else:
                translated = translator.translate(text)
            
            logger.info(f"✅ Translation successful: {text[:50]}... → {translated[:50]}...")
            return translated
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            logger.warning("Returning original text")
            return text
    
    def translate_from_english(self, text: str, target_lang: str) -> str:
        """
        Translate English to ANY language
        
        Args:
            text: English text
            target_lang: Target language code
        """
        if target_lang == 'en' or not text or len(text.strip()) < 3:
            return text
        
        try:
            logger.info(f"Translating from English to {target_lang}...")
            
            translator = GoogleTranslator(source='en', target=target_lang)
            
            # Split long text into chunks
            if len(text) > 4500:
                chunks = self._split_text(text, 4500)
                translated_chunks = []
                
                for chunk in chunks:
                    translated = translator.translate(chunk)
                    translated_chunks.append(translated)
                
                translated = ' '.join(translated_chunks)
            else:
                translated = translator.translate(text)
            
            logger.info(f"✅ Translation successful: {text[:50]}... → {translated[:50]}...")
            return translated
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            logger.warning("Returning original text")
            return text
    
    def detect_language(self, text: str) -> str:
        """
        Auto-detect language for ANY text
        Works for 100+ languages
        """
        try:
            from langdetect import detect
            detected_lang = detect(text)
            
            lang_name = SUPPORTED_LANGUAGES.get(detected_lang, detected_lang.upper())
            logger.info(f"✅ Detected: {lang_name} ({detected_lang})")
            
            return detected_lang
            
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            # Fallback: check first character Unicode range
            if text and len(text) > 0:
                first_char = text[0]
                # Simple detection based on character ranges
                if '\u4e00' <= first_char <= '\u9fff':
                    return 'zh-CN'  # Chinese
                elif '\u0600' <= first_char <= '\u06ff':
                    return 'ar'  # Arabic
                elif '\u0900' <= first_char <= '\u097f':
                    return 'hi'  # Hindi
            
            return 'en'  # Default to English
    
    def get_language_name(self, lang_code: str) -> str:
        """Get human-readable language name"""
        return SUPPORTED_LANGUAGES.get(lang_code, lang_code.upper())
    
    def _split_text(self, text: str, max_length: int) -> list:
        """Split text into chunks for translation"""
        # Split by sentences or newlines
        sentences = text.replace('\n', '. ').split('. ')
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            if current_length + sentence_length > max_length:
                if current_chunk:
                    chunks.append('. '.join(current_chunk))
                current_chunk = [sentence]
                current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
        
        if current_chunk:
            chunks.append('. '.join(current_chunk))
        
        return chunks


# Singleton
_translator_instance = None

def get_translator():
    """Get or create universal translator instance"""
    global _translator_instance
    if _translator_instance is None:
        _translator_instance = UniversalTranslator()
    return _translator_instance
