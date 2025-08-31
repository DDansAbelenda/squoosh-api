import os
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def get_chrome_service():
    """Get Chrome service with correct driver path"""
    # Check if we're in production (Railway/Docker)
    chromedriver_path = os.getenv("CHROMEDRIVER_PATH")

    if chromedriver_path and os.path.exists(chromedriver_path):
        # Use pre-installed chromedriver in production
        return Service(chromedriver_path)
    else:
        # Use webdriver-manager for local development
        return Service(ChromeDriverManager().install())