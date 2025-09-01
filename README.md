# Squoosh API

REST API for image compression using native Python libraries (PIL/Pillow) instead of browser automation.

## Features

- 🚀 **FastAPI** with automatic documentation (OpenAPI/Swagger)
- 🖼️ **Image compression** using native Python libraries (PIL/Pillow)
- 📦 **Multiple format support**: WebP, JPEG/MozJPEG, PNG/OxiPNG, AVIF
- 🐋 **Docker ready** for deployment in any environment
- 🔄 **Memory-based processing** - no filesystem dependencies
- 📊 **Detailed compression statistics** with reduction percentages
- 🛡️ **Professional logging** system with structured output
- ✅ **Input validation** with Pydantic models
- 🌍 **CORS enabled** for web applications

## Project Structure

```
squoosh-api/
├── main.py                 # FastAPI application with lifecycle management
├── run_local.py           # Local development server script
├── pyproject.toml         # Poetry dependencies and project config
├── Dockerfile             # Container configuration (Railway optimized)
├── railway.json           # Railway deployment configuration
├── requirements.txt       # pip requirements (fallback)
├── models/
│   └── schemas.py         # Pydantic models with validation
├── routes/
│   ├── compression.py     # Image compression endpoints
│   └── health.py         # Health check and service info
└── services/
    └── squoosh_service.py # Core compression logic
```

## Requirements

- **Python**: 3.12+ (tested up to 3.13)
- **Dependencies**: FastAPI, Uvicorn, Pillow, Pydantic
- **No Chrome required** - uses native Python image processing
- **Memory**: Minimum 512MB RAM recommended

## Installation & Setup

### Option 1: Using Poetry (Recommended)
```bash
# Clone repository
git clone <repository-url>
cd squoosh-api

# Install with Poetry
poetry install

# Run development server
poetry run python run_local.py
```

### Option 2: Using pip + venv
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server
python run_local.py
```

### Option 3: Docker
```bash
# Build image
docker build -t squoosh-api .

# Run container
docker run -p 8000:8000 squoosh-api

# With environment variables
docker run -p 8000:8000 -e DEBUG=false squoosh-api
```

## API Documentation

### Interactive Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

### Available Endpoints

#### 1. Image Compression from Base64
```http
POST /compress/base64
Content-Type: application/json

{
  "image_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
  "format": "webp",
  "quality": 80,
  "filename": "my_image.jpg"
}
```

**Response:**
```json
{
  "success": true,
  "compressed_image_base64": "UklGRqQAAABXRUJQVlA4...",
  "format": "webp",
  "quality": 80,
  "stats": {
    "original_size": 245760,
    "compressed_size": 89432,
    "reduction_percent": 63.6,
    "compression_ratio": 2.75
  },
  "filename": "my_image.jpg"
}
```

#### 2. Image Compression from File Upload
```http
POST /compress/upload
Content-Type: multipart/form-data

file: [binary image data]
format: webp
quality: 80
```

#### 3. Supported Formats
```http
GET /compress/formats
```

Returns available compression formats with descriptions.

#### 4. Health Check
```http
GET /health
```

Returns service status and system information.

#### 5. Root Information
```http
GET /
```

Returns API information and available endpoints.

## Supported Formats

| Format | Extension | Description | Use Case |
|--------|-----------|-------------|----------|
| `webp` | .webp | WebP format | Best balance of quality/size |
| `mozjpeg` | .jpg/.jpeg | Optimized JPEG | Photographs and complex images |
| `jpeg`/`jpg` | .jpg/.jpeg | Standard JPEG | Alias for mozjpeg |
| `png` | .png | PNG optimization | Images with transparency |
| `oxipng` | .png | Optimized PNG | Alias for png with optimization |
| `avif` | .avif | AVIF format | Next-gen format (fallback to WebP) |

## Usage Examples

### Python Client
```python
import requests
import base64

# Read and encode image
with open("image.jpg", "rb") as f:
    image_data = f.read()
    image_base64 = base64.b64encode(image_data).decode()

# Compress image
response = requests.post("http://localhost:8000/compress/base64", json={
    "image_base64": image_base64,
    "format": "webp",
    "quality": 80,
    "filename": "my_image.jpg"
})

