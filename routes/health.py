import subprocess
import shutil
from fastapi import APIRouter
from models.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    chrome_available = _check_chrome_available()
    
    return HealthResponse(
        chrome_available=chrome_available
    )


@router.get("/", response_model=dict)
async def root():
    """Root endpoint with basic information"""
    return {
        "service": "Squoosh API",
        "version": "1.0.0",
        "description": "API for image compression using Squoosh",
        "endpoints": {
            "compress_base64": "/compress/base64",
            "compress_upload": "/compress/upload",
            "supported_formats": "/compress/formats",
            "health": "/health",
            "docs": "/docs"
        }
    }


def _check_chrome_available() -> bool:
    """Check if Google Chrome is available"""
    try:
        # Check if Chrome binary exists
        chrome_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable", 
            "/usr/bin/chromium-browser",
            "/opt/google/chrome/chrome"
        ]
        
        for path in chrome_paths:
            if shutil.which(path):
                return True
        
        # Try to execute Chrome to verify
        result = subprocess.run(
            ["google-chrome", "--version"], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        return result.returncode == 0
        
    except Exception:
        return False