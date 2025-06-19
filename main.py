import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
import os
from urllib.parse import urljoin, urlparse
import logging
from typing import Dict, List, Optional
import re

class EGramSwarajScraper:
    def __init__(self, delay=1, max_retries=3):
        """
        Initialize the scraper with rate limiting and retry logic
        
        Args:
            delay: Delay between requests in seconds
            max_retries: Maximum number of retries for failed requests
        """
        self.base_url = "https://egramswaraj.gov.in"
        self.delay = delay
        self.max_retries = max_retries
        self.session = requests.Session()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Headers to mimic browser behavior
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Data storage
        self.scraped_data = {
            'states': [],
            'districts': [],
            'blocks': [],
            'villages': [],
            'vouchers': [],
            'voucher_details': []
        }

    def make_request(self, url: str) -> Optional[BeautifulSoup]:
        """Make HTTP request with retry logic and rate limiting"""
        for attempt in range(self.max_retries):
            try:
                time.sleep(self.delay)  # Rate limiting
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                self.logger.info(f"Successfully fetched: {url}")
                return BeautifulSoup(response.content, 'html.parser')
                
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt == self.max_retries - 1:
                    self.logger.error(f"Failed to fetch {url} after {self.max_retries} attempts")
                    return None
                time.sleep(self.delay * (attempt + 1))  # Exponential backoff
        
        return None

    def scrape_state_report(self) -> Dict:
        """Scrape the main state report page"""
        url = f"{self.base_url}/FileRedirect.jsp?FD=SummaryReport2025-2026&name=StateSummaryReport.html"
        soup = self.make_request(url)
        
        if not soup:
            return {}
        
        state_data = {
            'url': url,
            'title': soup.title.string if soup.title else '',
            'content': str(soup)
        }
        
        self.scraped_data['states'].append(state_data)
        self.logger.info("State report scraped successfully")
        return state_data

    def scrape_districts(self, state_code: str = "27") -> List[Dict]:
        """Scrape all districts for a given state"""
        districts_url = f"{self.base_url}/FileRedirect.jsp?FD=SummaryReport2025-2026/{state_code}&name={state_code}.html"
        soup = self.make_request(districts_url)
        
        if not soup:
            return []

        # Extract district links/codes from the page
        districts = []
        
        # Look for district codes in the range 424-456
        for district_code in range(424, 457):  # 424 to 456 inclusive
            district_url = f"{self.base_url}/FileRedirect.jsp?FD=SummaryReport2025-2026/{state_code}/{district_code}&name={district_code}.html"
            district_soup = self.make_request(district_url)
            
            if district_soup:
                district_data = {
                    'state_code': state_code,
                    'district_code': district_code,
                    'url': district_url,
                    'title': district_soup.title.string if district_soup.title else '',
                    'content': str(district_soup)
                }
                districts.append(district_data)
                self.scraped_data['districts'].append(district_data)
                
                # Extract blocks for this district
                self.scrape_blocks(state_code, str(district_code))
        
        self.logger.info(f"Scraped {len(districts)} districts")
        return districts

    def scrape_blocks(self, state_code: str, district_code: str) -> List[Dict]:
        """Scrape all blocks for a given district"""
        district_url = f"{self.base_url}/FileRedirect.jsp?FD=SummaryReport2025-2026/{state_code}/{district_code}&name={district_code}.html"
        soup = self.make_request(district_url)
        
        if not soup:
            return []

        blocks = []
        # Extract block codes from the district page
        # Look for 4-digit block codes in links
        block_links = soup.find_all('a', href=True) if soup else []
        block_codes = set()
        
        for link in block_links:
            href = link.get('href', '')
            # Extract 4-digit codes from href
            matches = re.findall(r'/(\d{4})\.html', href)
            block_codes.update(matches)
        
        # If no blocks found in links, try a range-based approach
        if not block_codes:
            # Try common block code ranges (this might need adjustment based on actual data)
            for block_code in range(4700, 4800):  # Adjust range as needed
                block_url = f"{self.base_url}/FileRedirect.jsp?FD=SummaryReport2025-2026/{state_code}/{district_code}&name={block_code}.html"
                block_soup = self.make_request(block_url)
                
                if block_soup and block_soup.title and "Error" not in block_soup.title.string:
                    block_codes.add(str(block_code))

        for block_code in block_codes:
            block_url = f"{self.base_url}/FileRedirect.jsp?FD=SummaryReport2025-2026/{state_code}/{district_code}&name={block_code}.html"
            block_soup = self.make_request(block_url)
            
            if block_soup:
                block_data = {
                    'state_code': state_code,
                    'district_code': district_code,
                    'block_code': block_code,
                    'url': block_url,
                    'title': block_soup.title.string if block_soup.title else '',
                    'content': str(block_soup)
                }
                blocks.append(block_data)
                self.scraped_data['blocks'].append(block_data)
                
                # Extract villages for this block
                self.scrape_villages(state_code, district_code, block_code)
        
        self.logger.info(f"Scraped {len(blocks)} blocks for district {district_code}")
        return blocks

    def scrape_villages(self, state_code: str, district_code: str, block_code: str) -> List[Dict]:
        """Scrape all villages for a given block"""
        block_url = f"{self.base_url}/FileRedirect.jsp?FD=SummaryReport2025-2026/{state_code}/{district_code}&name={block_code}.html"
        soup = self.make_request(block_url)
        
        if not soup:
            return []

        villages = []
        # Extract village codes from the block page
        village_links = soup.find_all('a', href=True) if soup else []
        village_codes = set()
        
        for link in village_links:
            href = link.get('href', '')
            # Extract village codes (typically 6-digit codes)
            matches = re.findall(r'/(\d{6})\.html', href)
            village_codes.update(matches)

        for village_code in village_codes:
            village_url = f"{self.base_url}/FileRedirect.jsp?FD=FinancialYear2025-2026/{state_code}&name={village_code}.html"
            village_soup = self.make_request(village_url)
            
            if village_soup:
                village_data = {
                    'state_code': state_code,
                    'district_code': district_code,
                    'block_code': block_code,
                    'village_code': village_code,
                    'url': village_url,
                    'title': village_soup.title.string if village_soup.title else '',
                    'content': str(village_soup)
                }
                villages.append(village_data)
                self.scraped_data['villages'].append(village_data)
                
                # Extract vouchers for this village
                self.scrape_vouchers(state_code, district_code, block_code, village_code)
        
        self.logger.info(f"Scraped {len(villages)} villages for block {block_code}")
        return villages

    def scrape_vouchers(self, state_code: str, district_code: str, block_code: str, village_code: str) -> List[Dict]:
        """Scrape voucher data for a given village"""
        vouchers = []
        
        # Scrape monthly voucher data (months 1-12)
        for month in range(1, 13):
            voucher_url = f"{self.base_url}/voucherWiseReport.do?voucherWise=Y&finYear=2025-2026&month={month}&schemewise=P&state={state_code}&district={district_code}&block={block_code}&village={village_code}&schemeCode=-1"
            soup = self.make_request(voucher_url)
            
            if soup:
                voucher_data = {
                    'state_code': state_code,
                    'district_code': district_code,
                    'block_code': block_code,
                    'village_code': village_code,
                    'month': month,
                    'url': voucher_url,
                    'content': str(soup)
                }
                vouchers.append(voucher_data)
                self.scraped_data['vouchers'].append(voucher_data)
                
                # Extract voucher IDs and get details
                self.extract_voucher_details(soup, state_code, district_code, block_code, village_code)
        
        self.logger.info(f"Scraped vouchers for village {village_code}")
        return vouchers

    def extract_voucher_details(self, soup: BeautifulSoup, state_code: str, district_code: str, block_code: str, village_code: str):
        """Extract individual voucher details from voucher list page"""
        if not soup:
            return

        # Look for voucher IDs in the page
        voucher_links = soup.find_all('a', href=True)
        voucher_ids = set()
        
        for link in voucher_links:
            href = link.get('href', '')
            if 'voucherID=' in href:
                match = re.search(r'voucherID=(\d+)', href)
                if match:
                    voucher_ids.add(match.group(1))

        for voucher_id in voucher_ids:
            detail_url = f"{self.base_url}/paymentVoucherDetail.do?finYear=2025-2026&PRIEntity_code={village_code}&stateCode={state_code}&districtCode={district_code}&blockCode={block_code}&villageCode={village_code}&voucherID={voucher_id}"
            detail_soup = self.make_request(detail_url)
            
            if detail_soup:
                detail_data = {
                    'state_code': state_code,
                    'district_code': district_code,
                    'block_code': block_code,
                    'village_code': village_code,
                    'voucher_id': voucher_id,
                    'url': detail_url,
                    'content': str(detail_soup)
                }
                self.scraped_data['voucher_details'].append(detail_data)

    def save_data(self, output_dir: str = "egramswaraj_data"):
        """Save scraped data to files"""
        os.makedirs(output_dir, exist_ok=True)
        
        for data_type, data_list in self.scraped_data.items():
            if data_list:
                # Save as JSON
                json_file = os.path.join(output_dir, f"{data_type}.json")
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(data_list, f, indent=2, ensure_ascii=False)
                
                # Save as CSV (for structured data)
                if data_type != 'content':  # Skip raw HTML content for CSV
                    csv_data = []
                    for item in data_list:
                        csv_row = {k: v for k, v in item.items() if k != 'content'}
                        csv_data.append(csv_row)
                    
                    if csv_data:
                        df = pd.DataFrame(csv_data)
                        csv_file = os.path.join(output_dir, f"{data_type}.csv")
                        df.to_csv(csv_file, index=False, encoding='utf-8')
                
                self.logger.info(f"Saved {len(data_list)} {data_type} records")

    def run_full_scrape(self, state_code: str = "27"):
        """Run the complete scraping process"""
        self.logger.info("Starting full scrape of E-Gram Swaraj data")
        
        try:
            # 1. Scrape state report
            self.scrape_state_report()
            
            # 2. Scrape districts (424-456)
            self.scrape_districts(state_code)
            
            # 3. Save all data
            self.save_data()
            
            self.logger.info("Full scrape completed successfully")
            self.print_summary()
            
        except Exception as e:
            self.logger.error(f"Error during scraping: {str(e)}")
            raise

    def print_summary(self):
        """Print summary of scraped data"""
        print("\n" + "="*50)
        print("SCRAPING SUMMARY")
        print("="*50)
        for data_type, data_list in self.scraped_data.items():
            print(f"{data_type.capitalize()}: {len(data_list)} records")
        print("="*50)


# Usage example
if __name__ == "__main__":
    # Initialize scraper with 2-second delay between requests
    scraper = EGramSwarajScraper(delay=2)
    
    # Run full scrape for state code 27
    scraper.run_full_scrape(state_code="27")
    
    print("Scraping completed. Check the 'egramswaraj_data' directory for output files.")