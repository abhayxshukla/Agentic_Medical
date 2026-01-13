from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import uvicorn

# Import your FastAPI apps
from medicin.chat3 import app as medicin_app
# from mental_health.chat import app as mental_health_app  # If you convert this too

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create main FastAPI app
app = FastAPI(
    title="Medical Health Project API",
    description="Comprehensive medical assistant API with symptom analysis and document processing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8080",
        "file://"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount sub-applications
app.mount("/medical-api/medicin", medicin_app)
# app.mount("/medical-api/mental_health", mental_health_app)  # Uncomment when converted

# Root endpoint
@app.get("/")
async def root():
    """Main API health check"""
    return {
        "message": "Medical Health Project API",
        "status": "healthy",
        "version": "1.0.0",
        "modules": ["medicin", "mental_health"],
        "documentation": "/docs"
    }

@app.get("/medical-api")
async def medical_api_root():
    """Medical API health check"""
    return {
        "message": "Medical API Server is running",
        "status": "healthy",
        "available_endpoints": {
            "medicin": "/medical-api/medicin",
            "mental_health": "/medical-api/mental_health"
        }
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "path": str(request.url)
        }
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    return {
        "status": "healthy",
        "api_version": "1.0.0",
        "modules": {
            "medicin": "active",
            "mental_health": "active"
        }
    }

if __name__ == "__main__":
    logger.info("Starting Medical Health Project API...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5005,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )
