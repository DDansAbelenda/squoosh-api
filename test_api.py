"""
Sample script to test the API
"""
import requests
import base64
import logging
from PIL import Image
from io import BytesIO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = "http://localhost:8000"


def create_test_image():
    """Create test image"""
    # Create simple test image
    img = Image.new('RGB', (200, 200), color='red')

    # Convert to bytes
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    image_bytes = buffer.getvalue()

    return image_bytes


def test_health():
    """Health check test"""
    logger.info("🏥 Testing health check...")
    response = requests.get(f"{API_BASE_URL}/health")

    if response.status_code == 200:
        data = response.json()
        logger.info(f"✅ Health OK - Chrome available: {data['chrome_available']}")
        return True
    else:
        logger.error(f"❌ Health failed: {response.status_code}")
        return False


def test_compress_base64():
    """Test compression from base64"""
    logger.info("\n📦 Testing compression from base64...")

    # Create test image
    image_bytes = create_test_image()
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')

    # Request
    payload = {
        "image_base64": image_base64,
        "format": "webp",
        "quality": 80,
        "filename": "test_image.jpg"
    }

    response = requests.post(
        f"{API_BASE_URL}/compress/base64",
        json=payload
    )

    if response.status_code == 200:
        data = response.json()
        logger.info("✅ Compression successful!")
        logger.info(f"📊 Original size: {data['stats']['original_size']:,} bytes")
        logger.info(f"📊 Compressed size: {data['stats']['compressed_size']:,} bytes")
        logger.info(f"📊 Reduction: {data['stats']['reduction_percent']}%")

        # Save compressed image (optional)
        compressed_bytes = base64.b64decode(data["compressed_image_base64"])
        with open("test_compressed.webp", "wb") as f:
            f.write(compressed_bytes)
        logger.info("💾 Image saved as test_compressed.webp")

        return True
    else:
        logger.error(f"❌ Error: {response.status_code}")
        logger.error(f"Response: {response.text}")
        return False


def test_upload():
    """Test compression by upload"""
    logger.info("\n📤 Testing compression by upload...")

    # Create temporary file
    image_bytes = create_test_image()

    with open("temp_test.jpg", "wb") as f:
        f.write(image_bytes)

    # Upload
    with open("temp_test.jpg", "rb") as f:
        files = {"file": ("test.jpg", f, "image/jpeg")}
        data = {
            "format": "webp",
            "quality": 80
        }

        response = requests.post(
            f"{API_BASE_URL}/compress/upload",
            files=files,
            data=data
        )

    if response.status_code == 200:
        data = response.json()
        logger.info("✅ Upload compressed successfully!")
        logger.info(f"📊 Reduction: {data['stats']['reduction_percent']}%")
        return True
    else:
        logger.error(f"❌ Error: {response.status_code}")
        logger.error(f"Response: {response.text}")
        return False


def test_formats():
    """Test supported formats endpoint"""
    logger.info("\n📋 Testing supported formats...")

    response = requests.get(f"{API_BASE_URL}/compress/formats")

    if response.status_code == 200:
        data = response.json()
        logger.info("✅ Formats obtained:")
        for format_name, description in data["formats"].items():
            logger.info(f"  • {format_name}: {description}")
        return True
    else:
        logger.error(f"❌ Error: {response.status_code}")
        return False


def main():
    """Run all tests"""
    logger.info("🚀 Starting Squoosh API tests...")
    logger.info("=" * 50)

    tests = [
        ("Health Check", test_health),
        ("Formats", test_formats),
        ("Base64 Compression", test_compress_base64),
        ("Upload", test_upload)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ Error in {test_name}: {e}")
            results.append((test_name, False))

    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")

    logger.info(f"\nResult: {passed}/{total} successful tests")

    if passed == total:
        logger.info("🎉 All tests passed!")
    else:
        logger.warning("⚠️ Some tests failed")


if __name__ == "__main__":
    main()
