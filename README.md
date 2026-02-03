Agentic_Medical - Medical Intake System
An intelligent medical intake system that combines OCR, geolocation, and doctor recommendations using LlamaIndex workflows and FastAPI.

Overview
This project automates medical intake processes by extracting information from prescriptions and medical reports using OCR, understanding patient symptoms and medical context, and recommending nearby doctors based on semantic similarity rather than external APIs.
​

Key Features
1. Multilingual OCR Processing
Primary OCR: Google Vision API for multi-language support (English, Hindi, Bengali, Tamil, Telugu, etc.)
​

Fallback OCR: AWS Textract and Tesseract for reliability
​

Processes prescriptions, medical reports, and handwritten documents

Image quality validation before processing

2. Geolocation & Doctor Recommendations
Vector-based doctor search using Practo-scraped data (599 doctors)
​

Semantic matching by specialty, locality, experience, and fees
​

Hybrid scoring system: Combines similarity (40%), specialty match (30%), recommendation % (20%), and fees (10%)
​

PIN code-based locality matching without external API costs
​

3. Conversational Medical Assistant
Session-based chat with conversation memory
​

Context-aware responses using LlamaIndex ContextChatEngine

Automatic specialty extraction from symptoms
​

Combined prescription + medicine database context
​

Technology Stack
Backend (Python 46.9%)
FastAPI: REST API framework

LlamaIndex: Document indexing and conversational workflows

OpenAI GPT-4: LLM for medical understanding
​

HuggingFace Embeddings: BAAI/bge-large-en-v1.5 (1024-dim) for medicine recommendation
​

PostgreSQL + pgvector: Vector storage for doctor embeddings
​

OCR & Computer Vision
Google Cloud Vision API
​

AWS Textract
​

Tesseract OCR
​

OpenCV for image preprocessing
​

Frontend (JavaScript 30.6% + CSS 21.5%)
Web interface for document upload and chat

Session management UI

Doctor recommendation display
