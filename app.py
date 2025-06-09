# app.py - Improved version with better error handling

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import json
import time
import re
import logging
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def fetch_json_with_selenium(url, output_file="json_data.txt"):
    """
    Opens a headless browser, fetches JSON data from URL, and saves to file.

    Args:
        url (str): The URL to fetch JSON data from
        output_file (str): Name of the output file to save JSON data
    """
    driver = None
    
    try:
        logger.info("Configuring Chrome options...")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--disable-javascript")  # Remove if JS is needed
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36")
        
        # Additional Docker-specific options
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        
        logger.info("Starting Chrome browser...")
        
        try:
            # Try to use ChromeDriverManager first
            service = Service(ChromeDriverManager().install())
            logger.info(f"Using ChromeDriver from: {service.path}")
        except Exception as e:
            logger.warning(f"ChromeDriverManager failed: {e}, trying system chromedriver")
            # Fallback to system chromedriver
            service = Service()
        
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)
        
        logger.info(f"Navigating to: {url}")
        driver.get(url)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        logger.info("Page loaded, extracting content...")
        
        # Try multiple methods to extract JSON
        json_text = None
        
        # Method 1: Look for <pre> tag
        try:
            pre_elements = driver.find_elements(By.TAG_NAME, "pre")
            if pre_elements:
                json_text = pre_elements[0].text
                logger.info("Found JSON in <pre> tag")
        except Exception as e:
            logger.debug(f"No <pre> tag found: {e}")
        
        # Method 2: Look for JSON in body
        if not json_text:
            try:
                body_element = driver.find_element(By.TAG_NAME, "body")
                body_text = body_element.text.strip()
                if body_text and (body_text.startswith('{') or body_text.startswith('[')):
                    json_text = body_text
                    logger.info("Found JSON in body text")
            except Exception as e:
                logger.debug(f"Could not extract from body: {e}")
        
        # Method 3: Parse page source
        if not json_text:
            try:
                page_source = driver.page_source
                logger.debug(f"Page source length: {len(page_source)}")
                
                # Look for JSON in <pre> tags in source
                json_match = re.search(r'<pre[^>]*>(.*?)</pre>', page_source, re.DOTALL)
                if json_match:
                    json_text = json_match.group(1).strip()
                    logger.info("Found JSON in page source <pre> tag")
                else:
                    # Look for JSON patterns
                    json_match = re.search(r'(\{.*\}|\[.*\])', page_source, re.DOTALL)
                    if json_match:
                        json_text = json_match.group(1).strip()
                        logger.info("Found JSON pattern in page source")
            except Exception as e:
                logger.error(f"Error parsing page source: {e}")
        
        if not json_text:
            logger.error("No JSON content found on the page")
            return False
        
        logger.info(f"Extracted content length: {len(json_text)}")
        logger.debug(f"Content preview: {json_text[:500]}...")
        
        # Try to parse and format JSON
        try:
            json_data = json.loads(json_text)
            formatted_json = json.dumps(json_data, indent=2, ensure_ascii=False)
            logger.info("✓ Valid JSON data retrieved and formatted")
        except json.JSONDecodeError as e:
            logger.warning(f"Content is not valid JSON: {e}")
            formatted_json = json_text
            logger.info("⚠ Content saved as-is (may not be valid JSON)")
        
        # Save to file
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(formatted_json)
            logger.info(f"✓ Data saved to: {output_file}")
            
            # Verify file was written
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                logger.info(f"✓ File size: {file_size} bytes")
            else:
                logger.error("✗ File was not created")
                return False
                
        except Exception as e:
            logger.error(f"✗ Error saving file: {e}")
            return False
        
        return True

    except TimeoutException:
        logger.error("✗ Page load timeout")
        return False
    except WebDriverException as e:
        logger.error(f"✗ WebDriver error: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False
    
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("✓ Browser closed")
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")

# Test function for debugging
def test_fetch(url):
    """Test function to debug locally"""
    logger.info(f"Testing fetch for URL: {url}")
    result = fetch_json_with_selenium(url)
    logger.info(f"Test result: {result}")
    return result

if __name__ == "__main__":
    # Test with a sample JSON URL
    test_url = "https://jsonplaceholder.typicode.com/posts/1"
    test_fetch(test_url)