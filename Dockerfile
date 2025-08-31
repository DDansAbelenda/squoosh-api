# Dockerfile para Railway con correcciones
FROM python:3.12-slim

# Evitar prompts interactivos
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libdrm2 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libxss1 \
    libxtst6 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Instalar Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /etc/apt/trusted.gpg.d/google-chrome.gpg \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario antes de crear el directorio de trabajo
RUN adduser --disabled-password --gecos "" appuser

# Directorio de trabajo
WORKDIR /app

# Cambiar ownership del directorio
RUN chown -R appuser:appuser /app

# Copiar requirements como root primero
COPY requirements.txt* ./

# Instalar dependencias Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    fastapi==0.115.0 \
    uvicorn[standard]==0.30.0 \
    selenium==4.25.0 \
    webdriver-manager==4.0.0 \
    pillow==10.4.0 \
    python-multipart==0.0.9

# Copiar código y cambiar ownership
COPY . .
RUN chown -R appuser:appuser /app

# Cambiar a usuario no-root
USER appuser

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CHROME_BIN=/usr/bin/google-chrome \
    DISPLAY=:99

# Puerto
EXPOSE 8000

# Comando de inicio con ruta completa
CMD ["/usr/local/bin/python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]