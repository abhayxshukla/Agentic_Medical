import urllib.parse
import os
import uuid
from typing import List, Dict, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException
from starlette.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.core.memory import Memory
from datetime import datetime
from llama_index.core.chat_engine import SimpleChatEngine, ContextChatEngine
from llama_index.core import Settings
from medicin.ocr_service import check_image_quality, extract_text_from_image
from medicin.google_vision_ocr import extract_text_from_image_multilingual, check_image_quality as google_check_quality
from medicin.translation_service import get_translator, SUPPORTED_LANGUAGES
from llama_index.core.schema import Document
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.readers.file import PDFReader, DocxReader
from medicin.sharedembeddings import get_shared_embedding
from werkzeug.utils import secure_filename
from medicin.geolocation_service import (
    find_nearby_hospitals_google,  # Changed from overpass
    format_hospitals_for_chat,
    extract_specialty_from_symptoms_hybrid,  # Changed to hybrid with LLM  
)

import logging
translator = get_translator()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Medical Assistant API",
    description="AI-powered medical assistant with symptom analysis and document processing",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize LLM
# llm = OpenAI(
#     model="gpt-5",
#     api_key=os.getenv("OPENAI_API_KEY"),
#     temperature=0.0,     # VERY important for medical + classification
#     max_tokens=512       # Safe default, override per-call if needed
# )
llm = GoogleGenAI(
    model="gemini-2.5-flash",
    api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.0,     # VERY important for medical + classification
    timeout=30,          # seconds
)

Settings.llm = llm
Settings.embed_model = get_shared_embedding()

# Database configuration
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')

encoded_password = urllib.parse.quote_plus(DB_PASSWORD)
connection_string = f"postgresql+psycopg2://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
async_connection_string = f"postgresql+asyncpg://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Medicine database vector store
vector_store = PGVectorStore(
    connection_string=connection_string,
    async_connection_string=async_connection_string,
    table_name="medicine_db",
    embed_dim=1024,
    perform_setup=False,
    schema_name="vector"
)

medicine_index = VectorStoreIndex.from_vector_store(
    vector_store=vector_store,
    embed_model=Settings.embed_model
)
logger.info("Medicine database index loaded successfully")

# Medicine recommendation retriever
medicine_retriever = VectorIndexRetriever(index=medicine_index, similarity_top_k=3)

# Prompts
medicine_prompt = (
    "You are a medical assistant. Based on the symptoms and medical context provided, "
    "recommend appropriate medicines. Be specific about dosage and usage instructions.\n\n"
    "Context: {context_str}\n"
    "Symptoms/Query: {query_str}\n"
)

medicine_chat_engine = ContextChatEngine.from_defaults(
    retriever=medicine_retriever,
    context_template=medicine_prompt,
    llm=llm,
)

symptom_prompt = (
    """You are a friendly and empathetic medical assistant. Have a natural conversation 
    with the user about their health concerns. Ask one question at a time to understand:
    - Main symptoms
    - Duration and severity
    - Affected body parts
    - Any triggers or patterns
    
    Keep the conversation to 6-8 questions maximum. Be empathetic and caring.
    When you have enough information, respond with exactly "SYMPTOMS_COMPLETE" to conclude."""
)

# Session storage
user_sessions = {}

# File upload configuration
UPLOAD_FOLDER = 'medicin/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'docx', 'doc', 'txt'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Pydantic models for request/response validation
class ChatMessage(BaseModel):
    session_id: str
    message: str

class SessionResponse(BaseModel):
    session_id: str
    response: str
    status: str = "started"

class ChatResponse(BaseModel):
    status: str
    response: Optional[str] = None
    symptoms_summary: Optional[str] = None
    medicine_recommendation: Optional[str] = None
    session_id: str

class DocumentChatRequest(BaseModel):
    session_id: str
    message: str

class DocumentChatResponse(BaseModel):
    response: str
    document: str
    session_id: str

class UploadResponse(BaseModel):
    session_id: str
    filename: str
    message: str
    pages: int

class DeleteSessionRequest(BaseModel):
    session_id: str

class DeleteSessionResponse(BaseModel):
    message: str
    session_id: str

class SessionInfoResponse(BaseModel):
    session_id: str
    type: str
    filename: Optional[str] = None
    pages: Optional[int] = None

class LocationRequest(BaseModel):
    pin_code: str
    specialty: Optional[str] = None
    radius_km: float = 10


