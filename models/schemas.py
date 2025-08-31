from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional
from enum import Enum
import base64


class CompressionFormat(str, Enum):
    """Supported compression formats"""
    WEBP = "webp"
    MOZJPEG = "mozjpeg"
    AVIF = "avif"
    OXIPNG = "oxipng"
    JPEG = "jpeg"
    JPG = "jpg"
    PNG = "png"


class CompressionRequest(BaseModel):
    """Request to compress image"""
    image_base64: str = Field(..., description="Image in base64 format")
    format: CompressionFormat = Field(default=CompressionFormat.WEBP, description="Output format")
    quality: int = Field(default=80, ge=1, le=100, description="Compression quality (1-100)")
    filename: Optional[str] = Field(default="image.jpg", description="Original filename")

    @field_validator('image_base64')
    def validate_base64(cls, v):
        try:
            # Remove data URL prefix if exists
            if v.startswith('data:'):
                v = v.split(',', 1)[1]

            # Validate that it's valid base64
            base64.b64decode(v)
            return v
        except Exception:
            raise ValueError('image_base64 must be a valid base64 string')

    @field_validator('filename')
    def validate_filename(cls, v):
        if v and not any(v.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff']):
            return v + '.jpg'  # Add default extension
        return v


class CompressionStats(BaseModel):
    """Compression statistics"""
    original_size: int = Field(..., description="Original size in bytes")
    compressed_size: int = Field(..., description="Compressed size in bytes")
    reduction_percent: float = Field(..., description="Reduction percentage")
    compression_ratio: float = Field(..., description="Compression ratio")


class CompressionResponse(BaseModel):
    """Successful compression response"""
    success: bool = Field(default=True)
    compressed_image_base64: str = Field(..., description="Compressed image in base64")
    format: str = Field(..., description="Output format used")
    quality: int = Field(..., description="Quality used")
    stats: CompressionStats = Field(..., description="Compression statistics")
    filename: str = Field(..., description="Processed filename")


class ErrorResponse(BaseModel):
    """Error response"""
    success: bool = Field(default=False)
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(default="healthy")
    service: str = Field(default="squoosh-api")
    version: str = Field(default="1.0.0")
    chrome_available: bool = Field(..., description="Chrome available")


class SupportedFormatsResponse(BaseModel):
    """Response with supported formats"""
    formats: dict = Field(..., description="Dictionary of supported formats and their descriptions")
