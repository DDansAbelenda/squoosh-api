#!/usr/bin/env python3
"""
Script de ejemplo para probar la API
"""
import requests
import base64
from PIL import Image
from io import BytesIO

# Configuración
API_BASE_URL = "http://localhost:8000"

def create_test_image():
    """Crear imagen de prueba"""
    # Crear imagen simple de prueba
    img = Image.new('RGB', (200, 200), color='red')
    
    # Convertir a bytes
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    image_bytes = buffer.getvalue()
    
    return image_bytes

def test_health():
    """Probar health check"""
    print("🏥 Probando health check...")
    response = requests.get(f"{API_BASE_URL}/health")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Health OK - Chrome disponible: {data['chrome_available']}")
        return True
    else:
        print(f"❌ Health failed: {response.status_code}")
        return False

def test_compress_base64():
    """Probar compresión desde base64"""
    print("\n📦 Probando compresión desde base64...")
    
    # Crear imagen de prueba
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
        print(f"✅ Compresión exitosa!")
        print(f"📊 Tamaño original: {data['stats']['original_size']:,} bytes")
        print(f"📊 Tamaño comprimido: {data['stats']['compressed_size']:,} bytes")
        print(f"📊 Reducción: {data['stats']['reduction_percent']}%")
        
        # Guardar imagen comprimida (opcional)
        compressed_bytes = base64.b64decode(data["compressed_image_base64"])
        with open("test_compressed.webp", "wb") as f:
            f.write(compressed_bytes)
        print("💾 Imagen guardada como test_compressed.webp")
        
        return True
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_upload():
    """Probar compresión por upload"""
    print("\n📤 Probando compresión por upload...")
    
    # Crear archivo temporal
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
        print(f"✅ Upload comprimido exitosamente!")
        print(f"📊 Reducción: {data['stats']['reduction_percent']}%")
        return True
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_formats():
    """Probar endpoint de formatos"""
    print("\n📋 Probando formatos soportados...")
    
    response = requests.get(f"{API_BASE_URL}/compress/formats")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Formatos obtenidos:")
        for format_name, description in data["formats"].items():
            print(f"  • {format_name}: {description}")
        return True
    else:
        print(f"❌ Error: {response.status_code}")
        return False

def main():
    """Ejecutar todas las pruebas"""
    print("🚀 Iniciando pruebas de la API Squoosh...")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health),
        ("Formatos", test_formats),
        ("Compresión Base64", test_compress_base64),
        ("Upload", test_upload)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nResultado: {passed}/{total} pruebas exitosas")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron!")
    else:
        print("⚠️ Algunas pruebas fallaron")

if __name__ == "__main__":
    main()