class LocationResponse(BaseModel):
    status: str
    pin_code: str
    hospitals: List[Dict]
    formatted_response: str
    location: Optional[Dict] = None


class ChatWithLocationRequest(BaseModel):
    session_id: str
    message: str
    pin_code: Optional[str] = None

class MultilingualUploadResponse(BaseModel):
    session_id: str
    filename: str
    message: str
    pages: int
    detected_language: str
    language_name: str


class MultilingualChatRequest(BaseModel):
    session_id: str
    message: str
    response_language: str = 'en'  # User can choose response language


class MultilingualChatResponse(BaseModel):
    response_english: str
    response_translated: str
    language: str
    document: str
    session_id: str



def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==================== ENDPOINTS ====================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Medical Assistant API",
        "version": "1.0.0"
    }

async def extract_specialty_safe(
    text: str,
    llm_instance
) -> str:
    """
    Thread-safe wrapper for Gemini specialty extraction.
    MUST be used inside FastAPI async endpoints.
    """
    return await run_in_threadpool(
        extract_specialty_from_symptoms_hybrid,
        text,
        llm_instance,
        True
    )

# Add this after your existing imports and configuration
def get_combined_documents(prescription_docs: List[Document], include_medicine_db: bool = True) -> List[Document]:
    """
    Combine prescription documents with medicine database documents
    
    Args:
        prescription_docs: Documents from uploaded prescription
        include_medicine_db: Whether to include medicine database
    
    Returns:
        Combined list of documents
    """
    if not include_medicine_db:
        return prescription_docs
    
    try:
        # Query medicine database for relevant medicines
        # Extract medicine names from prescription
        prescription_text = " ".join([doc.text for doc in prescription_docs])
        
        # Search medicine database
        medicine_results = medicine_retriever.retrieve(prescription_text)
        
        # Convert to Document objects
        medicine_docs = [
            Document(
                text=node.text,
                metadata={
                    **node.metadata,
                    "source": "medicine_database",
                    "type": "medicine_info"
                }
            )
            for node in medicine_results
        ]
        
        logger.info(f"Added {len(medicine_docs)} medicine database documents to context")
        
        # Combine: prescription first, then medicine database
        return prescription_docs + medicine_docs
        
    except Exception as e:
        logger.error(f"Error fetching medicine database docs: {e}")
        return prescription_docs  # Fallback to just prescription


# ==================== FLOW 1: WITHOUT DOCUMENT ====================

@app.post("/start_symptom_chat", response_model=SessionResponse)
async def start_symptom_chat():
    """Initialize a new symptom-based conversation"""
    try:
        session_id = str(uuid.uuid4())
        
        # Create new memory for this session
        chat_memory = Memory.from_defaults(token_limit=40000)
        
        symptom_engine = SimpleChatEngine.from_defaults(
            llm=llm,
            system_prompt=symptom_prompt,
            memory=chat_memory,
        )
        
        # Store session
        user_sessions[session_id] = {
            'type': 'symptom',
            'engine': symptom_engine,
            'memory': chat_memory
        }
        
        # Start conversation
        initial_response = symptom_engine.chat("Hello")
        
        logger.info(f"Started symptom chat session: {session_id}")
        
        return SessionResponse(
            session_id=session_id,
            response=str(initial_response),
            status="started"
        )
        
    except Exception as e:
        logger.error(f"Error starting symptom chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat_symptoms", response_model=ChatResponse)
