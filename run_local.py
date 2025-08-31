#!/usr/bin/env python3
"""
Script para ejecutar la API localmente
"""
import os
import uvicorn
from dotenv import load_dotenv

# Cargar variables de entorno si existe archivo .env
load_dotenv()

if __name__ == "__main__":
    # Configuración para desarrollo local
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "true").lower() == "true"
    
    print(f"🚀 Iniciando Squoosh API en http://{host}:{port}")
    print(f"📖 Documentación disponible en http://{host}:{port}/docs")
    print(f"🔧 Modo debug: {debug}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )