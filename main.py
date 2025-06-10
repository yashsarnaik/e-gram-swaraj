from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time
import re
from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="URL Processing API",
    description="API for processing URLs using Undetected ChromeDriver",
    version="1.0.0"
)

class URLRequest(BaseModel):
    url: HttpUrl
    wait_time: Optional[int] = 3
    timeout: Optional[int] = 30

class URLResponse(BaseModel):
    success: bool
    url: str
    content: Optional[str] = None
    json_data: Optional[Dict[Any, Any]] = None
    error: Optional[str] = None
    content_type: Optional[str] = None
    status_code: Optional[int] = None

class WebScraper:
    def __init__(self):
        self.driver = None
    
    def setup_driver(self):
        """Setup undetected Chrome driver with headed mode"""
        try:
            # Use minimal options for better compatibility
            options = uc.ChromeOptions()

            # Basic options only
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            # Initialize undetected Chrome driver with minimal configuration
            self.driver = uc.Chrome(options=options, version_main=None)

            logger.info("Undetected ChromeDriver initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to setup driver: {str(e)}")
            return False
    
    def process_url(self, url: str, wait_time: int = 3, timeout: int = 30) -> URLResponse:
        """Process a URL and extract content"""
        try:
            if not self.setup_driver():
                return URLResponse(
                    success=False,
                    url=url,
                    error="Failed to initialize browser driver"
                )
            
            # Set page load timeout
            self.driver.set_page_load_timeout(timeout)
            
            # Navigate to the URL
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            time.sleep(wait_time)
            
            # Get page content
            page_content = self.driver.page_source
            
            # Try to extract JSON or text content
            content_result = self._extract_content()
            
            return URLResponse(
                success=True,
                url=url,
                content=content_result.get("raw_content"),
                json_data=content_result.get("json_data"),
                content_type=content_result.get("content_type"),
                status_code=200
            )
            
        except Exception as e:
            logger.error(f"Error processing URL {url}: {str(e)}")
            return URLResponse(
                success=False,
                url=url,
                error=str(e)
            )
        
        finally:
            self._cleanup()
    
    def _extract_content(self):
        """Extract content from the current page"""
        try:
            # Method 1: Try to get JSON from <pre> tag (common for JSON APIs)
            try:
                pre_element = self.driver.find_element(By.TAG_NAME, "pre")
                raw_content = pre_element.text
                content_type = "json"
            except:
                # Method 2: Try to get text from <body> tag
                try:
                    body_element = self.driver.find_element(By.TAG_NAME, "body")
                    raw_content = body_element.text
                    content_type = "text"
                except:
                    # Method 3: Use page source directly
                    raw_content = self.driver.page_source
                    content_type = "html"
            
            # Try to parse as JSON
            json_data = None
            if raw_content:
                # Clean up content if it contains HTML
                if raw_content.startswith('<!DOCTYPE html>') or raw_content.startswith('<html'):
                    # Try to extract JSON from HTML
                    json_match = re.search(r'<pre[^>]*>(.*?)</pre>', raw_content, re.DOTALL)
                    if json_match:
                        clean_content = json_match.group(1)
                    else:
                        # Try to find JSON-like content
                        json_match = re.search(r'(\{.*\}|\[.*\])', raw_content, re.DOTALL)
                        clean_content = json_match.group(1) if json_match else raw_content
                else:
                    clean_content = raw_content
                
                # Try to parse as JSON
                try:
                    json_data = json.loads(clean_content)
                    content_type = "json"
                except json.JSONDecodeError:
                    # Not valid JSON, keep as text
                    pass
            
            return {
                "raw_content": raw_content,
                "json_data": json_data,
                "content_type": content_type
            }
            
        except Exception as e:
            logger.error(f"Error extracting content: {str(e)}")
            return {
                "raw_content": None,
                "json_data": None,
                "content_type": "error"
            }
    
    def _cleanup(self):
        """Clean up the driver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser driver closed successfully")
            except Exception as e:
                logger.error(f"Error closing driver: {str(e)}")
            finally:
                self.driver = None

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "URL Processing API",
        "version": "1.0.0",
        "endpoints": {
            "POST /process-url": "Process a URL and extract content",
            "GET /health": "Health check endpoint"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "API is running"}

@app.post("/process-url", response_model=URLResponse)
async def process_url(request: URLRequest):
    """
    Process a URL and extract content using Undetected ChromeDriver
    
    - **url**: The URL to process
    - **wait_time**: Time to wait after page load (default: 3 seconds)
    - **timeout**: Page load timeout (default: 30 seconds)
    """
    try:
        scraper = WebScraper()
        result = scraper.process_url(
            url=str(request.url),
            wait_time=request.wait_time,
            timeout=request.timeout
        )
        
        if result.success:
            return result
        else:
            raise HTTPException(status_code=400, detail=result.error)
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3306)
