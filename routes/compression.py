import base64
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from models.schemas import (
    CompressionRequest,
    CompressionResponse,
    CompressionFormat,
    SupportedFormatsResponse
)
from services.squoosh_service import SquooshService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/compress", tags=["compression"])


@router.post("/base64", response_model=CompressionResponse)
async def compress_image_base64(request: CompressionRequest):
    """
    Compress image from base64

    - **image_base64**: Image in base64 format
    - **format**: Output format (webp, mozjpeg, avif, oxipng, jpeg, jpg, png)
    - **quality**: Compression quality (1-100)
    - **filename**: Original filename (optional)
    """
    squoosh = None
    try:
        logger.info(f"Starting compression - Format: {request.format}, Quality: {request.quality}")

        # Decode base64
        try:
            image_bytes = base64.b64decode(request.image_base64)
            logger.info(f"Base64 decoded successfully, size: {len(image_bytes)} bytes")
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Error decoding base64: {str(e)}"
            )

        # Create SquooshService instance
        squoosh = SquooshService()

        # Create driver
        squoosh.create_driver()

        # Compress image
        compressed_bytes = squoosh.compress_image_from_bytes(
            image_bytes=image_bytes,
            format_type=request.format.value,
            quality=request.quality,
            original_filename=request.filename or "image.jpg"
        )

        if not compressed_bytes:
            raise HTTPException(
                status_code=500,
                detail="Error during image compression"
            )

        # Calculate statistics
        stats = squoosh.get_compression_stats(image_bytes, compressed_bytes)

        # Encode result to base64
        compressed_base64 = base64.b64encode(compressed_bytes).decode('utf-8')

        logger.info(f"Compression successful - Reduction: {stats['reduction_percent']}%")

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
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
    finally:
        # Always clean up
        if squoosh:
            try:
                squoosh.close()
            except Exception as e:
                logger.warning(f"Error cleaning up SquooshService: {e}")


@router.post("/upload", response_model=CompressionResponse)
async def compress_image_upload(
        file: UploadFile = File(...),
        format: CompressionFormat = Form(default=CompressionFormat.WEBP),
        quality: int = Form(default=80, ge=1, le=100)
):
    """
    Compress image from uploaded file

    - **file**: Image file
    - **format**: Output format
    - **quality**: Compression quality (1-100)
    """
    squoosh = None
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="File must be an image"
            )

        logger.info(f"Processing upload - File: {file.filename}, Format: {format}, Quality: {quality}")

        # Read file bytes
        image_bytes = await file.read()

        if len(image_bytes) == 0:
            raise HTTPException(
                status_code=400,
                detail="File is empty"
            )

        # Create SquooshService instance
        squoosh = SquooshService()

        # Create driver
        squoosh.create_driver()

        # Compress image
        compressed_bytes = squoosh.compress_image_from_bytes(
            image_bytes=image_bytes,
            format_type=format.value,
            quality=quality,
            original_filename=file.filename or "image.jpg"
        )

        if not compressed_bytes:
            raise HTTPException(
                status_code=500,
                detail="Error during image compression"
            )

        # Calculate statistics
        stats = squoosh.get_compression_stats(image_bytes, compressed_bytes)

        # Encode result to base64
        compressed_base64 = base64.b64encode(compressed_bytes).decode('utf-8')

        logger.info(f"Upload compressed successfully - Reduction: {stats['reduction_percent']}%")

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
        logger.error(f"Error processing upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
    finally:
        # Always clean up
        if squoosh:
            try:
                squoosh.close()
            except Exception as e:
                logger.warning(f"Error cleaning up SquooshService: {e}")


@router.get("/formats", response_model=SupportedFormatsResponse)
async def get_supported_formats():
    """Get supported compression formats"""
    formats = {
        "webp": "WebP - Excellent universal compression",
        "mozjpeg": "MozJPEG - Best for photographs",
        "avif": "AVIF - Maximum compression (slower)",
        "oxipng": "OxiPNG - PNG optimization without loss",
        "jpeg": "JPEG - Alias for mozJPEG",
        "jpg": "JPG - Alias for mozJPEG",
        "png": "PNG - Alias for oxiPNG"
    }

    return SupportedFormatsResponse(formats=formats)