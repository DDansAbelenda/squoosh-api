"""
Script to run the API locally
"""
import os
import logging
import uvicorn
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables if .env file exists
load_dotenv()

if __name__ == "__main__":
    # Configuration for local development
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "true").lower() == "true"

    logger.info(f"🚀 Starting Squoosh API on http://{host}:{port}")
    logger.info(f"📖 Documentation available at http://{host}:{port}/docs")
    logger.info(f"🔧 Debug mode: {debug}")

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )
