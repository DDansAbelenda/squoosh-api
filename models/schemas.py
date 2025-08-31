from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional
from enum import Enum
import base64


class CompressionFormat(str, Enum):
    """Formatos de compresión soportados"""
    WEBP = "webp"
    MOZJPEG = "mozjpeg"
    AVIF = "avif"
    OXIPNG = "oxipng"
    JPEG = "jpeg"
    JPG = "jpg"
    PNG = "png"


class CompressionRequest(BaseModel):
    """Request para comprimir imagen"""
    image_base64: str = Field(..., description="Imagen en formato base64")
    format: CompressionFormat = Field(default=CompressionFormat.WEBP, description="Formato de salida")
    quality: int = Field(default=80, ge=1, le=100, description="Calidad de compresión (1-100)")
    filename: Optional[str] = Field(default="image.jpg", description="Nombre del archivo original")

    @field_validator('image_base64')
    def validate_base64(cls, v):
        try:
            # Remover prefijo data URL si existe
            if v.startswith('data:'):
                v = v.split(',', 1)[1]

            # Validar que es base64 válido
            base64.b64decode(v)
            return v
        except Exception:
            raise ValueError('image_base64 debe ser una cadena base64 válida')

    @field_validator('filename')
    def validate_filename(cls, v):
        if v and not any(v.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff']):
            return v + '.jpg'  # Agregar extensión por defecto
        return v


class CompressionStats(BaseModel):
    """Estadísticas de compresión"""
    original_size: int = Field(..., description="Tamaño original en bytes")
    compressed_size: int = Field(..., description="Tamaño comprimido en bytes")
    reduction_percent: float = Field(..., description="Porcentaje de reducción")
    compression_ratio: float = Field(..., description="Ratio de compresión")


class CompressionResponse(BaseModel):
    """Response de compresión exitosa"""
    success: bool = Field(default=True)
    compressed_image_base64: str = Field(..., description="Imagen comprimida en base64")
    format: str = Field(..., description="Formato de salida utilizado")
    quality: int = Field(..., description="Calidad utilizada")
    stats: CompressionStats = Field(..., description="Estadísticas de compresión")
    filename: str = Field(..., description="Nombre del archivo procesado")


class ErrorResponse(BaseModel):
    """Response de error"""
    success: bool = Field(default=False)
    error: str = Field(..., description="Mensaje de error")
    details: Optional[str] = Field(None, description="Detalles adicionales del error")


class HealthResponse(BaseModel):
    """Response del health check"""
    status: str = Field(default="healthy")
    service: str = Field(default="squoosh-api")
    version: str = Field(default="1.0.0")
    chrome_available: bool = Field(..., description="Chrome disponible")


class SupportedFormatsResponse(BaseModel):
    """Response con formatos soportados"""
    formats: dict = Field(..., description="Diccionario de formatos soportados y sus descripciones")
