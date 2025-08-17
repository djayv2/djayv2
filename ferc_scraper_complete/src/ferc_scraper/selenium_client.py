from __future__ import annotations

import logging
import time
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

logger = logging.getLogger(__name__)


class SeleniumHTTPClient:
    """HTTP client using Selenium to bypass Cloudflare protection"""
    
    def __init__(self, headless: bool = True, timeout: int = 30):
        self.headless = headless
        self.timeout = timeout
        self.driver: Optional[webdriver.Chrome] = None
        
    def __enter__(self):
        self._setup_driver()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cleanup()
        
    def _setup_driver(self):
        """Set up Chrome driver with anti-detection measures"""
        try:
            # Use system ChromeDriver
            service = Service('/usr/bin/chromedriver')
            
            # Configure Chrome options
            options = Options()
            
            if self.headless:
                options.add_argument('--headless')
            
            # Anti-detection options
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Additional options to avoid detection
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            options.add_argument('--disable-images')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-web-security')
            options.add_argument('--allow-running-insecure-content')
            
            # Set user agent
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Create driver
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Selenium driver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Selenium driver: {e}")
            raise
            
    def _cleanup(self):
        """Clean up driver resources"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Selenium driver closed")
            except Exception as e:
                logger.warning(f"Error closing driver: {e}")
            finally:
                self.driver = None
                
    def wait_for_cloudflare(self, timeout: int = 30) -> bool:
        """Wait for Cloudflare challenge to complete"""
        try:
            # Wait for page to load
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Check if we're still on a Cloudflare challenge page
            page_source = self.driver.page_source.lower()
            if "just a moment" in page_source or "checking your browser" in page_source:
                logger.info("Waiting for Cloudflare challenge to complete...")
                time.sleep(10)  # Wait longer for challenge
                
                # Wait again for completion
                WebDriverWait(self.driver, timeout).until(
                    lambda driver: "just a moment" not in driver.page_source.lower()
                )
                
            logger.info("Cloudflare challenge completed")
            return True
            
        except TimeoutException:
            logger.warning("Timeout waiting for Cloudflare challenge")
            return False
        except Exception as e:
            logger.error(f"Error during Cloudflare wait: {e}")
            return False
            
    def get_page(self, url: str) -> Optional[str]:
        """Get page content using Selenium"""
        if not self.driver:
            raise RuntimeError("Driver not initialized. Use context manager.")
            
        try:
            logger.info(f"Fetching page: {url}")
            
            # Navigate to URL
            self.driver.get(url)
            
            # Wait for Cloudflare challenge to complete
            if not self.wait_for_cloudflare(self.timeout):
                logger.error("Failed to bypass Cloudflare protection")
                return None
                
            # Get page source
            page_source = self.driver.page_source
            
            # Check if we got the actual content
            if len(page_source) < 1000:
                logger.warning("Page content seems too short, might be blocked")
                return None
                
            logger.info(f"Successfully fetched page, content length: {len(page_source)}")
            return page_source
            
        except WebDriverException as e:
            logger.error(f"WebDriver error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            return None
            
    def get_page_with_retry(self, url: str, max_retries: int = 3) -> Optional[str]:
        """Get page with retry logic"""
        for attempt in range(max_retries):
            try:
                content = self.get_page(url)
                if content:
                    return content
                    
                logger.warning(f"Attempt {attempt + 1} failed, retrying...")
                time.sleep(2 ** attempt)  # Exponential backoff
                
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed with error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    
        logger.error(f"Failed to fetch {url} after {max_retries} attempts")
        return None