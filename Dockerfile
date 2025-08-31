FROM python:3.12-slim

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    CHROME_BIN=/usr/bin/google-chrome-stable \
    CHROMEDRIVER_PATH=/usr/local/bin/chromedriver

# Instalar dependencias del sistema y Chrome con ChromeDriver
RUN apt-get update && apt-get install -y \
    wget curl unzip gnupg ca-certificates \
    fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 \
    libatspi2.0-0 libdrm2 libgtk-3-0 libnspr4 libnss3 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libxss1 libxtst6 xdg-utils \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /etc/apt/trusted.gpg.d/google-chrome.gpg \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && CHROME_VERSION=$(google-chrome --version | cut -d ' ' -f3 | cut -d '.' -f1-3) \
    && echo "Chrome version: $CHROME_VERSION" \
    && wget -q "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}.0/linux64/chromedriver-linux64.zip" -O /tmp/chromedriver.zip \
    && unzip /tmp/chromedriver.zip -d /tmp/ \
    && mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver \
    && rm -rf /tmp/chromedriver* \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Directorio de trabajo
WORKDIR /app

# Copiar requirements primero (para mejor cache de Docker)
COPY requirements.txt* ./

# Instalar dependencias Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    fastapi==0.115.0 \
    uvicorn[standard]==0.30.6 \
    selenium==4.25.0 \
    pillow==10.4.0 \
    python-multipart==0.0.9

# Copiar el resto del código
COPY . .

# Verificar instalación (esto aparecerá en los logs de build)
RUN echo "=== Verification ===" \
    && google-chrome --version \
    && chromedriver --version \
    && python --version \
    && echo "=== Ready ==="

# Puerto dinámico de Railway
EXPOSE $PORT

# Comando de inicio
CMD ["python", "main.py"]