if response.status_code == 200:
    result = response.json()
    
    # Save compressed image
    compressed_data = base64.b64decode(result["compressed_image_base64"])
    with open("compressed_image.webp", "wb") as f:
        f.write(compressed_data)
    
    print(f"✅ Compressed successfully!")
    print(f"📊 Original: {result['stats']['original_size']:,} bytes")
    print(f"📊 Compressed: {result['stats']['compressed_size']:,} bytes")
    print(f"📊 Reduction: {result['stats']['reduction_percent']}%")
```

### JavaScript/Fetch
```javascript
const compressImage = async (base64Image) => {
  const response = await fetch('http://localhost:8000/compress/base64', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      image_base64: base64Image,
      format: 'webp',
      quality: 80,
      filename: 'image.jpg'
    })
  });
  
  const result = await response.json();
  return result;
};
```

### cURL
```bash
# Compress from base64
curl -X POST "http://localhost:8000/compress/base64" \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "'$(base64 -w 0 image.jpg)'",
    "format": "webp",
    "quality": 80,
    "filename": "image.jpg"
  }'

# Upload file directly
curl -X POST "http://localhost:8000/compress/upload" \
  -F "file=@image.jpg" \
  -F "format=webp" \
  -F "quality=80"
```

## Environment Variables

The application uses minimal environment variables for configuration:

| Variable | Default | Description | Used In |
|----------|---------|-------------|---------|
| `HOST` | `127.0.0.1` | Server host address | `run_local.py` |
| `PORT` | `8000` | Server port | `run_local.py`, Railway |
| `DEBUG` | `true` | Debug mode (enables reload & error details) | `run_local.py`, `main.py` |

### Local Development (.env file - optional)
You can create a `.env` file in the project root:
```bash
HOST=127.0.0.1
PORT=8000
DEBUG=true
```

**Note:** The project works perfectly without any `.env` file as all variables have sensible defaults.

## Deployment

### Railway (Recommended)
The project is pre-configured for Railway deployment:

1. Connect your repository to Railway
2. Deploy automatically using `railway.json` configuration
3. Environment variables are handled automatically

### Docker Production
```dockerfile
# Multi-stage build for optimization
docker build -t squoosh-api .
docker run -d -p 8000:8000 --name squoosh-api squoosh-api
```

### Manual Production
```bash
# Install production dependencies
pip install -r requirements.txt

# Run with Gunicorn (install separately)
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
```

## Testing

### Manual API Testing

You can test the API endpoints manually using the interactive documentation or command line tools:

#### Using Swagger UI (Recommended)
1. Start the server: `python run_local.py`
2. Open browser: `http://localhost:8000/docs`
3. Test all endpoints interactively

#### Using cURL commands
```bash
# Test health check
curl http://localhost:8000/health

# Test supported formats
curl http://localhost:8000/compress/formats

# Test base64 compression (replace with actual base64 data)
curl -X POST "http://localhost:8000/compress/base64" \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
    "format": "webp",
    "quality": 80,
    "filename": "test.png"
  }'
```

### Automated Testing
Currently, the project does not include automated test files. To add testing:

1. Install testing dependencies:
```bash
pip install pytest httpx
```

2. Create test files in a `tests/` directory
3. Write tests using pytest and FastAPI's TestClient

## Logging

The application uses structured logging:

```python
# Logs are formatted as:
# 2024-01-15 10:30:45,123 - squoosh_service - INFO - Compressing image: test.jpg to format: webp
```

Logging levels:
- `INFO`: General operations
- `DEBUG`: Detailed processing information
- `WARNING`: Non-critical issues
- `ERROR`: Error conditions

## Error Handling

The API provides detailed error responses:

```json
{
  "success": false,
  "error": "Error decoding base64",
  "details": "Invalid base64 string format"
}
```

Common errors:
- `400`: Invalid input (bad base64, unsupported format)
- `413`: File too large
- `500`: Internal processing error

## Performance Notes

- **Memory usage**: ~50MB base + image size × 3 (original + working + compressed)
- **Processing time**: 100-500ms per image (depends on size and format)
- **Concurrent requests**: Supported (FastAPI async)
- **File size limits**: Handled by FastAPI settings (default 16MB)

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Make changes with proper logging and error handling
4. Add tests for new functionality
5. Update documentation
6. Commit: `git commit -am 'Add new feature'`
7. Push: `git push origin feature/new-feature`
8. Create Pull Request

## License

This project is available under the MIT License.

## Support

For issues and questions:
- Create an issue in the repository
- Check the logs for detailed error information
- Verify all dependencies are correctly installed
