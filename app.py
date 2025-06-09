import streamlit as st
import logging
import json
import time
import os
import shutil
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import threading
from io import StringIO
import sys

# Configure logging
def setup_logger():
    """Set up logger with both file and stream handlers"""
    logger = logging.getLogger('selenium_scraper')
    logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File handler
    log_filename = f"selenium_scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Stream handler for Streamlit
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    
    return logger, log_filename

class StreamlitLogHandler(logging.Handler):
    """Custom log handler to display logs in Streamlit"""
    def __init__(self, log_container):
        super().__init__()
        self.log_container = log_container
        self.logs = []
    
    def emit(self, record):
        log_entry = self.format(record)
        self.logs.append(log_entry)
        # Update the container with latest logs
        with self.log_container.container():
            st.text_area(
                "Live Logs",
                value="\n".join(self.logs[-50:]),  # Show last 50 logs
                height=300,
                disabled=True
            )

class SeleniumJSONScraper:
    def __init__(self, logger):
        self.logger = logger
        self.driver = None
    
    def find_chrome_binary(self):
        """Find Chrome binary location"""
        possible_paths = [
            '/usr/bin/google-chrome',
            '/usr/bin/google-chrome-stable',
            '/usr/bin/chromium-browser',
            '/usr/bin/chromium',
            '/opt/google/chrome/chrome',
            '/usr/local/bin/google-chrome',
            'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
            'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe'
        ]
        
        # Check environment variable first
        env_chrome = os.environ.get('CHROME_BIN')
        if env_chrome and os.path.exists(env_chrome):
            self.logger.info(f"Using Chrome from environment variable: {env_chrome}")
            return env_chrome
        
        # Check common paths
        for path in possible_paths:
            if os.path.exists(path):
                self.logger.info(f"Found Chrome binary at: {path}")
                return path
        
        # Try using which command
        chrome_path = shutil.which('google-chrome') or shutil.which('google-chrome-stable') or shutil.which('chromium')
        if chrome_path:
            self.logger.info(f"Found Chrome using which: {chrome_path}")
            return chrome_path
        
        self.logger.warning("Chrome binary not found in standard locations")
        return None
    
    def find_chromedriver(self):
        """Find ChromeDriver location"""
        # Check environment variable first
        env_driver = os.environ.get('CHROMEDRIVER_PATH')
        if env_driver and os.path.exists(env_driver):
            self.logger.info(f"Using ChromeDriver from environment: {env_driver}")
            return env_driver
        
        # Check common paths
        possible_paths = [
            '/usr/local/bin/chromedriver',
            '/usr/bin/chromedriver',
            '/opt/chromedriver/chromedriver',
            'C:\\chromedriver\\chromedriver.exe'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                self.logger.info(f"Found ChromeDriver at: {path}")
                return path
        
        # Try using which command
        driver_path = shutil.which('chromedriver')
        if driver_path:
            self.logger.info(f"Found ChromeDriver using which: {driver_path}")
            return driver_path
        
        return None
    
    def setup_driver(self, headless=True, timeout=30):
        """Setup Chrome driver with options"""
        self.logger.info("Setting up Chrome driver...")
        
        try:
            # Find Chrome binary
            chrome_binary = self.find_chrome_binary()
            
            chrome_options = Options()
            
            if headless:
                chrome_options.add_argument("--headless=new")  # Use new headless mode
                self.logger.info("Headless mode enabled")
            
            # Essential Chrome options for containerized environments
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument("--disable-features=TranslateUI")
            chrome_options.add_argument("--disable-ipc-flooding-protection")
            chrome_options.add_argument("--disable-default-apps")
            chrome_options.add_argument("--disable-sync")
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--no-default-browser-check")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--ignore-certificate-errors")
            chrome_options.add_argument("--ignore-ssl-errors")
            chrome_options.add_argument("--ignore-certificate-errors-spki-list")
            chrome_options.add_argument("--remote-debugging-port=9222")
            
            # Set Chrome binary location if found
            if chrome_binary:
                chrome_options.binary_location = chrome_binary
            
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Add prefs to disable notifications and other popups
            prefs = {
                "profile.default_content_setting_values": {
                    "notifications": 2,
                    "popups": 2,
                    "geolocation": 2,
                    "media_stream": 2,
                }
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            self.logger.debug(f"Chrome options configured with {len(chrome_options.arguments)} arguments")
            
            # Setup Chrome service
            service = None
            chromedriver_path = self.find_chromedriver()
            
            if chromedriver_path:
                self.logger.info(f"Using ChromeDriver at: {chromedriver_path}")
                service = Service(chromedriver_path)
            else:
                try:
                    self.logger.info("Attempting to install ChromeDriver via ChromeDriverManager...")
                    service = Service(ChromeDriverManager().install())
                    self.logger.info("ChromeDriver installed via ChromeDriverManager")
                except Exception as e:
                    self.logger.warning(f"ChromeDriverManager failed: {e}")
                    # Try system chromedriver as fallback
                    service = Service()
                    self.logger.info("Using system ChromeDriver")
            
            # Initialize driver
            self.logger.info("Initializing Chrome WebDriver...")
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(timeout)
            self.driver.implicitly_wait(10)
            
            # Execute script to hide webdriver property
            try:
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
                self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
            except Exception as e:
                self.logger.warning(f"Could not execute stealth scripts: {e}")
            
            # Test the driver
            try:
                self.driver.get("about:blank")
                self.logger.info("✓ Chrome driver initialized and tested successfully")
                return True
            except Exception as e:
                self.logger.error(f"Driver test failed: {e}")
                return False
            
        except Exception as e:
            self.logger.error(f"✗ Failed to setup Chrome driver: {str(e)}")
            self.logger.error(f"Error details: {type(e).__name__}: {str(e)}")
            
            # Additional debugging info
            try:
                import subprocess
                result = subprocess.run(['google-chrome', '--version'], capture_output=True, text=True, timeout=10)
                self.logger.info(f"Chrome version check: {result.stdout.strip()}")
            except Exception as version_e:
                self.logger.error(f"Could not check Chrome version: {version_e}")
            
            try:
                result = subprocess.run(['chromedriver', '--version'], capture_output=True, text=True, timeout=10)
                self.logger.info(f"ChromeDriver version check: {result.stdout.strip()}")
            except Exception as driver_e:
                self.logger.error(f"Could not check ChromeDriver version: {driver_e}")
            
            return False
    
    def fetch_json_data(self, url, wait_time=2):
        """Fetch JSON data from URL"""
        if not self.driver:
            self.logger.error("Driver not initialized")
            return None, "Driver not initialized"
        
        try:
            self.logger.info(f"Navigating to URL: {url}")
            start_time = time.time()
            
            self.driver.get(url)
            load_time = time.time() - start_time
            self.logger.info(f"✓ Page loaded in {load_time:.2f} seconds")
            
            # Wait for page to stabilize
            self.logger.debug(f"Waiting {wait_time} seconds for page to stabilize...")
            time.sleep(wait_time)
            
            # Get page title and URL for verification
            page_title = self.driver.title
            current_url = self.driver.current_url
            self.logger.info(f"Page title: {page_title}")
            self.logger.info(f"Current URL: {current_url}")
            
            # Try different methods to extract JSON
            json_text = self._extract_json_content()
            
            if not json_text:
                self.logger.warning("No JSON content found")
                return None, "No JSON content found"
            
            # Validate and format JSON
            return self._process_json_content(json_text)
            
        except TimeoutException as e:
            error_msg = f"Timeout loading page: {str(e)}"
            self.logger.error(f"✗ {error_msg}")
            return None, error_msg
            
        except WebDriverException as e:
            error_msg = f"WebDriver error: {str(e)}"
            self.logger.error(f"✗ {error_msg}")
            return None, error_msg
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(f"✗ {error_msg}")
            return None, error_msg
    
    def _extract_json_content(self):
        """Extract JSON content using multiple methods"""
        json_text = None
        
        # Method 1: Try to find <pre> tag
        try:
            self.logger.debug("Attempting to extract JSON from <pre> tag...")
            pre_element = self.driver.find_element(By.TAG_NAME, "pre")
            json_text = pre_element.text
            if json_text and json_text.strip():
                self.logger.info("✓ JSON extracted from <pre> tag")
                return json_text
        except Exception as e:
            self.logger.debug(f"<pre> tag method failed: {str(e)}")
        
        # Method 2: Try to get text from body
        try:
            self.logger.debug("Attempting to extract JSON from <body> tag...")
            body_element = self.driver.find_element(By.TAG_NAME, "body")
            json_text = body_element.text
            if json_text and (json_text.strip().startswith('{') or json_text.strip().startswith('[')):
                self.logger.info("✓ JSON extracted from <body> tag")
                return json_text
        except Exception as e:
            self.logger.debug(f"<body> tag method failed: {str(e)}")
        
        # Method 3: Try specific JSON containers
        try:
            self.logger.debug("Attempting to find JSON in common containers...")
            json_selectors = [
                'script[type="application/json"]',
                'script[type="application/ld+json"]',
                '.json-data',
                '#json-data',
                '[data-json]'
            ]
            
            for selector in json_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    json_text = element.text or element.get_attribute('innerHTML')
                    if json_text and json_text.strip():
                        self.logger.info(f"✓ JSON found in {selector}")
                        return json_text
                except:
                    continue
                    
        except Exception as e:
            self.logger.debug(f"JSON container method failed: {str(e)}")
        
        # Method 4: Use page source as fallback
        try:
            self.logger.debug("Attempting to extract JSON from page source...")
            page_source = self.driver.page_source
            
            # Try to find JSON in page source
            import re
            
            # Look for JSON in <pre> tags
            json_match = re.search(r'<pre[^>]*>(.*?)</pre>', page_source, re.DOTALL | re.IGNORECASE)
            if json_match:
                json_text = json_match.group(1).strip()
                if json_text:
                    self.logger.info("✓ JSON extracted from page source <pre> tags")
                    return json_text
            
            # Look for JSON-like patterns in the entire page
            json_patterns = [
                r'(\{[^<>]*\})',  # Simple object
                r'(\[[^<>]*\])',  # Simple array
                r'(\{.*?\})',     # More complex object
                r'(\[.*?\])'      # More complex array
            ]
            
            for pattern in json_patterns:
                json_match = re.search(pattern, page_source, re.DOTALL)
                if json_match:
                    potential_json = json_match.group(1).strip()
                    # Basic validation
                    if len(potential_json) > 10 and (potential_json.startswith('{') or potential_json.startswith('[')):
                        self.logger.info("✓ JSON pattern found in page source")
                        return potential_json
                
        except Exception as e:
            self.logger.debug(f"Page source method failed: {str(e)}")
        
        self.logger.warning("All JSON extraction methods failed")
        return None
    
    def _process_json_content(self, json_text):
        """Process and validate JSON content"""
        try:
            self.logger.debug(f"Processing JSON content ({len(json_text)} characters)...")
            
            # Clean up the JSON text
            json_text = json_text.strip()
            
            # Try to parse as JSON
            json_data = json.loads(json_text)
            formatted_json = json.dumps(json_data, indent=2, ensure_ascii=False)
            
            self.logger.info("✓ Valid JSON data processed")
            self.logger.debug(f"JSON structure: {type(json_data)}")
            
            if isinstance(json_data, dict):
                self.logger.debug(f"JSON object with {len(json_data)} keys")
            elif isinstance(json_data, list):
                self.logger.debug(f"JSON array with {len(json_data)} items")
            
            return formatted_json, None
            
        except json.JSONDecodeError as e:
            self.logger.warning(f"Invalid JSON format: {str(e)}")
            self.logger.info("Saving content as raw text")
            return json_text, f"Invalid JSON format: {str(e)}"
        except Exception as e:
            self.logger.error(f"Error processing JSON: {str(e)}")
            return json_text, f"Error processing content: {str(e)}"
    
    def save_to_file(self, content, filename):
        """Save content to file"""
        try:
            self.logger.info(f"Saving content to file: {filename}")
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            file_size = os.path.getsize(filename)
            self.logger.info(f"✓ File saved successfully ({file_size} bytes)")
            return True, None
            
        except Exception as e:
            error_msg = f"Failed to save file: {str(e)}"
            self.logger.error(f"✗ {error_msg}")
            return False, error_msg
    
    def close_driver(self):
        """Close the browser driver"""
        if self.driver:
            try:
                self.logger.info("Closing browser...")
                self.driver.quit()
                self.driver = None
                self.logger.info("✓ Browser closed successfully")
            except Exception as e:
                self.logger.error(f"Error closing browser: {str(e)}")

def main():
    st.set_page_config(
        page_title="Selenium JSON Scraper",
        page_icon="🕷️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🕷️ Selenium JSON Scraper with Logger")
    st.markdown("---")
    
    # Initialize session state
    if 'scraper' not in st.session_state:
        st.session_state.scraper = None
    if 'logger' not in st.session_state:
        st.session_state.logger = None
    if 'log_filename' not in st.session_state:
        st.session_state.log_filename = None
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Logger setup
        if st.button("🔧 Initialize Logger"):
            logger, log_filename = setup_logger()
            st.session_state.logger = logger
            st.session_state.log_filename = log_filename
            st.success(f"Logger initialized: {log_filename}")
        
        if st.session_state.logger:
            st.success("✅ Logger Ready")
            st.info(f"Log file: {st.session_state.log_filename}")
        
        st.markdown("---")
        
        # System info section
        with st.expander("🔍 System Check"):
            # Check Chrome
            chrome_status = "❌ Not Found"
            try:
                import subprocess
                result = subprocess.run(['google-chrome', '--version'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    chrome_status = f"✅ {result.stdout.strip()}"
            except:
                pass
            st.write(f"**Chrome:** {chrome_status}")
            
            # Check ChromeDriver
            driver_status = "❌ Not Found"
            try:
                result = subprocess.run(['chromedriver', '--version'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    driver_status = f"✅ {result.stdout.strip()}"
            except:
                pass
            st.write(f"**ChromeDriver:** {driver_status}")
        
        # Browser settings
        st.subheader("🌐 Browser Settings")
        headless_mode = st.checkbox("Headless Mode", value=True)
        page_timeout = st.slider("Page Load Timeout (seconds)", 10, 60, 30)
        wait_time = st.slider("Wait Time After Load (seconds)", 1, 10, 2)
        
        # Advanced settings
        with st.expander("Advanced Settings"):
            disable_js = st.checkbox("Disable JavaScript", value=False, help="Disable JS for faster loading")
            disable_images = st.checkbox("Disable Images", value=True, help="Disable images for faster loading")
    
    # Main interface
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📝 Input")
        
        # URL input
        url = st.text_input(
            "🔗 Enter URL to scrape:",
            placeholder="https://jsonplaceholder.typicode.com/posts/1",
            help="Enter the URL that returns JSON data"
        )
        
        # Output filename
        output_filename = st.text_input(
            "📄 Output filename:",
            value="scraped_data.txt",
            help="Name of the file to save JSON data"
        )
        
        # Action buttons
        col1_1, col1_2 = st.columns([1, 1])
        
        with col1_1:
            if st.button("🚀 Start Scraping", type="primary"):
                if not st.session_state.logger:
                    st.error("Please initialize logger first!")
                elif not url:
                    st.error("Please enter a URL!")
                else:
                    # Initialize scraper
                    st.session_state.scraper = SeleniumJSONScraper(st.session_state.logger)
                    
                    with st.spinner("Scraping in progress..."):
                        # Setup driver
                        if st.session_state.scraper.setup_driver(headless_mode, page_timeout):
                            # Fetch data
                            content, error = st.session_state.scraper.fetch_json_data(url, wait_time)
                            
                            if content:
                                # Save to file
                                success, save_error = st.session_state.scraper.save_to_file(content, output_filename)
                                
                                if success:
                                    st.success("✅ Scraping completed successfully!")
                                    
                                    # Show download button
                                    with open(output_filename, 'r', encoding='utf-8') as f:
                                        file_content = f.read()
                                    
                                    st.download_button(
                                        label="📥 Download Scraped Data",
                                        data=file_content,
                                        file_name=output_filename,
                                        mime="text/plain"
                                    )
                                    
                                    # Show preview
                                    with st.expander("📄 Data Preview"):
                                        st.text_area("Content Preview", value=file_content[:1000] + "..." if len(file_content) > 1000 else file_content, height=200)
                                else:
                                    st.error(f"Failed to save file: {save_error}")
                            else:
                                st.error(f"Failed to fetch data: {error}")
                            
                            # Close driver
                            st.session_state.scraper.close_driver()
                        else:
                            st.error("Failed to initialize browser driver!")
        
        with col1_2:
            if st.button("🗑️ Clear Logs"):
                if st.session_state.logger:
                    # Clear log handlers
                    for handler in st.session_state.logger.handlers:
                        handler.close()
                    st.session_state.logger = None
                    st.session_state.log_filename = None
                    st.success("Logs cleared!")
    
    with col2:
        st.header("📊 Live Logs")
        
        # Log display area
        if st.session_state.logger and st.session_state.log_filename:
            # Try to read and display current log file
            try:
                if os.path.exists(st.session_state.log_filename):
                    with open(st.session_state.log_filename, 'r', encoding='utf-8') as f:
                        log_content = f.read()
                    
                    st.text_area(
                        "Current Log Content",
                        value=log_content,
                        height=400,
                        disabled=True
                    )
                    
                    # Auto-refresh logs
                    if st.button("🔄 Refresh Logs"):
                        st.rerun()
                else:
                    st.info("Log file will appear here when scraping starts...")
            except Exception as e:
                st.error(f"Error reading log file: {str(e)}")
        else:
            st.info("Initialize logger to see live logs here...")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        **📌 Instructions:**
        1. Check system status in the sidebar to ensure Chrome is installed
        2. Initialize the logger first
        3. Enter a URL that returns JSON data
        4. Configure browser settings in the sidebar
        5. Click 'Start Scraping' to begin
        6. Monitor progress in the live logs
        7. Download the scraped data when complete
        
        **🔧 Common Issues:**
        - If Chrome driver fails, ensure Google Chrome is installed
        - For timeout issues, increase the page load timeout
        - For JavaScript-heavy sites, disable "Disable JavaScript" option
        - Check system status in sidebar for Chrome/ChromeDriver availability
        """
    )
    
    # System info
    with st.expander("ℹ️ System Information"):
        st.write(f"**Python Version:** {sys.version}")
        st.write(f"**Current Working Directory:** {os.getcwd()}")
        
        # Environment variables
        chrome_bin = os.environ.get('CHROME_BIN', 'Not set')
        chromedriver_path = os.environ.get('CHROMEDRIVER_PATH', 'Not set')
        st.write(f"**CHROME_BIN:** {chrome_bin}")
        st.write(f"**CHROMEDRIVER_PATH:** {chromedriver_path}")
        
        try:
            st.write(f"**Available Files:** {os.listdir('.')}")
        except:
            st.write("**Available Files:** Unable to list directory")

if __name__ == "__main__":
    main()