# Dockerfile simplificado para Railway
FROM python:3.12-slim

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Instalar dependencias del sistema y Chrome en una sola capa
RUN apt-get update && apt-get install -y \
    wget curl gnupg ca-certificates \
    fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 \
    libatspi2.0-0 libdrm2 libgtk-3-0 libnspr4 libnss3 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libxss1 libxtst6 xdg-utils \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /etc/apt/trusted.gpg.d/google-chrome.gpg \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# Copiar archivos
COPY . .

# Instalar dependencias Python
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
    fastapi==0.115.0 \
    uvicorn==0.30.6 \
    selenium==4.25.0 \
    webdriver-manager==4.0.0 \
    pillow==10.4.0 \
    python-multipart==0.0.9

# Exponer puerto
EXPOSE 8000

# Comando de inicio simple
CMD python main.py