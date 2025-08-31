import base64
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Optional

from models.schemas import (
    CompressionRequest, 
    CompressionResponse, 
    ErrorResponse,
    CompressionFormat,
    SupportedFormatsResponse
)
from services.squoosh_service import SquooshService

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/compress", tags=["compression"])


@router.post("/base64", response_model=CompressionResponse)
async def compress_image_base64(request: CompressionRequest):
    """
    Comprimir imagen desde base64
    
    - **image_base64**: Imagen en formato base64
    - **format**: Formato de salida (webp, mozjpeg, avif, oxipng, jpeg, jpg, png)
    - **quality**: Calidad de compresión (1-100)
    - **filename**: Nombre del archivo original (opcional)
    """
    try:
        logger.info(f"Iniciando compresión - Formato: {request.format}, Calidad: {request.quality}")
        
        # Decodificar base64
        try:
            image_bytes = base64.b64decode(request.image_base64)
        except Exception as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Error decodificando base64: {str(e)}"
            )
        
        # Comprimir imagen
        with SquooshService(headless=True) as squoosh:
            compressed_bytes = squoosh.compress_image_from_bytes(
                image_bytes=image_bytes,
                format_type=request.format.value,
                quality=request.quality,
                original_filename=request.filename or "image.jpg"
            )
            
            if not compressed_bytes:
                raise HTTPException(
                    status_code=500,
                    detail="Error durante la compresión de la imagen"
                )
            
            # Calcular estadísticas
            stats = squoosh.get_compression_stats(image_bytes, compressed_bytes)
            
            # Codificar resultado a base64
            compressed_base64 = base64.b64encode(compressed_bytes).decode('utf-8')
            
            logger.info(f"Compresión exitosa - Reducción: {stats['reduction_percent']}%")
            
            return CompressionResponse(
                compressed_image_base64=compressed_base64,
                format=request.format.value,
                quality=request.quality,
                stats=stats,
                filename=request.filename or "image.jpg"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.post("/upload", response_model=CompressionResponse)
async def compress_image_upload(
    file: UploadFile = File(...),
    format: CompressionFormat = Form(default=CompressionFormat.WEBP),
    quality: int = Form(default=80, ge=1, le=100)
):
    """
    Comprimir imagen desde archivo subido
    
    - **file**: Archivo de imagen
    - **format**: Formato de salida
    - **quality**: Calidad de compresión (1-100)
    """
    try:
        # Validar tipo de archivo
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="El archivo debe ser una imagen"
            )
        
        logger.info(f"Procesando upload - Archivo: {file.filename}, Formato: {format}, Calidad: {quality}")
        
        # Leer bytes del archivo
        image_bytes = await file.read()
        
        if len(image_bytes) == 0:
            raise HTTPException(
                status_code=400,
                detail="El archivo está vacío"
            )
        
        # Comprimir imagen
        with SquooshService(headless=True) as squoosh:
            compressed_bytes = squoosh.compress_image_from_bytes(
                image_bytes=image_bytes,
                format_type=format.value,
                quality=quality,
                original_filename=file.filename or "image.jpg"
            )
            
            if not compressed_bytes:
                raise HTTPException(
                    status_code=500,
                    detail="Error durante la compresión de la imagen"
                )
            
            # Calcular estadísticas
            stats = squoosh.get_compression_stats(image_bytes, compressed_bytes)
            
            # Codificar resultado a base64
            compressed_base64 = base64.b64encode(compressed_bytes).decode('utf-8')
            
            logger.info(f"Upload comprimido exitosamente - Reducción: {stats['reduction_percent']}%")
            
            return CompressionResponse(
                compressed_image_base64=compressed_base64,
                format=format.value,
                quality=quality,
                stats=stats,
                filename=file.filename or "image.jpg"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error procesando upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get("/formats", response_model=SupportedFormatsResponse)
async def get_supported_formats():
    """Obtener formatos de compresión soportados"""
    formats = {
        "webp": "WebP - Excelente compresión universal",
        "mozjpeg": "MozJPEG - Mejor para fotografías",
        "avif": "AVIF - Máxima compresión (más lento)",
        "oxipng": "OxiPNG - Optimización PNG sin pérdida",
        "jpeg": "JPEG - Alias para mozJPEG",
        "jpg": "JPG - Alias para mozJPEG", 
        "png": "PNG - Alias para oxiPNG"
    }
    
    return SupportedFormatsResponse(formats=formats)