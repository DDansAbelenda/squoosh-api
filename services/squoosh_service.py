import os
import tempfile
from typing import Optional
from io import BytesIO
from PIL import Image


class SquooshService:
    """Service for compressing images using native compression libraries"""

    def __init__(self, headless: bool = True):
        self.temp_dir = tempfile.mkdtemp()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def compress_image_from_bytes(
            self,
            image_bytes: bytes,
            format_type: str = "webp",
            quality: int = 80,
            original_filename: str = "image"
    ) -> Optional[bytes]:
        """
        Compress image from bytes using native libraries

        Args:
            image_bytes: Original image bytes
            format_type: Output format ('webp', 'mozjpeg', 'avif', 'oxipng', 'jpeg', 'jpg', 'png')
            quality: Compression quality (0-100)
            original_filename: Original filename (for extension)

        Returns:
            bytes: Compressed image or None if error
        """
        try:
            # Validate and open image
            img = Image.open(BytesIO(image_bytes))

            # Convert RGBA to RGB for JPEG formats
            if format_type.lower() in ['jpeg', 'jpg', 'mozjpeg'] and img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img

            # Compress based on format
            output_buffer = BytesIO()

            if format_type.lower() == 'webp':
                img.save(output_buffer, format='WebP', quality=quality, method=6)
            elif format_type.lower() in ['jpeg', 'jpg', 'mozjpeg']:
                img.save(output_buffer, format='JPEG', quality=quality, optimize=True)
            elif format_type.lower() in ['png', 'oxipng']:
                img.save(output_buffer, format='PNG', optimize=True)
            elif format_type.lower() == 'avif':
                # Fallback to WebP if AVIF not supported
                img.save(output_buffer, format='WebP', quality=quality, method=6)
            else:
                # Default to WebP
                img.save(output_buffer, format='WebP', quality=quality, method=6)

            return output_buffer.getvalue()

        except Exception as e:
            raise Exception(f"Error compressing image: {e}")

    def close(self):
        """Close resources"""
        # Clean up temporary directory
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
            except:
                pass

    def get_compression_stats(self, original_bytes: bytes, compressed_bytes: bytes) -> dict:
        """Calculate compression statistics"""
        original_size = len(original_bytes)
        compressed_size = len(compressed_bytes)
        reduction_percent = ((original_size - compressed_size) / original_size) * 100

        return {
            "original_size": original_size,
            "compressed_size": compressed_size,
            "reduction_percent": round(reduction_percent, 2),
            "compression_ratio": round(original_size / compressed_size, 2)
        }