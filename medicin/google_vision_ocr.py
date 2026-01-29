from google.cloud import vision
import os
import logging
import cv2

logger = logging.getLogger(__name__)

# Set credentials path
CREDENTIALS_PATH = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'google-vision-credentials.json')
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = CREDENTIALS_PATH

def check_image_quality(image_path: str) -> dict:
    """Check if image is suitable for OCR"""
    try:
        img = cv2.imread(image_path)
        
        if img is None:
            return {"valid": False, "reason": "Cannot read image file"}
        
        height, width = img.shape[:2]
        file_size = os.path.getsize(image_path)
        
        if width < 100 or height < 100:
            return {"valid": False, "reason": "Image too small (minimum 100x100 pixels)"}
        
        if file_size > 20 * 1024 * 1024:
            return {"valid": False, "reason": "Image too large (maximum 20 MB for Google Vision)"}
        
        # Check blur
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        if laplacian_var < 50:
            return {
                "valid": True,
                "warning": "Image may be blurry",
                "blur_score": laplacian_var
            }
        
        return {
            "valid": True,
            "dimensions": f"{width}x{height}",
            "file_size_mb": round(file_size / (1024*1024), 2),
            "blur_score": laplacian_var
        }
        
    except Exception as e:
        return {"valid": False, "reason": f"Error checking image: {str(e)}"}


def extract_text_with_google_vision(image_path: str) -> dict:
    """
    Extract text using Google Cloud Vision API
    Automatically detects and supports ALL Indian languages
    """
    try:
        logger.info(f"🔍 Using Google Vision API for: {image_path}")
        
        # Initialize Google Vision client
        client = vision.ImageAnnotatorClient()
        
        # Read image file
        with open(image_path, 'rb') as image_file:
            content = image_file.read()
        
        image = vision.Image(content=content)
        
        # Perform document text detection (best for multi-language documents)
        response = client.document_text_detection(image=image)
        
        # Check for errors
        if response.error.message:
            raise Exception(f"Google Vision API error: {response.error.message}")
        
        # Extract full text
        full_text = response.full_text_annotation.text
        
        if not full_text or len(full_text.strip()) < 5:
            logger.warning("Google Vision returned no text")
            return None
        
        # Extract detected languages
        detected_languages = []
        for page in response.full_text_annotation.pages:
            for block in page.blocks:
                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        if hasattr(word.property, 'detected_languages'):
                            for lang in word.property.detected_languages:
                                if lang.language_code not in detected_languages:
                                    detected_languages.append(lang.language_code)
        
        # Get confidence (average from pages)
        confidences = []
        for page in response.full_text_annotation.pages:
            if hasattr(page, 'confidence') and page.confidence > 0:
                confidences.append(page.confidence)
        
        avg_confidence = (sum(confidences) / len(confidences) * 100) if confidences else 95
        
        # Map Google's language codes to our codes
        lang_map = {
            'hi': 'hi',    # Hindi
            'bn': 'bn',    # Bengali
            'ta': 'ta',    # Tamil
            'te': 'te',    # Telugu
            'kn': 'kn',    # Kannada
            'ml': 'ml',    # Malayalam
            'mr': 'mr',    # Marathi
            'gu': 'gu',    # Gujarati
            'pa': 'pa',    # Punjabi
            'or': 'or',    # Odia
            'as': 'as',    # Assamese
            'ur': 'ur',    # Urdu
            'en': 'en'     # English
        }
        
        primary_lang = detected_languages[0] if detected_languages else 'en'
        our_lang_code = lang_map.get(primary_lang, 'en')
        
        logger.info(f"✅ Google Vision extracted {len(full_text)} chars")
        logger.info(f"Detected languages: {detected_languages}")
        logger.info(f"Confidence: {avg_confidence:.1f}%")
        logger.info(f"Preview: {full_text[:200]}...")
        
        return {
            'text': full_text,
            'confidence': avg_confidence,
            'detected_language_code': primary_lang,
            'all_detected_languages': detected_languages,
            'method': 'google_vision'
        }
        
    except Exception as e:
        logger.error(f"❌ Google Vision error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def extract_text_from_image_multilingual(image_path: str) -> dict:
    """
    Extract and translate text from documents in ANY language
    Using Google Vision (200+ languages) + Deep Translator (100+ languages)
    """
    from medicin.translation_service import get_translator
    
    logger.info(f"🔍 Starting universal multilingual OCR for: {image_path}")
    
    # Step 1: Extract text with Google Vision (supports 200+ languages)
    result = extract_text_with_google_vision(image_path)
    
    if not result:
        logger.error("❌ Google Vision OCR failed")
        return None
    
    extracted_text = result['text']
    detected_google_langs = result.get('all_detected_languages', [])
    primary_google_lang = result.get('detected_language_code', 'en')
    
    logger.info(f"Google Vision detected languages: {detected_google_langs}")
    
    # Step 2: Use Google Vision's primary detected language (most reliable)
    detected_lang = primary_google_lang if primary_google_lang != 'und' else 'en'
    
    # Get translator instance
    translator = get_translator()
    language_name = translator.get_language_name(detected_lang)
    
    logger.info(f"✅ Final detected language: {language_name} ({detected_lang})")
    
    # Step 3: Translate to English (if not already English)
    english_text = extracted_text
    if detected_lang != 'en':
        logger.info(f"🌐 Translating {language_name} → English...")
        english_text = translator.translate_to_english(extracted_text, detected_lang)
        logger.info(f"✅ Translation complete: {english_text[:100]}...")
    else:
        logger.info("✅ Text is already in English, no translation needed")
    
    return {
        'original_text': extracted_text,
        'detected_language': detected_lang,
        'english_text': english_text,
        'language_name': language_name,
        'confidence': result.get('confidence', 0),
        'method': 'google_vision',
        'all_detected_languages': detected_google_langs
    }




