"""FastAPI web application for Digital Skeptic AI"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, HttpUrl
from datetime import datetime
import logging

from src.models.schemas import AnalysisRequest
from src.models.response_models import AnalysisResponse, HealthResponse
from src.core.orchestrator import orchestrator
from src.utils.config import config

# Configure logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL, logging.INFO))
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Digital Skeptic AI",
    description="Empowering Critical Thinking in an Age of Information Overload",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple URL input model for the exact requirements
class URLInput(BaseModel):
    url: str

@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Digital Skeptic AI",
        "version": "1.0.0",
        "description": "AI-powered news article analysis and bias detection",
        "mission": "Hackathon Mission 2: The Digital Skeptic AI",
        "endpoints": {
            "analyze": "/analyze",
            "health": "/health"
        },
        "documentation": "/docs"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now().isoformat()
    )

@app.post("/analyze")
async def analyze_article(url_input: URLInput):
    """
    Analyze a news article from URL - Main hackathon endpoint
    
    Input: URL as string (exactly as specified in requirements)
    Output: Critical Analysis Report in Markdown format
    """
    
    try:
        logger.info(f"Starting analysis for URL: {url_input.url}")
        
        # Create analysis request with default settings
        request = AnalysisRequest(
            url=HttpUrl(url_input.url),
            include_counter_narrative=True,
            include_entity_analysis=True,
            include_source_check=True
        )
        
        # Execute analysis
        result = await orchestrator.analyze_article(request)
        
        if result.success:
            logger.info(f"Analysis completed successfully in {result.processing_time:.2f}s")
            
            # Return the exact format expected by hackathon requirements
            return {
                "success": True,
                "markdown_report": result.markdown_report,
                "processing_time": result.processing_time,
                "url": url_input.url
            }
        else:
            logger.error(f"Analysis failed: {result.error}")
            raise HTTPException(status_code=500, detail=result.error)
        
    except Exception as e:
        logger.error(f"Unexpected error in analyze_article: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Analysis failed: {str(e)}"
        )

@app.post("/analyze-full", response_model=AnalysisResponse)
async def analyze_article_full(request: AnalysisRequest):
    """
    Full analysis with all options (for advanced use)
    """
    
    try:
        logger.info(f"Starting full analysis for URL: {request.url}")
        
        result = await orchestrator.analyze_article(request)
        return result
        
    except Exception as e:
        logger.error(f"Error in analyze_article_full: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analyze/{url:path}")
async def analyze_article_get(url: str):
    """
    Simple GET analysis (for easy testing)
    """
    
    try:
        # Validate and fix URL format
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        url_input = URLInput(url=url)
        return await analyze_article(url_input)
        
    except Exception as e:
        logger.error(f"Error in analyze_article_get: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid URL: {str(e)}")

@app.get("/report/{url:path}")
async def get_markdown_report(url: str):
    """
    Get analysis report as plain markdown text
    """
    
    try:
        # Validate and fix URL format
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        url_input = URLInput(url=url)
        result = await analyze_article(url_input)
        
        if result.get("success") and result.get("markdown_report"):
            return PlainTextResponse(
                content=result["markdown_report"],
                media_type="text/markdown"
            )
        else:
            raise HTTPException(
                status_code=500, 
                detail="Failed to generate report"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_markdown_report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test/{url:path}")
async def test_url(url: str):
    """
    Test URL accessibility and provide diagnostics
    """
    
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        logger.info(f"Testing URL: {url}")
        diagnostics = await orchestrator.test_url(url)
        return diagnostics
        
    except Exception as e:
        logger.error(f"Error in test_url: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint not found",
            "message": "Check /docs for available endpoints",
            "available_endpoints": [
                "/analyze",
                "/health",
                "/docs"
            ]
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 handler"""
    logger.error(f"Internal server error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later."
        }
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("🚀 Digital Skeptic AI starting up...")
    logger.info(f"Debug mode: {config.DEBUG}")
    logger.info(f"Log level: {config.LOG_LEVEL}")
    
    # Test Gemini API connection
    try:
        from src.core.analyzer import analyzer
        logger.info("✅ Gemini API connection configured")
    except Exception as e:
        logger.error(f"❌ Gemini API connection failed: {e}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Digital Skeptic AI shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8080,
        reload=config.DEBUG,
        log_level=config.LOG_LEVEL.lower()
    )