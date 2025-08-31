import os
import time
import tempfile
import base64
from typing import Optional, Tuple
from io import BytesIO
from PIL import Image

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service


class SquooshService:
    """Servicio para comprimir imágenes usando Squoosh sin usar filesystem permanente"""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        self.wait = None
        self.temp_dir = None

    def __enter__(self):
        self._setup_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _setup_driver(self):
        """Configurar el driver de Chrome para entorno Docker/Linux"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless")

        # Opciones específicas para Docker/Linux
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-features=TranslateUI")
        chrome_options.add_argument("--disable-ipc-flooding-protection")
        chrome_options.add_argument("--window-size=1920,1080")

        # Crear directorio temporal
        self.temp_dir = tempfile.mkdtemp()

        # Configurar directorio de descarga temporal
        prefs = {
            "download.default_directory": self.temp_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)

        # Configurar driver
        try:
            # En Docker, usar Chrome binario del sistema
            if os.getenv("CHROME_BIN"):
                chrome_options.binary_location = os.getenv("CHROME_BIN")

            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)

        except Exception as e:
            raise Exception(f"Error configurando Chrome driver: {e}")

    def compress_image_from_bytes(
            self,
            image_bytes: bytes,
            format_type: str = "webp",
            quality: int = 80,
            original_filename: str = "image"
    ) -> Optional[bytes]:
        """
        Comprimir imagen desde bytes
        
        Args:
            image_bytes: Bytes de la imagen original
            format_type: Formato de salida ('webp', 'mozjpeg', 'avif', 'oxipng')
            quality: Calidad de compresión (0-100)
            original_filename: Nombre del archivo original (para extensión)
        
        Returns:
            bytes: Imagen comprimida o None si hay error
        """
        temp_input_path = None

        try:
            # Validar imagen
            try:
                img = Image.open(BytesIO(image_bytes))
                img.verify()
            except Exception:
                raise ValueError("Los bytes no corresponden a una imagen válida")

            # Crear archivo temporal de entrada
            file_ext = self._get_file_extension(original_filename)
            temp_input_path = os.path.join(self.temp_dir, f"input{file_ext}")

            with open(temp_input_path, 'wb') as f:
                f.write(image_bytes)

            # Procesar con Squoosh
            compressed_path = self._compress_with_squoosh(temp_input_path, format_type, quality)

            if compressed_path and os.path.exists(compressed_path):
                # Leer imagen comprimida
                with open(compressed_path, 'rb') as f:
                    compressed_bytes = f.read()

                # Limpiar archivos temporales
                self._cleanup_temp_files([temp_input_path, compressed_path])

                return compressed_bytes

            return None

        except Exception as e:
            # Limpiar archivos temporales en caso de error
            if temp_input_path:
                self._cleanup_temp_files([temp_input_path])
            raise Exception(f"Error comprimiendo imagen: {e}")

    def _compress_with_squoosh(self, image_path: str, format_type: str, quality: int) -> Optional[str]:
        """Comprimir imagen usando Squoosh web app"""
        try:
            # Navegar a Squoosh
            self.driver.get("https://squoosh.app/editor")
            time.sleep(3)

            # Subir imagen
            file_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file']")
            file_input.send_keys(os.path.abspath(image_path))

            # Esperar a que aparezcan los resultados
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "._results_17s86_26"))
            )
            time.sleep(3)

            # Configurar formato y calidad
            self._set_format(format_type, quality)
            time.sleep(3)

            # Descargar imagen procesada
            return self._download_compressed()

        except Exception as e:
            raise Exception(f"Error en Squoosh: {e}")

    def _set_format(self, format_type: str, quality: int):
        """Configurar formato y calidad"""
        try:
            # Mapeo de formatos
            format_map = {
                "webp": "webP",
                "mozjpeg": "mozJPEG",
                "jpg": "mozJPEG",
                "jpeg": "mozJPEG",
                "avif": "avif",
                "oxipng": "oxiPNG",
                "png": "oxiPNG",
                "browserjpeg": "browserJPEG",
                "browserpng": "browserPNG"
            }

            format_value = format_map.get(format_type.lower(), "webP")

            # Cambiar formato
            format_select = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "select._builtin-select_1onzk_5"))
            )

            self.driver.execute_script(f"arguments[0].value = '{format_value}'", format_select)
            self.driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", format_select)
            time.sleep(3)

            # Ajustar calidad si está disponible
            try:
                quality_input = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='range'][name='quality']"))
                )

                self.driver.execute_script(f"arguments[0].value = {quality}", quality_input)
                self.driver.execute_script("arguments[0].dispatchEvent(new Event('input'))", quality_input)
                self.driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", quality_input)
                time.sleep(2)

            except TimeoutException:
                pass  # Control de calidad no disponible para este formato

        except Exception as e:
            raise Exception(f"Error configurando formato: {e}")

    def _download_compressed(self) -> Optional[str]:
        """Descargar imagen comprimida"""
        try:
            # Obtener archivos existentes antes de la descarga
            files_before = set(os.listdir(self.temp_dir))

            # Buscar enlace de descarga habilitado
            download_link = None
            max_attempts = 20

            for _ in range(max_attempts):
                try:
                    download_links = self.driver.find_elements(By.CSS_SELECTOR, "a[download]")

                    for link in download_links:
                        classes = link.get_attribute('class') or ''
                        download_name = link.get_attribute('download') or ''

                        # Buscar link que no esté deshabilitado y no sea la imagen original
                        if ('_download-disable_' not in classes and
                                download_name and
                                link.is_enabled() and
                                link.is_displayed()):
                            download_link = link
                            break

                    if download_link:
                        break

                    time.sleep(2)

                except Exception:
                    time.sleep(2)

            if not download_link:
                raise Exception("No se encontró botón de descarga habilitado")

            # Hacer scroll y click
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", download_link)
            time.sleep(1)

            try:
                download_link.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", download_link)

            # Esperar descarga
            for _ in range(30):
                time.sleep(1)
                files_after = set(os.listdir(self.temp_dir))
                new_files = files_after - files_before

                if new_files:
                    downloaded_file = os.path.join(self.temp_dir, list(new_files)[0])
                    return downloaded_file

            raise Exception("Timeout esperando descarga")

        except Exception as e:
            raise Exception(f"Error descargando: {e}")

    def _get_file_extension(self, filename: str) -> str:
        """Obtener extensión del archivo"""
        _, ext = os.path.splitext(filename.lower())
        return ext if ext else '.jpg'

    def _cleanup_temp_files(self, file_paths: list):
        """Limpiar archivos temporales"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass

    def close(self):
        """Cerrar recursos"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass

        # Limpiar directorio temporal
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
            except:
                pass

    def get_compression_stats(self, original_bytes: bytes, compressed_bytes: bytes) -> dict:
        """Calcular estadísticas de compresión"""
        original_size = len(original_bytes)
        compressed_size = len(compressed_bytes)
        reduction_percent = ((original_size - compressed_size) / original_size) * 100

        return {
            "original_size": original_size,
            "compressed_size": compressed_size,
            "reduction_percent": round(reduction_percent, 2),
            "compression_ratio": round(original_size / compressed_size, 2)
        }
