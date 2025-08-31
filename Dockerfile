# Dockerfile para Railway - Sin Chrome
FROM python:3.12-slim

# Evitar prompts interactivos
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependencias básicas del sistema
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario antes de crear el directorio de trabajo
RUN adduser --disabled-password --gecos "" appuser

# Directorio de trabajo
WORKDIR /app

# Cambiar ownership del directorio
RUN chown -R appuser:appuser /app

# Copiar requirements como root primero
COPY requirements.txt* ./

# Instalar dependencias Python (sin selenium ni webdriver-manager)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    fastapi==0.115.0 \
    uvicorn[standard]==0.30.0 \
    pillow==10.4.0 \
    python-multipart==0.0.9

# Copiar código y cambiar ownership
COPY . .
RUN chown -R appuser:appuser /app

# Cambiar a usuario no-root
USER appuser

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Comando de inicio con variable PORT de Railway y opciones de memoria
CMD /usr/local/bin/python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1