async def chat_symptoms(request: ChatMessage):
    """Continue symptom conversation and get medicine recommendation"""
    try:
        if not request.session_id or request.session_id not in user_sessions:
            raise HTTPException(status_code=400, detail="Invalid session_id")
        
        session = user_sessions[request.session_id]
        
        if session['type'] != 'symptom':
            raise HTTPException(status_code=400, detail="This session is not for symptom chat")
        
        # Continue conversation
        response = await run_in_threadpool(
            session['chat_engine'].chat,
            request.message
        )

        response_text = str(response)
        
        # Check if symptom gathering is complete
        if "SYMPTOMS_COMPLETE" in response_text:
            # Extract all user messages (symptoms)
            all_messages = session['memory'].get_all()
            user_symptoms = " ".join([m.content for m in all_messages if m.role == "user"])
            
            # Get medicine recommendation from database
            medicine_response = medicine_chat_engine.chat(user_symptoms)
            
            logger.info(f"Symptom assessment complete for session: {request.session_id}")
            
            return ChatResponse(
                status="complete",
                symptoms_summary=user_symptoms,
                medicine_recommendation=str(medicine_response),
                session_id=request.session_id
            )
        else:
            return ChatResponse(
                status="ongoing",
                response=response_text,
                session_id=request.session_id
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in symptom chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== FLOW 2: WITH DOCUMENT ====================

@app.post("/upload_document", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload medical document (blood report, prescription, etc.)"""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file selected")
        
        if not allowed_file(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Read file content
        content = await file.read()
        
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File size exceeds 16 MB limit")
        
        # Create new session
        session_id = str(uuid.uuid4())
        
        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, f"{session_id}_{filename}")
        
        with open(filepath, 'wb') as f:
            f.write(content)
        
        # Configure readers for different file types
        file_extractors = {
          ".pdf": PDFReader(),
          ".docx": DocxReader(),
          ".doc": DocxReader()
        }
        
        # Load and index the document
        documents = []
        ext = os.path.splitext(filepath)[1].lower()

        if ext in [".png", ".jpg", ".jpeg"]:
            quality = check_image_quality(filepath)

            if not quality["valid"]:
                if os.path.exists(filepath):
                    os.remove(filepath)
                
                raise HTTPException(
                    status_code=422,
                    detail=quality["reason"]
                )
            
            logger.info(f"Processing image: {filename}")
            ocr_text = extract_text_from_image(filepath)

            if not ocr_text or len(ocr_text.strip()) < 20:
                if os.path.exists(filepath):
                    os.remove(filepath)
                raise HTTPException(
                    status_code=422,
                    detail="Could not extract sufficient text from image. "
                   "Please ensure the image is clear and contains readable text."
                )
            
            documents.append(Document(
                text=ocr_text,
                metadata={
                    "source": filename,
                    "type": "ocr_image",
                    "quality_check": quality
                    }
            ))

        else:
            documents = SimpleDirectoryReader(
            input_files=[filepath],
            file_extractor=file_extractors
        ).load_data()

        
        if not documents:
            raise HTTPException(status_code=500, detail="Could not extract content from document")
        
        # Create index from document
        document_index = VectorStoreIndex.from_documents(
            documents,
            embed_model=Settings.embed_model
        )

        doc_medicine_prompt = (
            "You are a medical assistant analyzing medical documents. "
            "Based on the medical report/document content and the user's question, "
            "provide appropriate medicine recommendations with dosage and usage instructions.\n\n"
            "Document Content: {context_str}\n"
            "User Question: {query_str}\n\n"
            "Provide a clear medical recommendation based on the document."
        )

        doc_chat_engine = ContextChatEngine.from_defaults(
            retriever=VectorIndexRetriever(index=document_index, similarity_top_k=4),
            context_template=doc_medicine_prompt,
            llm=llm,
            memory=Memory.from_defaults(token_limit=40000)
        )
        
        # Store session
        user_sessions[session_id] = {
            'type': 'document',
            'index': document_index,
            'chat_engine': doc_chat_engine,  # NEW: Store persistent engine
            'filename': filename,
            'filepath': filepath,
            'documents': documents,
            'created_at': datetime.utcnow(),  # NEW: Track creation time
            'last_accessed': datetime.utcnow()  # NEW: Track last access
        }
        
        logger.info(f"Document uploaded successfully: {filename} (session: {session_id})")
        
        return UploadResponse(
            session_id=session_id,
            filename=filename,
            message="Document uploaded and processed successfully",
            pages=len(documents)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat_with_document", response_model=DocumentChatResponse)
async def chat_with_document(request: DocumentChatRequest):
    """Chat about uploaded document and get medicine recommendations"""
    try:
        if not request.session_id or request.session_id not in user_sessions:
            raise HTTPException(
                status_code=404,
                detail="Invalid session_id. Please upload a document first."
            )
        
        session = user_sessions[request.session_id]
        
        if session['type'] != 'document':
            raise HTTPException(status_code=400, detail="This session does not have a document")
        
        if not request.message:
            raise HTTPException(status_code=400, detail="No message provided")
        
        # ✅ Update last accessed time
        session['last_accessed'] = datetime.utcnow()
        
        # ✅ Use the STORED chat engine (preserves conversation history)
        response = await run_in_threadpool(
            session['chat_engine'].chat,
            request.message
        )

        
        logger.info(f"Document query processed for session: {request.session_id}")
        
        return DocumentChatResponse(
            response=str(response),
            document=session['filename'],
            session_id=request.session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in document chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    

# ==================== GEOLOCATION ENDPOINTS ====================

@app.post("/find_nearby_hospitals", response_model=LocationResponse)
async def find_nearby_hospitals(request: LocationRequest):
    """
    Find nearby hospitals/clinics using Google Maps Places API.
    Includes ratings, reviews, and business hours.
    """
    try:
        # Validate PIN code format
        if not request.pin_code or len(request.pin_code) != 6 or not request.pin_code.isdigit():
            raise HTTPException(
                status_code=400,
                detail="Invalid PIN code. Must be 6 digits."
            )
        
        # Search for hospitals using Google Maps
        geo_result = find_nearby_hospitals_google(  # Changed function name
            pin_code=request.pin_code,
            specialty=request.specialty,
            radius_km=request.radius_km
        )
        
        if geo_result['status'] != 'success':
            raise HTTPException(status_code=404, detail=geo_result['message'])
        
        # Format for display
        formatted = format_hospitals_for_chat(geo_result)
        
        logger.info(f"Google Maps query: PIN {request.pin_code}, "  # Updated log message
                   f"Specialty: {request.specialty or 'Any'}, "
                   f"Found: {len(geo_result['hospitals'])}")
        
        return LocationResponse(
            status=geo_result['status'],
            pin_code=geo_result['pin_code'],
            hospitals=geo_result['hospitals'],
            formatted_response=formatted,
            location=geo_result.get('location')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in hospital search: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/chat_symptoms_with_location")
async def chat_symptoms_with_location(request: ChatWithLocationRequest):
    """
    Enhanced symptom chat with Google Maps hospital recommendations.
    """
    try:
        if not request.session_id or request.session_id not in user_sessions:
            raise HTTPException(status_code=400, detail="Invalid session_id")
        
        session = user_sessions[request.session_id]
        
        if session['type'] != 'symptom':
            raise HTTPException(status_code=400, detail="This session is not for symptom chat")
        
        response = await run_in_threadpool(
            session['chat_engine'].chat,
            request.message
        )

        response_text = str(response)
        
        if "SYMPTOMS_COMPLETE" in response_text:
            all_messages = session['memory'].get_all()
            user_symptoms = " ".join([m.content for m in all_messages if m.role == "user"])
            
            medicine_response = medicine_chat_engine.chat(user_symptoms)
            
            location_info = None
            if request.pin_code:
                # Changed: Use LLM-based specialty extraction
                specialty = await extract_specialty_safe(
                    user_symptoms,
                    llm
                )

                
                logger.info(f"Google Maps search: PIN {request.pin_code}, "
                           f"specialty: {specialty or 'General'}")
                
                # Changed: Use Google Maps function
                geo_result = find_nearby_hospitals_google(
                    pin_code=request.pin_code,
                    specialty=specialty,
                    radius_km=10
                )
                
                if geo_result['status'] == 'success':
                    location_info = {
                        'hospitals': geo_result['hospitals'],
                        'formatted': format_hospitals_for_chat(geo_result),
                        'specialty_detected': specialty
                    }
            
            return {
                "status": "complete",
                "symptoms_summary": user_symptoms,
                "medicine_recommendation": str(medicine_response),
                "location_info": location_info,
                "session_id": request.session_id
            }
        else:
            return {
                "status": "ongoing",
                "response": response_text,
                "session_id": request.session_id
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in symptom chat with location: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat_document_with_location")
async def chat_document_with_location(request: ChatWithLocationRequest):
    """
    Enhanced document chat with Google Maps hospital recommendations.
    Always searches for hospitals when PIN code is provided.
    """
    try:
        if not request.session_id or request.session_id not in user_sessions:
            raise HTTPException(status_code=404, detail="Invalid session_id")
        
        session = user_sessions[request.session_id]
        
        if session['type'] != 'document':
            raise HTTPException(status_code=400, detail="This session does not have a document")
        
        session['last_accessed'] = datetime.utcnow()
        
        # Get LLM response about the document
        response = await run_in_threadpool(
            session['chat_engine'].chat,
            request.message
        )

        response_text = str(response)
        
        location_info = None
        
        # Search for hospitals if PIN code is provided
        if request.pin_code:
            
            # Extract specialty from LLM's response
            specialty = await extract_specialty_safe(
                response_text,
                llm
            )

            
            logger.info(f"Finding hospitals for PIN {request.pin_code}, "
                       f"specialty detected: {specialty}")
            
            # Search hospitals with Google Maps
            geo_result = find_nearby_hospitals_google(
                pin_code=request.pin_code,
                specialty=specialty,
                radius_km=10
            )
            
            if geo_result['status'] == 'success' and len(geo_result['hospitals']) > 0:
                location_info = {
                    'hospitals': geo_result['hospitals'],
                    'formatted': format_hospitals_for_chat(geo_result),
                    'specialty_detected': specialty
                }
                logger.info(f"Found {len(geo_result['hospitals'])} hospitals for {specialty}")
            else:
                logger.warning(f"No hospitals found for PIN {request.pin_code}, specialty {specialty}")
        
        return {
            "response": response_text,
            "document": session['filename'],
            "location_info": location_info,
            "session_id": request.session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in document chat with location: {e}")
        raise HTTPException(status_code=500, detail=str(e))



    

@app.post("/upload_multilingual_document", response_model=MultilingualUploadResponse)
async def upload_multilingual_document(file: UploadFile = File(...)):
    """
    Upload medical document in ANY LANGUAGE.
    Automatically includes medicine database for comprehensive answers.
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file selected")
        
        if not allowed_file(file.filename):
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
        
        # Process based on file type
        ext = os.path.splitext(filepath)[1].lower()
        
        if ext in [".png", ".jpg", ".jpeg"]:
            quality = google_check_quality(filepath)
            
            if not quality["valid"]:
                if os.path.exists(filepath):
                    os.remove(filepath)
                raise HTTPException(status_code=422, detail=quality["reason"])
            
            logger.info(f"Processing multilingual image: {filename}")
            
            # Use Google Vision + Deep Translator
            ocr_result = extract_text_from_image_multilingual(filepath)
            
            if not ocr_result or len(ocr_result['english_text'].strip()) < 20:
                if os.path.exists(filepath):
                    os.remove(filepath)
                raise HTTPException(
                    status_code=422,
                    detail="Could not extract sufficient text from image."
                )
            
            # Create document with English text
            prescription_docs = [Document(
                text=ocr_result['english_text'],
                metadata={
                    "source": filename,
                    "type": "ocr_image_multilingual",
                    "original_language": ocr_result['detected_language'],
                    "language_name": ocr_result['language_name'],
                    "original_text": ocr_result['original_text'],
                    "confidence": ocr_result.get('confidence', 0),
                    "method": ocr_result.get('method', 'google_vision')
                }
            )]
            
        else:
            # PDF/DOCX processing
            file_extractors = {
                ".pdf": PDFReader(),
                ".docx": DocxReader(),
                ".doc": DocxReader()
            }
            
            prescription_docs = SimpleDirectoryReader(
                input_files=[filepath],
                file_extractor=file_extractors
            ).load_data()
            
            ocr_result = {
                'detected_language': 'en',
                'language_name': 'English'
            }
        
        if not prescription_docs:
            raise HTTPException(status_code=500, detail="Could not extract content from document")
        
        # 🆕 COMBINE PRESCRIPTION + MEDICINE DATABASE
        all_documents = get_combined_documents(prescription_docs, include_medicine_db=True)
        
        logger.info(f"Creating index with {len(all_documents)} documents "
                   f"({len(prescription_docs)} prescription + {len(all_documents) - len(prescription_docs)} medicine DB)")
        
        # Create unified index
        document_index = VectorStoreIndex.from_documents(
            all_documents,
            embed_model=Settings.embed_model
        )
        
        # Enhanced prompt with medicine database context
        doc_medicine_prompt = (
            "You are a medical assistant with access to both the uploaded prescription "
            "and a comprehensive medicine database.\n\n"
            "When answering questions:\n"
            "- For 'What medicines are mentioned?': Focus on the prescription\n"
            "- For 'Alternative medicines' or 'Substitutes': Use the medicine database to suggest "
            "generic versions, cheaper alternatives, or similar medicines\n"
            "- For 'Side effects', 'Dosage', 'Interactions': Combine prescription info with database knowledge\n\n"
            "Context (Prescription + Medicine Database): {context_str}\n"
            "User Question: {query_str}\n\n"
            "Provide comprehensive, accurate medical information."
        )
        
        doc_chat_engine = ContextChatEngine.from_defaults(
            retriever=VectorIndexRetriever(
                index=document_index, 
                similarity_top_k=6  # 🆕 Increased from 4 to get more context
            ),
            context_template=doc_medicine_prompt,
            llm=llm,
            memory=Memory.from_defaults(token_limit=40000)
        )
        
        # Store session
        user_sessions[session_id] = {
            'type': 'multilingual_document',
            'index': document_index,
            'chat_engine': doc_chat_engine,
            'filename': filename,
            'filepath': filepath,
            'documents': prescription_docs,  # Store original prescription docs
            'all_documents': all_documents,  # Store combined docs
            'detected_language': ocr_result.get('detected_language', 'en'),
            'language_name': ocr_result.get('language_name', 'English'),
            'created_at': datetime.utcnow(),
            'last_accessed': datetime.utcnow(),
            'has_medicine_db': True  # 🆕 Flag to indicate DB access
        }
        
        logger.info(f"Multilingual document with medicine DB uploaded: {filename} "
                   f"({ocr_result.get('language_name', 'Unknown')})")
        
        return MultilingualUploadResponse(
            session_id=session_id,
            filename=filename,
            message=f"Document processed successfully in {ocr_result.get('language_name', 'Unknown')} "
                   f"with medicine database access",
            pages=len(prescription_docs),
            detected_language=ocr_result.get('detected_language', 'en'),
            language_name=ocr_result.get('language_name', 'English')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading multilingual document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


    

@app.post("/chat_multilingual", response_model=MultilingualChatResponse)
async def chat_multilingual(request: MultilingualChatRequest):
    """
    Chat about uploaded multilingual document.
    User can ask in English, get response in their preferred language.
    """
    try:
        if not request.session_id or request.session_id not in user_sessions:
            raise HTTPException(status_code=404, detail="Invalid session_id")
        
        session = user_sessions[request.session_id]
        
        if session['type'] != 'multilingual_document':
            raise HTTPException(status_code=400, detail="This session is not multilingual")
        
        session['last_accessed'] = datetime.utcnow()
        
        # Chat in English (LLM processes in English)
        response = await run_in_threadpool(
            session['chat_engine'].chat,
            request.message
        )

        response_english = str(response)
        
        # Translate response to user's preferred language
        response_translated = response_english
        if request.response_language != 'en':
            response_translated = translator.translate_from_english(
                response_english,
                request.response_language
            )
        
        logger.info(f"Multilingual chat: {request.session_id} → Response in {request.response_language}")
        
        return MultilingualChatResponse(
            response_english=response_english,
            response_translated=response_translated,
            language=request.response_language,
            document=session['filename'],
            session_id=request.session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in multilingual chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/supported_languages")
async def get_supported_languages():
    """Get list of supported Indian languages"""
    return {
        "languages": [
            {"code": code, "name": name}
            for code, name in SUPPORTED_LANGUAGES.items()
        ]
    }



# ==================== UTILITY ENDPOINTS ====================

@app.post("/delete_session", response_model=DeleteSessionResponse)
async def delete_session(request: DeleteSessionRequest):
    """Delete a session and associated files"""
    try:
        if not request.session_id or request.session_id not in user_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = user_sessions[request.session_id]
        
        # Delete uploaded file if it exists
        if session['type'] == 'document' and os.path.exists(session['filepath']):
            os.remove(session['filepath'])
            logger.info(f"Deleted file: {session['filepath']}")
        
        # Remove session
        del user_sessions[request.session_id]
        
        logger.info(f"Session deleted: {request.session_id}")
        
        return DeleteSessionResponse(
            message="Session deleted successfully",
            session_id=request.session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/session_info/{session_id}", response_model=SessionInfoResponse)
async def session_info(session_id: str):
    """Get information about a session"""
    try:
        if not session_id or session_id not in user_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = user_sessions[session_id]
        
        info = SessionInfoResponse(
            session_id=session_id,
            type=session['type']
        )
        
        if session['type'] == 'document':
            info.filename = session['filename']
            info.pages = len(session['documents'])
        
        return info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "active_sessions": len(user_sessions),
        "medicine_index_loaded": medicine_index is not None,
        "upload_folder": UPLOAD_FOLDER
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
