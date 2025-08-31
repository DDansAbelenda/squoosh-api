# services/squoosh_service.py - Versión corregida compatible
import os
import time
import tempfile
import logging
from typing import Optional
from io import BytesIO
from PIL import Image

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException

logger = logging.getLogger(__name__)


class SquooshService:
    """Service for compressing images using Squoosh"""

    def __init__(self):
        """Initialize service without parameters"""
        self.driver = None
        self.wait = None
        self.temp_dir = tempfile.mkdtemp()
        logger.info(f"Temporary directory created: {self.temp_dir}")

    def _get_chrome_options(self):
        """Configurar opciones de Chrome para Railway"""
        options = Options()

        # Opciones esenciales para headless
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=VizDisplayCompositor')

        # Optimizaciones de memoria y rendimiento
        options.add_argument('--memory-pressure-off')
        options.add_argument('--max_old_space_size=4096')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')
        options.add_argument('--disable-javascript')

        # Configuraciones de descarga
        prefs = {
            "download.default_directory": self.temp_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": False
        }
        options.add_experimental_option("prefs", prefs)

        # Configurar user agent
        options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36')

        # Tamaño de ventana
        options.add_argument('--window-size=1920,1080')

        # Configurar binario de Chrome
        chrome_bin = os.environ.get('CHROME_BIN', '/usr/bin/google-chrome-stable')
        if os.path.exists(chrome_bin):
            options.binary_location = chrome_bin
            logger.info(f"Using Chrome binary: {chrome_bin}")

        return options

    def _get_chrome_service(self):
        """Configurar servicio de ChromeDriver"""
        chromedriver_path = os.environ.get('CHROMEDRIVER_PATH', '/usr/local/bin/chromedriver')

        if os.path.exists(chromedriver_path):
            logger.info(f"Using ChromeDriver at: {chromedriver_path}")
            return Service(chromedriver_path)
        else:
            # Fallback a WebDriver Manager
            logger.warning("ChromeDriver not found, falling back to WebDriver Manager")
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                driver_path = ChromeDriverManager().install()
                logger.info(f"WebDriver Manager installed ChromeDriver at: {driver_path}")
                return Service(driver_path)
            except Exception as e:
                logger.error(f"WebDriver Manager failed: {e}")
                raise Exception(f"Could not configure ChromeDriver: {e}")

    def create_driver(self):
        """Crear instancia de WebDriver"""
        if self.driver:
            return self.driver

        try:
            options = self._get_chrome_options()
            service = self._get_chrome_service()

            logger.info("Creating Chrome WebDriver...")
            self.driver = webdriver.Chrome(service=service, options=options)
            self.wait = WebDriverWait(self.driver, 30)

            logger.info("✅ Chrome WebDriver created successfully")
            return self.driver

        except Exception as e:
            logger.error(f"❌ Error creating Chrome driver: {e}")
            raise Exception(f"Error configuring Chrome driver: {e}")

    def compress_image_from_bytes(
            self,
            image_bytes: bytes,
            format_type: str = "webp",
            quality: int = 80,
            original_filename: str = "image"
    ) -> Optional[bytes]:
        """
        Compress image from bytes

        Args:
            image_bytes: Original image bytes
            format_type: Output format ('webp', 'mozjpeg', 'avif', 'oxipng')
            quality: Compression quality (0-100)
            original_filename: Original filename (for extension)

        Returns:
            bytes: Compressed image or None if error
        """
        temp_input_path = None

        try:
            # Create driver if not exists
            if not self.driver:
                self.create_driver()

            # Validate image
            try:
                img = Image.open(BytesIO(image_bytes))
                img.verify()
            except Exception:
                raise ValueError("Bytes do not correspond to a valid image")

            # Create temporary input file
            file_ext = self._get_file_extension(original_filename)
            temp_input_path = os.path.join(self.temp_dir, f"input_{int(time.time())}{file_ext}")

            with open(temp_input_path, 'wb') as f:
                f.write(image_bytes)

            # Process with Squoosh
            compressed_path = self._compress_with_squoosh(temp_input_path, format_type, quality)

            if compressed_path and os.path.exists(compressed_path):
                # Read compressed image
                with open(compressed_path, 'rb') as f:
                    compressed_bytes = f.read()

                # Clean up temporary files
                self._cleanup_temp_files([temp_input_path, compressed_path])

                return compressed_bytes

            return None

        except Exception as e:
            # Clean up temporary files on error
            if temp_input_path:
                self._cleanup_temp_files([temp_input_path])
            raise Exception(f"Error compressing image: {e}")

    def _compress_with_squoosh(self, image_path: str, format_type: str, quality: int) -> Optional[str]:
        """Compress image using Squoosh web app"""
        try:
            # Navigate to Squoosh
            logger.info("Loading Squoosh.app...")
            self.driver.get("https://squoosh.app/editor")
            time.sleep(5)

            # Upload image
            logger.info("Uploading image...")
            file_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )
            file_input.send_keys(os.path.abspath(image_path))

            # Wait for image to load
            logger.info("Waiting for image processing...")
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "canvas"))
            )
            time.sleep(3)

            # Configure format and quality
            logger.info(f"Setting format: {format_type}, quality: {quality}")
            self._set_format(format_type, quality)
            time.sleep(3)

            # Download processed image
            logger.info("Downloading compressed image...")
            return self._download_compressed()

        except Exception as e:
            logger.error(f"Error in Squoosh processing: {e}")
            raise Exception(f"Error in Squoosh: {e}")

    def _set_format(self, format_type: str, quality: int):
        """Configure format and quality"""
        try:
            # Format mapping
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
            logger.info(f"Setting format to: {format_value}")

            # Find and change format
            format_select = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "select"))
            )

            self.driver.execute_script(f"arguments[0].value = '{format_value}'", format_select)
            self.driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", format_select)
            time.sleep(2)

            # Adjust quality if available
            if format_type.lower() in ['webp', 'mozjpeg', 'jpg', 'jpeg', 'avif']:
                try:
                    quality_input = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='range']"))
                    )

                    self.driver.execute_script(f"arguments[0].value = {quality}", quality_input)
                    self.driver.execute_script("arguments[0].dispatchEvent(new Event('input'))", quality_input)
                    self.driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", quality_input)
                    logger.info(f"Quality set to: {quality}")
                    time.sleep(2)

                except TimeoutException:
                    logger.warning(f"Quality control not available for format: {format_type}")

        except Exception as e:
            logger.error(f"Error setting format: {e}")
            raise Exception(f"Error configuring format: {e}")

    def _download_compressed(self) -> Optional[str]:
        """Download compressed image"""
        try:
            # Get existing files before download
            files_before = set(os.listdir(self.temp_dir))

            # Search for enabled download link
            download_link = None
            max_attempts = 30

            for attempt in range(max_attempts):
                try:
                    download_links = self.driver.find_elements(By.CSS_SELECTOR, "a[download]")
                    logger.info(f"Found {len(download_links)} download links on attempt {attempt + 1}")

                    for i, link in enumerate(download_links):
                        try:
                            classes = link.get_attribute('class') or ''
                            download_name = link.get_attribute('download') or ''

                            logger.info(
                                f"Link {i}: classes='{classes}', download='{download_name}', enabled={link.is_enabled()}")

                            # Search for enabled link
                            if (link.is_enabled() and
                                    link.is_displayed() and
                                    download_name and
                                    'disable' not in classes.lower()):
                                download_link = link
                                logger.info(f"Found valid download link: {download_name}")
                                break

                        except Exception as e:
                            logger.warning(f"Error checking link {i}: {e}")

                    if download_link:
                        break

                    time.sleep(1)

                except Exception as e:
                    logger.warning(f"Error finding download links on attempt {attempt + 1}: {e}")
                    time.sleep(1)

            if not download_link:
                raise Exception("No enabled download button found after all attempts")

            # Click download
            try:
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", download_link)
                time.sleep(1)
                self.driver.execute_script("arguments[0].click();", download_link)
                logger.info("Download link clicked")
            except Exception as e:
                logger.error(f"Error clicking download: {e}")
                raise

            # Wait for download
            logger.info("Waiting for file download...")
            for attempt in range(30):
                time.sleep(1)
                try:
                    files_after = set(os.listdir(self.temp_dir))
                    new_files = files_after - files_before

                    if new_files:
                        downloaded_file = os.path.join(self.temp_dir, list(new_files)[0])
                        logger.info(f"File downloaded: {downloaded_file}")
                        return downloaded_file

                except Exception as e:
                    logger.warning(f"Error checking downloads on attempt {attempt + 1}: {e}")

            raise Exception("Timeout waiting for download")

        except Exception as e:
            logger.error(f"Error in download process: {e}")
            raise Exception(f"Error downloading: {e}")

    def _get_file_extension(self, filename: str) -> str:
        """Get file extension"""
        _, ext = os.path.splitext(filename.lower())
        return ext if ext else '.jpg'

    def _cleanup_temp_files(self, file_paths: list):
        """Clean up temporary files"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"Cleaned up temp file: {file_path}")
            except Exception as e:
                logger.warning(f"Could not clean up {file_path}: {e}")

    def close_driver(self):
        """Cerrar WebDriver si existe"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("✅ Chrome WebDriver closed")
            except Exception as e:
                logger.warning(f"Warning closing driver: {e}")
            finally:
                self.driver = None
                self.wait = None

    def close(self):
        """Close all resources"""
        self.close_driver()

        # Clean up temporary directory
        if hasattr(self, 'temp_dir') and self.temp_dir and os.path.exists(self.temp_dir):
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temp directory: {self.temp_dir}")
            except Exception as e:
                logger.warning(f"Could not clean up temp directory: {e}")

    def get_compression_stats(self, original_bytes: bytes, compressed_bytes: bytes) -> dict:
        """Calculate compression statistics"""
        original_size = len(original_bytes)
        compressed_size = len(compressed_bytes)
        reduction_percent = ((original_size - compressed_size) / original_size) * 100

        return {
            "original_size": original_size,
            "compressed_size": compressed_size,
            "reduction_percent": round(reduction_percent, 2),
            "compression_ratio": round(original_size / compressed_size, 2)
        }