import cv2
import numpy as np
import boto3
import pytesseract
from typing import Optional, Dict
import logging
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

# Initialize AWS Textract client
try:
    textract_client = boto3.client(
        'textract',
        region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    logger.info("✅ AWS Textract client initialized successfully")
except Exception as e:
    logger.warning(f"⚠️ AWS Textract initialization failed: {e}")
    logger.warning("Will use Tesseract as fallback for all OCR")
    textract_client = None

# Usage tracking to stay within free tier
textract_usage_count = 0
TEXTRACT_MONTHLY_LIMIT = 900  # Stay under 1000 free tier


def extract_text_with_textract(image_path: str) -> Optional[Dict]:
    """
    Extract text using AWS Textract (handles both handwritten and printed)
    Returns dict with text and confidence
    """
    global textract_usage_count

    if textract_client is None:
        logger.warning("Textract client not available, skipping")
        return None
    
    try:
        # Read image file
        with open(image_path, 'rb') as document:
            image_bytes = document.read()
        
        # Check file size (Textract limit: 5MB for synchronous API)
        if len(image_bytes) > 5 * 1024 * 1024:
            logger.warning("Image too large for Textract (>5MB)")
            return None
        
        # Call Textract
        response = textract_client.detect_document_text(
            Document={'Bytes': image_bytes}
        )
        
        # Extract text with confidence
        text_lines = []
        confidences = []
        
        for block in response['Blocks']:
            if block['BlockType'] == 'LINE':
                text_lines.append(block['Text'])
                confidences.append(block['Confidence'])
        
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        extracted_text = '\n'.join(text_lines)
        
        # Increment usage counter
        textract_usage_count += 1
        
        logger.info(f"✅ Textract extracted {len(extracted_text)} chars "
                   f"with {avg_confidence:.1f}% confidence "
                   f"(Usage: {textract_usage_count}/{TEXTRACT_MONTHLY_LIMIT})")
        
        return {
            'text': extracted_text.strip(),
            'confidence': avg_confidence,
            'method': 'textract'
        }
        
    except textract_client.exceptions.InvalidParameterException as e:
        logger.error(f"Invalid image format for Textract: {e}")
        return None
    except textract_client.exceptions.ProvisionedThroughputExceededException:
        logger.warning("⚠️ Textract rate limit exceeded")
        return None
    except textract_client.exceptions.InvalidS3ObjectException:
        logger.error("Invalid S3 object for Textract")
        return None
    except Exception as e:
        logger.error(f"Textract error: {e}")
        return None


def extract_text_with_tesseract(image_path: str) -> Optional[Dict]:
    """
    Fallback OCR using Tesseract (only used if Textract fails or quota exceeded)
    """
    try:
        # Preprocess image
        img = cv2.imread(image_path)
        
        if img is None:
            logger.error(f"Could not read image: {image_path}")
            return None
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Enhanced preprocessing for medical documents
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        denoised = cv2.fastNlMeansDenoising(enhanced, None, 10, 7, 21)
        
        thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Extract text
        text = pytesseract.image_to_string(thresh, config="--oem 3 --psm 6")
        
        # Get confidence estimate
        data = pytesseract.image_to_data(
            thresh,
            config="--oem 3 --psm 6",
            output_type=pytesseract.Output.DICT
        )
        
        confidences = [int(conf) for conf in data['conf'] if conf != '-1' and int(conf) > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        logger.info(f"⚠️ Tesseract (fallback) extracted {len(text.strip())} chars "
                   f"with ~{avg_confidence:.1f}% confidence")
        
        return {
            'text': text.strip(),
            'confidence': avg_confidence,
            'method': 'tesseract'
        }
        
    except pytesseract.TesseractNotFoundError:
        logger.error("❌ Tesseract is not installed")
        return None
    except Exception as e:
        logger.error(f"Tesseract error: {e}")
        return None


def extract_text_from_image(image_path: str) -> Optional[str]:
    """
    Smart OCR with Textract primary, Tesseract fallback
    
    Strategy:
    1. Always try Textract first (handles both handwritten and printed)
    2. Use Tesseract only if:
       - Textract fails
       - Textract quota exceeded
       - Textract returns low confidence/empty result
    """
    logger.info(f"🔍 Starting OCR for: {image_path}")
    
    # Check if within Textract quota
    if textract_usage_count >= TEXTRACT_MONTHLY_LIMIT:
        logger.warning(f"⚠️ Textract monthly limit reached ({TEXTRACT_MONTHLY_LIMIT}), using Tesseract")
        result = extract_text_with_tesseract(image_path)
        return result['text'] if result else None
    
    # Primary: Try Textract (works for both handwritten and printed)
    logger.info("📤 Attempting Textract (handles handwritten + printed)...")
    result = extract_text_with_textract(image_path)
    
    # Check if Textract was successful
    if result and len(result['text']) >= 10 and result['confidence'] > 50:
        logger.info(f"✅ Textract successful!")
        return result['text']
    
    # Fallback: Use Tesseract if Textract failed or returned poor results
    logger.warning("⚠️ Textract failed or returned poor results, falling back to Tesseract...")
    fallback_result = extract_text_with_tesseract(image_path)
    
    if fallback_result and len(fallback_result['text']) >= 10:
        logger.info(f"✅ Tesseract fallback successful")
        return fallback_result['text']
    
    # Both methods failed
    logger.error("❌ Both Textract and Tesseract failed to extract text")
    return None


def check_image_quality(image_path: str) -> dict:
    """
    Validate image before OCR processing
    """
    try:
        img = cv2.imread(image_path)
        
        if img is None:
            return {"valid": False, "reason": "Cannot read image file"}
        
        height, width = img.shape[:2]
        file_size = os.path.getsize(image_path)
        
        # Check minimum dimensions
        if width < 100 or height < 100:
            return {"valid": False, "reason": "Image too small (minimum 100x100 pixels)"}
        
        # Check file size (5MB limit for Textract)
        if file_size > 5 * 1024 * 1024:
            return {
                "valid": False, 
                "reason": "Image too large (maximum 5MB for Textract)"
            }
        
        # Check if image is too blurry
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


# Keep for backward compatibility (your original function name)
def preprocess_image(image_path):
    """
    Legacy function - kept for compatibility
    Now just a wrapper for the new implementation
    """
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    return thresh
