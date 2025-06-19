
#!/usr/bin/env python3
"""
Selenium-based hierarchical web scraper for egramswaraj.gov.in
Modified to capture HTML data without clicking export buttons
Navigation: Base URL → XPath1 → XPath2 → XPath3 → New Tab → Hierarchical Scraping
"""

import json
import csv
import time
import logging
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class VoucherDetail:
    """Structure for voucher detail data"""
    voucher_id: str = ""
    state: str = ""
    district: str = ""
    block: str = ""
    village: str = ""
    month: str = ""
    amount: Optional[str] = None
    date: Optional[str] = None
    description: Optional[str] = None
    beneficiary: Optional[str] = None
    scheme: Optional[str] = None
    status: Optional[str] = None
    url: Optional[str] = None

@dataclass
class HierarchyNode:
    """Structure for hierarchy node data"""
    id: str
    name: str
    url: str
    level: str  # 'state', 'district', 'block', 'village'
    parent_id: Optional[str] = None
    parent_name: Optional[str] = None
    html_content: Optional[str] = None  # Store HTML content

class EgramSwarajScraper:
    """Main scraper class for egramswaraj.gov.in with HTML data capture"""
    
    def __init__(self, headless=True, delay=2, target_state: Optional[str] = None):
        self.base_url = "https://egramswaraj.gov.in"
        self.delay = delay
        self.target_state = target_state
        self.scraped_data = []
        self.hierarchy_data = []
        self.failed_urls = []
        self.html_snapshots = []  # Store HTML snapshots
        
        # XPath selectors for navigation
        self.first_xpath = "/html/body/div[1]/div/div[3]/div/div/div/section[5]/div[2]/div/a[4]"
        self.second_xpath = "/html/body/form/section/div/div/div/div/div[1]/div[1]/div[1]/a"
        self.third_xpath = "/html/body/form/section/div/div/div/div/div[1]/div[1]/div[2]/div/div/div[1]/div[1]/a"
        self.fourth_xpath = "/html/body/form/section/div/div/div/div/div[1]/div[1]/div[2]/div/div/div[1]/div[2]/div/ul/li[1]/a"
        
        # Patterns to avoid clicking (export buttons, download links, etc.)
        self.avoid_click_patterns = [
            'export', 'excel', 'download', 'pdf', 'csv', 'xls', 'xlsx',
            'Export to Excel', 'Download', 'Export', 'Print', 'Save'
        ]
        
        # Initialize Chrome driver
        self.driver = self._setup_driver(headless)
        self.wait = WebDriverWait(self.driver, 15)
        
    def _setup_driver(self, headless=True):
        """Setup Chrome WebDriver with proper driver management"""
        options = Options()
        
        # Basic Chrome options
        if headless:
            options.add_argument('--headless=new')
        
        # Security and stability options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        
        # Window and display options
        options.add_argument('--window-size=800,600')
        options.add_argument('--start-maximized')
        
        # User agent to avoid detection
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        options.add_argument(f'--user-agent={user_agent}')
        
        # Bypass bot detection
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            # Execute script to hide automation indicators
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": user_agent
            })
            
            logger.info("Chrome driver setup successfully")
            return driver
            
        except Exception as e:
            logger.error(f"Failed to setup Chrome driver: {str(e)}")
            raise Exception("Could not initialize Chrome driver. Please ensure Chrome and ChromeDriver are installed.")
    
    def should_avoid_clicking(self, element_text: str, element_href: str = "") -> bool:
        """Check if element should be avoided for clicking (export buttons, etc.)"""
        text_lower = element_text.lower()
        href_lower = element_href.lower()
        
        for pattern in self.avoid_click_patterns:
            if pattern.lower() in text_lower or pattern.lower() in href_lower:
                logger.info(f"Avoiding click on element: {element_text} (matches pattern: {pattern})")
                return True
        return False
    
    def safe_click_and_wait(self, xpath: str, description: str, timeout=15) -> bool:
        """Safely click element by XPath and wait for page load"""
        try:
            logger.info(f"Attempting to click: {description}")
            logger.info(f"XPath: {xpath}")
            
            # Wait for element to be clickable
            element = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            
            # Check if we should avoid clicking this element
            element_text = element.text.strip()
            element_href = element.get_attribute("href") or ""
            
            if self.should_avoid_clicking(element_text, element_href):
                logger.warning(f"Skipping click on: {element_text} (export/download button)")
                return False
            
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(1)
            
            # Try regular click first
            try:
                element.click()
            except Exception:
                # If regular click fails, try JavaScript click
                self.driver.execute_script("arguments[0].click();", element)
            
            logger.info(f"Successfully clicked: {description}")
            time.sleep(self.delay)
            return True
            
        except TimeoutException:
            logger.error(f"Timeout waiting for element: {description}")
            return False
        except Exception as e:
            logger.error(f"Error clicking element {description}: {str(e)}")
            return False
    
    def capture_page_html(self, page_info: Dict) -> Dict:
        """Capture and parse HTML content from current page"""
        try:
            # Get page source
            html_content = self.driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Create HTML snapshot record
            html_snapshot = {
                'url': self.driver.current_url,
                'page_title': self.driver.title,
                'level': page_info.get('level', ''),
                'parent_id': page_info.get('id', ''),
                'parent_name': page_info.get('name', ''),
                'html_content': html_content,
                'text_content': soup.get_text(strip=True, separator=' '),
                'captured_at': datetime.now().isoformat(),
                'page_size': len(html_content)
            }
            
            self.html_snapshots.append(html_snapshot)
            
            logger.info(f"Captured HTML content: {len(html_content)} characters from {self.driver.current_url}")
            
            return html_snapshot
            
        except Exception as e:
            logger.error(f"Error capturing HTML content: {str(e)}")
            return {}
    
    def handle_new_tab(self) -> bool:
        """Handle switching to new tab if opened"""
        try:
            # Wait a bit for potential new tab to open
            time.sleep(2)
            
            # Check if new tab was opened
            if len(self.driver.window_handles) > 1:
                logger.info(f"New tab detected ({len(self.driver.window_handles)} tabs total), switching to new tab")
                self.driver.switch_to.window(self.driver.window_handles[-1])
                time.sleep(self.delay)
                logger.info(f"Switched to new tab. Current URL: {self.driver.current_url}")
                return True
            else:
                logger.info("No new tab opened, continuing on current page")
                return True
        except Exception as e:
            logger.error(f"Error handling new tab: {str(e)}")
            return False
    
    def navigate_to_scraping_page(self, start_url: str) -> bool:
        """Navigate through the specified path to reach scraping page"""
        try:
            # Step 1: Navigate to base URL
            logger.info(f"Step 1: Navigating to base URL: {start_url}")
            self.driver.get(start_url)
            time.sleep(self.delay * 2)
            
            # Step 2: Click first XPath element
            if not self.safe_click_and_wait(self.first_xpath, "First navigation element"):
                logger.error("Failed to click first navigation element")
                return False
            
            # Step 3: Click second XPath element
            if not self.safe_click_and_wait(self.second_xpath, "Second navigation element"):
                logger.error("Failed to click second navigation element")
                return False
            
            # Step 4: Click third XPath element 
            if not self.safe_click_and_wait(self.third_xpath, "Third navigation element"):
                logger.error("Failed to click third navigation element")
                return False
            
            # Step 5: Click fourth XPath element (the final one before new tab)
            if not self.safe_click_and_wait(self.fourth_xpath, "Fourth navigation element"):
                logger.error("Failed to click fourth navigation element")
                return False
            
            # Step 6: Handle potential new tab
            if not self.handle_new_tab():
                logger.error("Failed to handle new tab")
                return False
            
            logger.info("Successfully navigated to scraping page")
            logger.info(f"Current URL: {self.driver.current_url}")
            return True
            
        except Exception as e:
            logger.error(f"Error during navigation: {str(e)}")
            return False
    
    def extract_hierarchy_links(self, level_name: str, parent_info: Dict = None) -> List[Dict[str, str]]:
        """Extract links for current hierarchy level, avoiding export buttons"""
        links = []
        try:
            logger.info(f"Extracting {level_name} level links")
            
            # Common patterns for different hierarchy levels
            link_selectors = [
                "a[href*='state']",
                "a[href*='district']", 
                "a[href*='block']",
                "a[href*='village']",
                "a[href*='FileRedirect']",
                "a[href*='report']",
                "//table//a",
                "//div//a[contains(@href, '.html')]",
                "//a[not(contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'export')) and not(contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'excel')) and not(contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'download'))]"
            ]
            
            found_links = []
            
            # Try multiple selectors to find links
            for selector in link_selectors:
                try:
                    if selector.startswith("//"):
                        # XPath selector
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        # CSS selector
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        href = element.get_attribute("href")
                        text = element.text.strip()
                        
                        if href and text and len(text) > 0:
                            # Skip export/download buttons
                            if self.should_avoid_clicking(text, href):
                                continue
                                
                            # Extract ID from various URL patterns
                            link_id = self._extract_id_from_url(href)
                            
                            link_data = {
                                'id': link_id or text,
                                'name': text,
                                'url': href,
                                'level': level_name
                            }
                            
                            if parent_info:
                                link_data['parent_id'] = parent_info.get('id', '')
                                link_data['parent_name'] = parent_info.get('name', '')
                            
                            found_links.append(link_data)
                    
                    if found_links:
                        break
                        
                except Exception as e:
                    continue
            
            # Remove duplicates based on URL
            seen_urls = set()
            for link in found_links:
                if link['url'] not in seen_urls:
                    links.append(link)
                    seen_urls.add(link['url'])
            
            logger.info(f"Found {len(links)} unique {level_name} links (excluding export buttons)")
            
        except Exception as e:
            logger.error(f"Error extracting {level_name} links: {str(e)}")
        
        return links
    
    def _extract_id_from_url(self, url: str) -> str:
        """Extract ID from URL using various patterns"""
        patterns = [
            r'/(\d+)&name=\d+\.html',
            r'state=(\d+)',
            r'district=(\d+)', 
            r'block=(\d+)',
            r'village=(\d+)',
            r'voucherID=(\d+)',
            r'/(\d+)\.html',
            r'=(\d+)&',
            r'=(\d+)$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return ""
    
    def scrape_current_page_data(self, level_info: Dict) -> List[Dict]:
        """Scrape data from current page including HTML capture"""
        scraped_items = []
        
        try:
            # First, capture HTML content
            html_snapshot = self.capture_page_html(level_info)
            
            # Look for tables with data
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            
            for table_idx, table in enumerate(tables):
                try:
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    
                    if len(rows) > 1:  # Has header + data
                        # Get headers
                        header_row = rows[0]
                        headers = [th.text.strip() for th in header_row.find_elements(By.TAG_NAME, "th")]
                        
                        if not headers:
                            headers = [td.text.strip() for td in header_row.find_elements(By.TAG_NAME, "td")]
                        
                        # Process data rows
                        for row_idx, row in enumerate(rows[1:], 1):
                            cells = row.find_elements(By.TAG_NAME, "td")
                            
                            if cells:
                                row_data = {
                                    'table_index': table_idx,
                                    'row_index': row_idx,
                                    'level': level_info.get('level', ''),
                                    'parent_id': level_info.get('id', ''),
                                    'parent_name': level_info.get('name', ''),
                                    'url': self.driver.current_url,
                                    'page_title': self.driver.title,
                                    'scraped_at': datetime.now().isoformat()
                                }
                                
                                # Map cell data to headers or generic columns
                                for i, cell in enumerate(cells):
                                    cell_text = cell.text.strip()
                                    
                                    if i < len(headers) and headers[i]:
                                        row_data[headers[i]] = cell_text
                                    else:
                                        row_data[f'column_{i}'] = cell_text
                                
                                scraped_items.append(row_data)
                                
                except Exception as e:
                    logger.warning(f"Error processing table {table_idx}: {str(e)}")
                    continue
            
            # Also look for other data patterns (lists, divs, etc.)
            self._scrape_additional_data_patterns(level_info, scraped_items)
            
        except Exception as e:
            logger.error(f"Error scraping current page data: {str(e)}")
        
        return scraped_items
    
    def _scrape_additional_data_patterns(self, level_info: Dict, scraped_items: List[Dict]):
        """Scrape additional data patterns beyond tables"""
        try:
            # Look for definition lists
            dl_elements = self.driver.find_elements(By.TAG_NAME, "dl")
            for dl in dl_elements:
                try:
                    dt_elements = dl.find_elements(By.TAG_NAME, "dt")
                    dd_elements = dl.find_elements(By.TAG_NAME, "dd")
                    
                    if len(dt_elements) == len(dd_elements):
                        dl_data = {
                            'data_type': 'definition_list',
                            'level': level_info.get('level', ''),
                            'parent_id': level_info.get('id', ''),
                            'url': self.driver.current_url,
                            'scraped_at': datetime.now().isoformat()
                        }
                        
                        for dt, dd in zip(dt_elements, dd_elements):
                            key = dt.text.strip().replace(':', '').replace(' ', '_').lower()
                            if key:
                                dl_data[key] = dd.text.strip()
                        
                        scraped_items.append(dl_data)
                except Exception:
                    continue
            
            # Look for structured divs with data
            data_divs = self.driver.find_elements(By.CSS_SELECTOR, "div[class*='data'], div[class*='info'], div[class*='content']")
            for div in data_divs:
                try:
                    text_content = div.text.strip()
                    if len(text_content) > 20:  # Only capture meaningful content
                        div_data = {
                            'data_type': 'content_div',
                            'level': level_info.get('level', ''),
                            'parent_id': level_info.get('id', ''),
                            'content': text_content,
                            'url': self.driver.current_url,
                            'scraped_at': datetime.now().isoformat()
                        }
                        scraped_items.append(div_data)
                except Exception:
                    continue
                    
        except Exception as e:
            logger.warning(f"Error scraping additional data patterns: {str(e)}")
    
    def scrape_hierarchically(self, current_level_info: Dict, max_depth: int = 6, current_depth: int = 0) -> None:
        """Recursively scrape data following hierarchy"""
        
        if current_depth >= max_depth:
            logger.info(f"Maximum depth {max_depth} reached")
            return
        
        try:
            logger.info(f"Scraping level {current_depth}: {current_level_info.get('name', 'Unknown')}")
            
            # Navigate to current level URL if provided
            if current_level_info.get('url'):
                logger.info(f"Navigating to: {current_level_info['url']}")
                self.driver.get(current_level_info['url'])
                time.sleep(self.delay)
            
            # Scrape data from current page (includes HTML capture)
            page_data = self.scrape_current_page_data(current_level_info)
            self.scraped_data.extend(page_data)
            
            # Add current level to hierarchy
            self.hierarchy_data.append(HierarchyNode(
                id=current_level_info.get('id', ''),
                name=current_level_info.get('name', ''),
                url=current_level_info.get('url', ''),
                level=current_level_info.get('level', f'level_{current_depth}'),
                parent_id=current_level_info.get('parent_id'),
                parent_name=current_level_info.get('parent_name'),
                html_content=self.driver.page_source if current_depth < 3 else None  # Limit HTML storage
            ))
            
            # Extract next level links (avoiding export buttons)
            next_level_name = self._get_next_level_name(current_level_info.get('level', ''), current_depth)
            child_links = self.extract_hierarchy_links(next_level_name, current_level_info)

            # === MODIFICATION START: Filter for a specific state ===
            # If a target state is specified and we are at the state selection level (depth 0)
            if self.target_state and current_depth == 0:
                filtered_links = [
                    link for link in child_links
                    if self.target_state.upper() in link.get('name', '').upper()
                ]

                if not filtered_links:
                    logger.warning(f"Target state '{self.target_state}' not found in the list of states. Halting scrape.")
                    child_links = []  # Empty the list to stop recursion
                else:
                    logger.info(f"Found target state: '{self.target_state}'. Focusing scrape on this state only.")
                    child_links = filtered_links  # Proceed only with the target state
            # === MODIFICATION END ===

            logger.info(f"Found {len(child_links)} child links for next level to process.")
            
            # Recursively scrape child levels
            for i, child_link in enumerate(child_links):
                logger.info(f"Processing child {i+1}/{len(child_links)}: {child_link.get('name', 'Unknown')}")
                self.scrape_hierarchically(child_link, max_depth, current_depth + 1)
                
        except Exception as e:
            logger.error(f"Error in hierarchical scraping at depth {current_depth}: {str(e)}")
            self.failed_urls.append(current_level_info.get('url', ''))
    
    def _get_next_level_name(self, current_level: str, current_depth: int) -> str:
        """Get the name for the next hierarchy level"""
        level_names = ['state', 'district', 'block', 'village', 'voucher', 'detail']
        
        if current_depth + 1 < len(level_names):
            return level_names[current_depth + 1]
        else:
            return f'level_{current_depth + 1}'
    
    def run_complete_scraping(self, start_url: str, max_depth: int = 6, max_items_per_level: int = None):
        """Run the complete scraping process"""
        logger.info("Starting complete scraping process with HTML capture")
        
        try:
            # Step 1: Navigate to the scraping page
            if not self.navigate_to_scraping_page(start_url):
                logger.error("Failed to navigate to scraping page")
                return
            
            # Step 2: Extract initial hierarchy level
            initial_level_info = {
                'id': 'root',
                'name': 'Root Level',
                'url': self.driver.current_url,
                'level': 'root'
            }
            
            # Step 3: Start hierarchical scraping
            self.scrape_hierarchically(initial_level_info, max_depth, 0)
            
            logger.info("Complete scraping process finished")
            
        except KeyboardInterrupt:
            logger.info("Scraping interrupted by user")
        except Exception as e:
            logger.error(f"Error in complete scraping: {str(e)}")
        finally:
            logger.info(f"Scraping completed. Total records: {len(self.scraped_data)}, HTML snapshots: {len(self.html_snapshots)}")
    
    def save_data(self, filename_prefix="egramswaraj_hierarchical"):
        """Save scraped data to multiple formats with emphasis on CSV and HTML capture"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # PRIORITY: Save scraped data as CSV first
            if self.scraped_data:
                csv_filename = f"{filename_prefix}_data_{timestamp}.csv"
                df = pd.DataFrame(self.scraped_data)
                df.to_csv(csv_filename, index=False, encoding='utf-8')
                logger.info(f"✅ PRIMARY: Scraped data saved to CSV: {csv_filename}")
                print(f"✅ PRIMARY OUTPUT: {csv_filename}")
            else:
                logger.warning("No scraped data available to save to CSV")
            
            # Save HTML snapshots as separate CSV
            if self.html_snapshots:
                html_csv_filename = f"{filename_prefix}_html_snapshots_{timestamp}.csv"
                html_df = pd.DataFrame(self.html_snapshots)
                # Limit HTML content in CSV to first 10000 characters to avoid huge files
                html_df['html_content_preview'] = html_df['html_content'].str[:10000]
                html_df['text_content_preview'] = html_df['text_content'].str[:5000]
                # Save without full HTML content for CSV
                html_df_small = html_df.drop(['html_content'], axis=1)
                html_df_small.to_csv(html_csv_filename, index=False, encoding='utf-8')
                logger.info(f"✅ HTML snapshots saved to CSV: {html_csv_filename}")
                print(f"✅ HTML SNAPSHOTS: {html_csv_filename}")
            
            # Save hierarchy as separate CSV
            if self.hierarchy_data:
                hierarchy_filename = f"{filename_prefix}_hierarchy_{timestamp}.csv"
                hierarchy_df = pd.DataFrame([asdict(node) for node in self.hierarchy_data])
                # Remove HTML content from hierarchy CSV to keep it clean
                if 'html_content' in hierarchy_df.columns:
                    hierarchy_df = hierarchy_df.drop(['html_content'], axis=1)
                hierarchy_df.to_csv(hierarchy_filename, index=False, encoding='utf-8')
                logger.info(f"✅ Hierarchy data saved to CSV: {hierarchy_filename}")
                print(f"✅ HIERARCHY OUTPUT: {hierarchy_filename}")
            
            # Save complete HTML snapshots as JSON (with full HTML content)
            if self.html_snapshots:
                html_json_filename = f"{filename_prefix}_html_complete_{timestamp}.json"
                with open(html_json_filename, 'w', encoding='utf-8') as f:
                    json.dump(self.html_snapshots, f, indent=2, ensure_ascii=False)
                logger.info(f"✅ Complete HTML data saved to JSON: {html_json_filename}")
                print(f"✅ COMPLETE HTML JSON: {html_json_filename}")
            
            # Save as JSON (backup format)
            json_filename = f"{filename_prefix}_{timestamp}.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'scraped_data': self.scraped_data,
                    'hierarchy_data': [asdict(node) for node in self.hierarchy_data],
                    'html_snapshots_summary': [
                        {k: v for k, v in snapshot.items() if k != 'html_content'} 
                        for snapshot in self.html_snapshots
                    ],
                    'failed_urls': self.failed_urls,
                    'scraping_metadata': {
                        'timestamp': timestamp,
                        'total_records': len(self.scraped_data),
                        'total_hierarchy_nodes': len(self.hierarchy_data),
                        'total_html_snapshots': len(self.html_snapshots),
                        'failed_urls_count': len(self.failed_urls)
                    }
                }, f, indent=2, ensure_ascii=False)
            
            logger.info(f"JSON backup saved to {json_filename}")
            
            # Save failed URLs
            if self.failed_urls:
                failed_filename = f"{filename_prefix}_failed_{timestamp}.txt"
                with open(failed_filename, 'w') as f:
                    for url in self.failed_urls:
                        f.write(f"{url}\n")
                logger.info(f"Failed URLs saved to {failed_filename}")
            
            # Print summary
            print(f"\n📊 SCRAPING SUMMARY")
            print(f"=" * 50)
            print(f"Total records scraped: {len(self.scraped_data)}")
            print(f"Total hierarchy nodes: {len(self.hierarchy_data)}")
            print(f"Total HTML snapshots: {len(self.html_snapshots)}")
            print(f"Failed URLs: {len(self.failed_urls)}")
            print(f"Files saved with timestamp: {timestamp}")
            print(f"🎯 MAIN CSV OUTPUT: {csv_filename if self.scraped_data else 'No data to save'}")
            print(f"🌐 HTML SNAPSHOTS: {html_csv_filename if self.html_snapshots else 'No HTML data'}")
            
        except Exception as e:
            logger.error(f"Error saving data: {str(e)}")
            print(f"❌ Error saving data: {str(e)}")
    
    def close(self):

        """Close the browser driver"""
        try:
            if self.driver:
                self.driver.quit()
                logger.info("Browser driver closed")
        except Exception as e:
            logger.warning(f"Error closing browser: {str(e)}")

def main():
    """Main execution function"""
    # Configuration
    START_URL = "https://egramswaraj.gov.in"
    TARGET_STATE = "MAHARASHTRA"  # Set to a specific state name or None to scrape all states
    
    print("🚀 Starting EgramSwaraj Hierarchical Web Scraper")
    if TARGET_STATE:
        print(f"🎯 Target State: {TARGET_STATE}")
    print("📍 Navigation Path: Base URL → XPath1 → XPath2 → XPath3 → XPath4 → New Tab → Hierarchical Scraping")
    print("=" * 80)
    
    scraper = None
    try:
        print("📦 Initializing Chrome driver...")
        scraper = EgramSwarajScraper(
            headless=False, 
            delay=3, 
            target_state=TARGET_STATE
        )  # Set headless=True to hide browser
        print("✅ Chrome driver initialized successfully!")
        
        print("\n🔍 Starting navigation and hierarchical scraping...")
        
        # Run the complete scraping process
        scraper.run_complete_scraping(
            START_URL,
            max_depth=6,  # Adjust based on hierarchy depth needed
            max_items_per_level=None  # Set to limit items per level for testing
        )
        
        print("\n💾 Saving scraped data...")
        scraper.save_data()
        print("✅ Data saved successfully!")
        
    except Exception as e:
        print(f"❌ Error in main execution: {str(e)}")
        logger.error(f"Error in main execution: {str(e)}")
    finally:
        print("\n🔒 Closing browser...")
        if scraper:
            scraper.close()
        print("✅ Browser closed successfully!")
        print("\n🎉 Scraping process completed!")

# Installation and usage instructions
INSTRUCTIONS = """
📋 INSTALLATION REQUIREMENTS:
pip install selenium webdriver-manager pandas beautifulsoup4

🔧 SETUP INSTRUCTIONS:
1. Install Google Chrome browser
2. Install required Python packages:
   pip install selenium webdriver-manager pandas beautifulsoup4
3. Modify TARGET_STATE in main() function to your desired state, or set to None for all states.
4. Run: python app.py

⚙️ CONFIGURATION OPTIONS:
- TARGET_STATE="MAHARASHTRA" (Target a specific state)
- headless=True/False (show/hide browser)
- delay=3 (seconds between requests)
- max_depth=6 (maximum hierarchy depth)
- max_items_per_level=None (limit items per level for testing)

🗂️ OUTPUT FILES:
- {prefix}_data_{timestamp}.csv - Scraped data
- {prefix}_hierarchy_{timestamp}.csv - Hierarchy structure  
- {prefix}_{timestamp}.json - Complete data in JSON format
- {prefix}_failed_{timestamp}.txt - Failed URLs

📊 NAVIGATION PATH:
1. Navigate to base URL
2. Click element: /html/body/div[1]/div/div[3]/div/div/div/section[5]/div[2]/div/a[4]
3. Click element: /html/body/form/section/div/div/div/div/div[1]/div[1]/div[1]/a
4. Click element: /html/body/form/section/div/div/div/div/div[1]/div[1]/div[2]/div/div/div[1]/div[1]/a
5. Click element: /html/body/form/section/div/div/div/div/div[1]/div[1]/div[2]/div/div/div[1]/div[2]/div/ul/li[1]/a
6. Switch to new tab if opened
7. Start hierarchical scraping from current page (filtered for TARGET_STATE if specified)

🔍 HIERARCHY LEVELS:
- Level 0: Root/Initial page
- Level 1: States
- Level 2: Districts  
- Level 3: Blocks
- Level 4: Villages
- Level 5: Vouchers
- Level 6: Voucher Details
"""

if __name__ == "__main__":
    print(INSTRUCTIONS)
    print("\n" + "="*80)
    main()
