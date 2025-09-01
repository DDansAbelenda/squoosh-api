# Squoosh API

REST API for image compression using Squoosh.app

## Features

- 🚀 **FastAPI** with automatic documentation
- 🖼️ **Image compression** using Squoosh.app
- 📦 **Multiple format support**: WebP, MozJPEG, AVIF, OxiPNG
- 🐋 **Docker ready** for deployment in any environment
- 🔄 **No filesystem**: Processes images in memory
- 📊 **Detailed compression statistics**

## Project Structure

```
squoosh-api/
├── main.py                 # Main FastAPI application
├── run_local.py           # Script to run locally
├── pyproject.toml         # Poetry dependencies
├── Dockerfile             # Docker configuration
├── .env.example           # Environment variables example
├── models/
│   └── schemas.py         # Pydantic models
├── routes/
│   ├── compression.py     # Compression endpoints
│   └── health.py         # Health checks
└── services/
    └── squoosh_service.py # Compression logic
```

## Local Installation

### Prerequisites
- Python 3.12+
- Google Chrome installed
- Poetry (optional)

### Using Poetry
```bash
# Clone and install dependencies
git clone <your-repo>
cd squoosh-api
poetry install

# Run
poetry run python run_local.py
```

### Using pip
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install fastapi uvicorn selenium webdriver-manager pillow python-multipart

# Run
python run_local.py
```

## Docker Installation

```bash
# Build image
docker build -t squoosh-api .

# Run container
docker run -p 8000:8000 squoosh-api
```

## API Usage

### Interactive Documentation
Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Main Endpoints

#### 1. Compress from Base64
```bash
POST /compress/base64
```

**Request Body:**
```json
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

#### 2. Compress from Upload
```bash
POST /compress/upload
```

**Form Data:**
- `file`: Image file
- `format`: Output format (webp, mozjpeg, avif, oxipng)
- `quality`: Quality 1-100

#### 3. Supported Formats
```bash
GET /compress/formats
```

#### 4. Health Check
```bash
GET /health
```

### Example with curl

```bash
# Compress image from base64
curl -X POST "http://localhost:8000/compress/base64" \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "'$(base64 -i my_image.jpg)'",
    "format": "webp",
    "quality": 80,
    "filename": "my_image.jpg"
  }'

# Direct upload
curl -X POST "http://localhost:8000/compress/upload" \
  -F "file=@my_image.jpg" \
  -F "format=webp" \
  -F "quality=80"
```

### Example with Python

```python
import requests
import base64

# Read image
with open("my_image.jpg", "rb") as f:
    image_bytes = f.read()
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')

# Compress
response = requests.post(
    "http://localhost:8000/compress/base64",
    json={
        "image_base64": image_base64,
        "format": "webp",
        "quality": 80,
        "filename": "my_image.jpg"
    }
)

if response.status_code == 200:
    result = response.json()
    
    # Save compressed image
    compressed_bytes = base64.b64decode(result["compressed_image_base64"])
    with open("compressed_image.webp", "wb") as f:
        f.write(compressed_bytes)
    
    print(f"✅ Compression successful!")
    print(f"📉 Reduction: {result['stats']['reduction_percent']}%")
else:
    print(f"❌ Error: {response.text}")
```

## Supported Formats

| Format  | Description | Recommended Use |
|----------|-------------|-----------------|
| `webp` | WebP | Excellent balance quality/size |
| `mozjpeg` | MozJPEG | Best for photographs |
| `avif` | AVIF | Maximum compression (slower) |
| `oxipng` | OxiPNG | Optimized PNG without loss |

## Environment Variables

- `HOST`: Application host (default: 127.0.0.1)
- `PORT`: Application port (default: 8000)
- `DEBUG`: Debug mode (default: true)
- `CHROME_BIN`: Chrome binary path (for Docker)

## Troubleshooting

### Chrome not found
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install google-chrome-stable

# Verify installation
google-chrome --version
```

### Docker permission errors
Make sure the user has permissions to run Chrome:
```dockerfile
USER myuser
```

### Production timeouts
Increase timeouts in `squoosh_service.py` if needed:
```python
self.wait = WebDriverWait(self.driver, 60)  # Increase from 30 to 60
```

## Development

### Run tests
```bash
poetry run pytest
```

### Linting
```bash
poetry run black .
poetry run isort .
```

## Deployment

### Docker Compose
```yaml
version: '3.8'
services:
  squoosh-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PORT=8000
      - DEBUG=false
```

### Production environment variables
```bash
export PORT=8000
export DEBUG=false
export CHROME_BIN=/usr/bin/google-chrome
```

## Limitations

- Requires Google Chrome installed
- Depends on squoosh.app (external service)
- Sequential processing (one image at a time)
- Configurable timeouts per environment

## Contributing

1. Fork the project
2. Create feature branch (`git checkout -b feature/new-functionality`)
3. Commit changes (`git commit -am 'Add new functionality'`)
4. Push to branch (`git push origin feature/new-functionality`)
5. Create Pull Request
