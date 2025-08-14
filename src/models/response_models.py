from typing import Optional
from pydantic import BaseModel
from .schemas import AnalysisResult

class AnalysisResponse(BaseModel):
    """API response for analysis"""
    success: bool
    result: Optional[AnalysisResult] = None
    markdown_report: Optional[str] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: str

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    code: Optional[int] = None 
