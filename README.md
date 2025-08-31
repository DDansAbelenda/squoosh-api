# Squoosh API

API REST para compresión de imágenes usando Squoosh.app

## Características

- 🚀 **FastAPI** con documentación automática
- 🖼️ **Compresión de imágenes** usando Squoosh.app
- 📦 **Soporte múltiples formatos**: WebP, MozJPEG, AVIF, OxiPNG
- 🐋 **Docker ready** para despliegue en cualquier entorno
- 🔄 **Sin filesystem**: Procesa imágenes en memoria
- 📊 **Estadísticas** de compresión detalladas

## Estructura del Proyecto

```
squoosh-api/
├── main.py                 # Aplicación FastAPI principal
├── run_local.py           # Script para ejecutar localmente
├── pyproject.toml         # Dependencias Poetry
├── Dockerfile             # Configuración Docker
├── .env.example           # Variables de entorno ejemplo
├── models/
│   └── schemas.py         # Modelos Pydantic
├── routes/
│   ├── compression.py     # Endpoints de compresión
│   └── health.py         # Health checks
└── services/
    └── squoosh_service.py # Lógica de compresión
```

## Instalación Local

### Prerequisitos
- Python 3.12+
- Google Chrome instalado
- Poetry (opcional)

### Usando Poetry
```bash
# Clonar e instalar dependencias
git clone <tu-repo>
cd squoosh-api
poetry install

# Ejecutar
poetry run python run_local.py
```

### Usando pip
```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install fastapi uvicorn selenium webdriver-manager pillow python-multipart

# Ejecutar
python run_local.py
```

## Instalación con Docker

```bash
# Construir imagen
docker build -t squoosh-api .

# Ejecutar contenedor
docker run -p 8000:8000 squoosh-api
```

## Uso de la API

### Documentación Interactiva
Una vez ejecutándose, visita:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Endpoints Principales

#### 1. Comprimir desde Base64
```bash
POST /compress/base64
```

**Request Body:**
```json
{
  "image_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
  "format": "webp",
  "quality": 80,
  "filename": "mi_imagen.jpg"
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
  "filename": "mi_imagen.jpg"
}
```

#### 2. Comprimir desde Upload
```bash
POST /compress/upload
```

**Form Data:**
- `file`: Archivo de imagen
- `format`: Formato de salida (webp, mozjpeg, avif, oxipng)
- `quality`: Calidad 1-100

#### 3. Formatos Soportados
```bash
GET /compress/formats
```

#### 4. Health Check
```bash
GET /health
```

### Ejemplo con curl

```bash
# Comprimir imagen desde base64
curl -X POST "http://localhost:8000/compress/base64" \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "'$(base64 -i mi_imagen.jpg)'",
    "format": "webp",
    "quality": 80,
    "filename": "mi_imagen.jpg"
  }'

# Upload directo
curl -X POST "http://localhost:8000/compress/upload" \
  -F "file=@mi_imagen.jpg" \
  -F "format=webp" \
  -F "quality=80"
```

### Ejemplo con Python

```python
import requests
import base64

# Leer imagen
with open("mi_imagen.jpg", "rb") as f:
    image_bytes = f.read()
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')

# Comprimir
response = requests.post(
    "http://localhost:8000/compress/base64",
    json={
        "image_base64": image_base64,
        "format": "webp",
        "quality": 80,
        "filename": "mi_imagen.jpg"
    }
)

if response.status_code == 200:
    result = response.json()
    
    # Guardar imagen comprimida
    compressed_bytes = base64.b64decode(result["compressed_image_base64"])
    with open("imagen_comprimida.webp", "wb") as f:
        f.write(compressed_bytes)
    
    print(f"✅ Compresión exitosa!")
    print(f"📉 Reducción: {result['stats']['reduction_percent']}%")
else:
    print(f"❌ Error: {response.text}")
```

## Formatos Soportados

| Formato  | Descripción | Uso Recomendado |
|----------|-------------|-----------------|
| `webp` | WebP | Excelente balance calidad/tamaño |
| `mozjpeg` | MozJPEG | Mejor para fotografías |
| `avif` | AVIF | Máxima compresión (más lento) |
| `oxipng` | OxiPNG | PNG optimizado sin pérdida |

## Variables de Entorno

- `HOST`: Host de la aplicación (default: 127.0.0.1)
- `PORT`: Puerto de la aplicación (default: 8000)
- `DEBUG`: Modo debug (default: true)
- `CHROME_BIN`: Ruta del binario de Chrome (para Docker)

## Solución de Problemas

### Chrome no encontrado
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install google-chrome-stable

# Verificar instalación
google-chrome --version
```

### Errores de permisos en Docker
Asegúrate de que el usuario tiene permisos para ejecutar Chrome:
```dockerfile
USER myuser
```

### Timeouts en producción
Aumenta los timeouts en `squoosh_service.py` si es necesario:
```python
self.wait = WebDriverWait(self.driver, 60)  # Aumentar de 30 a 60
```

## Desarrollo

### Ejecutar tests
```bash
poetry run pytest
```

### Linting
```bash
poetry run black .
poetry run isort .
```

## Despliegue

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

### Variables de entorno en producción
```bash
export PORT=8000
export DEBUG=false
export CHROME_BIN=/usr/bin/google-chrome
```

## Limitaciones

- Requiere Google Chrome instalado
- Depende de squoosh.app (servicio externo)
- Procesamiento secuencial (una imagen a la vez)
- Timeouts configurables según entorno

## Contribuir

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request