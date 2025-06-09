import streamlit as st
import logging
import json
import time
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
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
    
    def setup_driver(self, headless=True, timeout=30):
        """Setup Chrome driver with options"""
        self.logger.info("Setting up Chrome driver...")
        
        try:
            chrome_options = Options()
            
            if headless:
                chrome_options.add_argument("--headless")
                self.logger.info("Headless mode enabled")
            
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.binary_location = '/usr/bin/google-chrome'
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            self.logger.debug(f"Chrome options configured: {chrome_options.arguments}")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(timeout)
            self.driver.implicitly_wait(10)
            
            self.logger.info("✓ Chrome driver initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"✗ Failed to setup Chrome driver: {str(e)}")
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
        
        # Method 3: Use page source
        try:
            self.logger.debug("Attempting to extract JSON from page source...")
            page_source = self.driver.page_source
            
            # Try to find JSON in page source
            import re
            json_match = re.search(r'<pre[^>]*>(.*?)</pre>', page_source, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
                self.logger.info("✓ JSON extracted from page source <pre> tags")
                return json_text
            
            # Look for JSON-like patterns
            json_match = re.search(r'(\{.*\}|\[.*\])', page_source, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
                self.logger.info("✓ JSON pattern found in page source")
                return json_text
                
        except Exception as e:
            self.logger.debug(f"Page source method failed: {str(e)}")
        
        self.logger.warning("All JSON extraction methods failed")
        return None
    
    def _process_json_content(self, json_text):
        """Process and validate JSON content"""
        try:
            self.logger.debug(f"Processing JSON content ({len(json_text)} characters)...")
            
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
        
        # Browser settings
        st.subheader("🌐 Browser Settings")
        headless_mode = st.checkbox("Headless Mode", value=True)
        page_timeout = st.slider("Page Load Timeout (seconds)", 10, 60, 30)
        wait_time = st.slider("Wait Time After Load (seconds)", 1, 10, 2)
    
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
        log_container = st.empty()
        
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
        1. Initialize the logger first
        2. Enter a URL that returns JSON data
        3. Configure browser settings in the sidebar
        4. Click 'Start Scraping' to begin
        5. Monitor progress in the live logs
        6. Download the scraped data when complete
        """
    )
    
    # System info
    with st.expander("ℹ️ System Information"):
        st.write(f"**Python Version:** {sys.version}")
        st.write(f"**Current Working Directory:** {os.getcwd()}")
        st.write(f"**Available Files:** {os.listdir('.')}")

if __name__ == "__main__":
    main()