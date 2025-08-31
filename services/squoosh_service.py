import os
import time
import tempfile
from typing import Optional
from io import BytesIO
from PIL import Image

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from chromedriver_config import get_chrome_service


class SquooshService:
    """Service for compressing images using Squoosh without permanent filesystem usage"""

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
        """Configure Chrome driver for Docker/Linux environment"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless")

        # Base options for all environments
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-features=TranslateUI")
        chrome_options.add_argument("--window-size=1920,1080")

        # Detect if running in Docker/Railway (Linux container)
        is_docker = os.path.exists('/.dockerenv') or os.getenv('CHROMEDRIVER_PATH')

        if is_docker:
            # Additional options for Docker/Railway
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--memory-pressure-off")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--remote-debugging-port=9222")
            chrome_options.add_argument("--disable-crash-reporter")
            chrome_options.add_argument("--disable-in-process-stack-traces")
            chrome_options.add_argument("--disable-logging")
            chrome_options.add_argument("--disable-dev-tools")
            chrome_options.add_argument("--disable-hang-monitor")
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--no-default-browser-check")
            chrome_options.add_argument("--disable-background-mode")

        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp()

        # Configure temporary download directory
        prefs = {
            "download.default_directory": self.temp_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)

        # Configure driver
        try:
            # In Docker, use system Chrome binary
            if os.getenv("CHROME_BIN"):
                chrome_options.binary_location = os.getenv("CHROME_BIN")

            service = get_chrome_service()
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)

        except Exception as e:
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
            # Validate image
            try:
                img = Image.open(BytesIO(image_bytes))
                img.verify()
            except Exception:
                raise ValueError("Bytes do not correspond to a valid image")

            # Create temporary input file
            file_ext = self._get_file_extension(original_filename)
            temp_input_path = os.path.join(self.temp_dir, f"input{file_ext}")

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
            self.driver.get("https://squoosh.app/editor")
            time.sleep(3)

            # Upload image
            file_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file']")
            file_input.send_keys(os.path.abspath(image_path))

            # Wait for results to appear
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "._results_17s86_26"))
            )
            time.sleep(3)

            # Configure format and quality
            self._set_format(format_type, quality)
            time.sleep(3)

            # Download processed image
            return self._download_compressed()

        except Exception as e:
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

            # Change format
            format_select = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "select._builtin-select_1onzk_5"))
            )

            self.driver.execute_script(f"arguments[0].value = '{format_value}'", format_select)
            self.driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", format_select)
            time.sleep(3)

            # Adjust quality if available
            try:
                quality_input = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='range'][name='quality']"))
                )

                self.driver.execute_script(f"arguments[0].value = {quality}", quality_input)
                self.driver.execute_script("arguments[0].dispatchEvent(new Event('input'))", quality_input)
                self.driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", quality_input)
                time.sleep(2)

            except TimeoutException:
                pass  # Quality control not available for this format

        except Exception as e:
            raise Exception(f"Error configuring format: {e}")

    def _download_compressed(self) -> Optional[str]:
        """Download compressed image"""
        try:
            # Get existing files before download
            files_before = set(os.listdir(self.temp_dir))

            # Search for enabled download link
            download_link = None
            max_attempts = 20

            for _ in range(max_attempts):
                try:
                    download_links = self.driver.find_elements(By.CSS_SELECTOR, "a[download]")

                    for link in download_links:
                        classes = link.get_attribute('class') or ''
                        download_name = link.get_attribute('download') or ''

                        # Search for link that is not disabled and not the original image
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
                raise Exception("No enabled download button found")

            # Scroll and click
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", download_link)
            time.sleep(1)

            try:
                download_link.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", download_link)

            # Wait for download
            for _ in range(30):
                time.sleep(1)
                files_after = set(os.listdir(self.temp_dir))
                new_files = files_after - files_before

                if new_files:
                    downloaded_file = os.path.join(self.temp_dir, list(new_files)[0])
                    return downloaded_file

            raise Exception("Timeout waiting for download")

        except Exception as e:
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
            except Exception:
                pass

    def close(self):
        """Close resources"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass

        # Clean up temporary directory
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
            except:
                pass

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