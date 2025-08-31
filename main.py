import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routes.compression import router as compression_router
from routes.health import router as health_router

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    logger.info("🚀 Iniciando Squoosh API...")
    
    # Startup
    try:
        # Verificar dependencias críticas al inicio
        from services.squoosh_service import SquooshService
        logger.info("✅ Servicios cargados correctamente")
    except Exception as e:
        logger.error(f"❌ Error cargando servicios: {e}")
        raise e
    
    yield
    
    # Shutdown
    logger.info("🛑 Cerrando Squoosh API...")


def create_app() -> FastAPI:
    """Factory para crear la aplicación FastAPI"""
    
    app = FastAPI(
        title="Squoosh API",
        description="API para compresión de imágenes usando Squoosh",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Configurar CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # En producción, especificar dominios específicos
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Manejador de excepciones global
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error(f"Error no manejado: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Error interno del servidor",
                "details": str(exc) if os.getenv("DEBUG") else None
            }
        )
    
    # Incluir routers
    app.include_router(health_router)
    app.include_router(compression_router)
    
    return app


# Crear instancia de la aplicación
app = create_app()