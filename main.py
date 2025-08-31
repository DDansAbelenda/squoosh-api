import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routes.compression import router as compression_router
from routes.health import router as health_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    logger.info("🚀 Starting Squoosh API...")

    # Startup
    try:
        # Verify critical dependencies on startup
        from services.squoosh_service import SquooshService
        logger.info("✅ Services loaded correctly")

        # Log Chrome and ChromeDriver versions
        import subprocess
        try:
            chrome_version = subprocess.check_output(["/usr/bin/google-chrome-stable", "--version"],
                                                     text=True).strip()
            logger.info(f"🌐 Chrome version: {chrome_version}")

            chromedriver_version = subprocess.check_output(["/usr/local/bin/chromedriver", "--version"],
                                                           text=True).strip()
            logger.info(f"🚗 ChromeDriver version: {chromedriver_version}")
        except Exception as e:
            logger.warning(f"⚠️ Could not verify Chrome/ChromeDriver versions: {e}")

    except Exception as e:
        logger.error(f"❌ Error loading services: {e}")
        raise e

    yield

    # Shutdown
    logger.info("🛑 Closing Squoosh API...")


def create_app() -> FastAPI:
    """Factory to create FastAPI application"""

    app = FastAPI(
        title="Squoosh API",
        description="API for image compression using Squoosh",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify specific domains
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error(f"Unhandled error: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Internal server error",
                "details": str(exc) if os.getenv("DEBUG") else None
            }
        )

    # Include routers
    app.include_router(health_router)
    app.include_router(compression_router)

    return app


# Create application instance
app = create_app()

if __name__ == "__main__":
    import uvicorn

    # Usar puerto dinámico de Railway o 8000 por defecto
    port = int(os.environ.get("PORT", 8000))

    logger.info(f"🌐 Starting server on 0.0.0.0:{port}")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )