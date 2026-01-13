"""
Unified OCR + Medical Analysis + Geolocation Routes
Follows mandatory flow: OCR → Medical Analysis → Severity → Geolocation (only if medium/high)
"""
import logging
import uuid
from typing import Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, Request
from pydantic import BaseModel, Field
from medicin.ocr_service import extract_text_from_image, check_image_quality
from tools.medical_value_extractor import analyze_medical_report
from tools.document_location_extractor import extract_location_from_document
from tools.hospitals import find_nearest_hospitals, find_emergency_hospitals
from tools.geolocation import geocode_address, get_location_from_ip
import os
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ocr-geo", tags=["ocr-geolocation"])

UPLOAD_FOLDER = 'medicin/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'docx', 'doc', 'txt'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


class OCRGeoResponse(BaseModel):
    """Response for OCR + Medical Analysis + Geolocation."""
    extracted_text: str = Field(..., description="Text extracted from document")
    medical_analysis: dict = Field(..., description="Medical analysis with findings, severity, specialty")
    location_extracted: Optional[dict] = Field(None, description="Location extracted from document")
    location_used: Optional[dict] = Field(None, description="Location used for hospital search (only if severity >= medium)")
    hospitals: list = Field(default_factory=list, description="Nearby hospitals (only if severity >= medium)")
    message: str = Field(..., description="User-friendly message")


@router.post("/upload-and-analyze")
async def upload_and_analyze(
    file: UploadFile = File(...),
    request: Optional[Request] = None
):
    """
    Unified flow: OCR → Medical Analysis → Severity → Geolocation (only if medium/high)
    
    Flow:
    1. Upload document
    2. Extract text using OCR
    3. Extract medical values (rule-based)
    4. Assess severity (low/medium/high)
    5. Map to specialty
    6. IF severity >= medium: Get location → Find nearby doctors
    7. Return findings, severity, specialty, and doctors (if applicable)
    
    Args:
        file: Document file (PDF, image, DOCX)
        request: FastAPI Request (for IP geolocation fallback)
        
    Returns:
        OCRGeoResponse with medical analysis and doctors (if severity >= medium)
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file selected")
        
        ext = os.path.splitext(file.filename)[1].lower().lstrip('.')
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Read and save file
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File size exceeds 16 MB limit")
        
        session_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, f"{session_id}_{filename}")
        
        with open(filepath, 'wb') as f:
            f.write(content)
        
        # Step 1: Extract text based on file type
        extracted_text = ""
        
        if ext in ['png', 'jpg', 'jpeg']:
            # OCR for images
            quality = check_image_quality(filepath)
            if not quality.get("valid"):
                os.remove(filepath)
                raise HTTPException(status_code=422, detail=quality.get("reason", "Image quality too low"))
            
            extracted_text = extract_text_from_image(filepath)
            if not extracted_text or len(extracted_text.strip()) < 20:
                os.remove(filepath)
                raise HTTPException(
                    status_code=422,
                    detail="Could not extract sufficient text from image."
                )
        
        elif ext == 'pdf':
            # PDF text extraction
            from llama_index.readers.file import PDFReader  # type: ignore[attr-defined]
            reader = PDFReader()
            documents = reader.load_data(filepath)
            extracted_text = "\n".join([doc.text for doc in documents])
        
        elif ext in ['docx', 'doc']:
            # DOCX text extraction
            from llama_index.readers.file import DocxReader  # type: ignore[attr-defined]
            reader = DocxReader()
            documents = reader.load_data(filepath)
            extracted_text = "\n".join([doc.text for doc in documents])
        
        elif ext == 'txt':
            # Plain text
            with open(filepath, 'r', encoding='utf-8') as f:
                extracted_text = f.read()
        
        if not extracted_text or len(extracted_text.strip()) < 10:
            os.remove(filepath)
            raise HTTPException(
                status_code=422,
                detail="Could not extract text from document."
            )
        
        logger.info(f"Extracted {len(extracted_text)} characters from document")
        
        # Step 2: Medical Analysis (Rule-based)
        medical_analysis = analyze_medical_report(extracted_text)
        severity = medical_analysis.get("severity", "low")
        findings = medical_analysis.get("findings", [])
        recommended_specialty = medical_analysis.get("recommended_specialty")
        
        logger.info(f"Medical analysis: severity={severity}, findings={len(findings)}, specialty={recommended_specialty}")
        
        # Step 3: Extract location from document (for potential use)
        doc_location = extract_location_from_document(extracted_text)
        
        # Step 4: Geolocation ONLY if severity >= medium
        location_used = None
        hospitals = []
        
        if severity in ["medium", "high"]:
            # Determine location (priority: document > IP)
            final_location = None
            location_source = None
            
            if doc_location and doc_location.get('geocoded'):
                final_location = {
                    'lat': doc_location['lat'],
                    'lon': doc_location['lon'],
                    'address': doc_location.get('address')
                }
                location_source = 'document'
            
            if not final_location and request:
                # Fallback to IP geolocation
                try:
                    ip_result = get_location_from_ip(request)
                    if ip_result and ip_result.get('valid'):
                        final_location = {
                            'lat': ip_result['lat'],
                            'lon': ip_result['lon']
                        }
                        location_source = 'ip'
                except Exception as e:
                    logger.warning(f"IP geolocation failed: {e}")
            
            # Find hospitals if location available
            if final_location:
                lat = final_location['lat']
                lon = final_location['lon']
                location_used = {
                    'lat': lat,
                    'lon': lon,
                    'address': final_location.get('address'),
                    'source': location_source
                }
                
                # Find hospitals by specialty if available
                if recommended_specialty:
                    # Map specialty to internal format
                    specialty_map = {
                        "Cardiologist": "cardiology",
                        "Endocrinologist": "endocrinology",
                        "Hematologist": "hematology"
                    }
                    specialty_key = specialty_map.get(recommended_specialty, recommended_specialty.lower())
                    
                    hospitals = find_nearest_hospitals(
                        lat=lat,
                        lon=lon,
                        radius_km=10.0,
                        specialty=specialty_key,
                        limit=10
                    )
                
                # Fallback to general hospitals
                if not hospitals:
                    hospitals = find_nearest_hospitals(
                        lat=lat,
                        lon=lon,
                        radius_km=10.0,
                        limit=10
                    )
                
                logger.info(f"Found {len(hospitals)} hospitals for severity {severity}")
        
        # Step 5: Generate user-friendly message
        if severity == "high":
            message = "⚠️ High risk detected. Please consult a specialist soon."
        elif severity == "medium":
            message = "📋 Medium risk detected. Consider consulting a healthcare professional."
        else:
            message = "✅ No significant findings. Continue monitoring your health."
        
        if recommended_specialty:
            message += f" Recommended specialty: {recommended_specialty}."
        
        if hospitals:
            message += f" Found {len(hospitals)} nearby healthcare facilities."
        elif severity in ["medium", "high"]:
            message += " Share your location to find nearby doctors."
        
        return OCRGeoResponse(
            extracted_text=extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text,
            medical_analysis=medical_analysis,
            location_extracted=doc_location,
            location_used=location_used,
            hospitals=hospitals,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in OCR+Analysis endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
