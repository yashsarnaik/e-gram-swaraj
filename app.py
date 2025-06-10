from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time

def fetch_json_with_selenium(url, output_file="json_data.txt"):
    """
    Opens a headless browser, fetches JSON data from URL, and saves to file
    
    Args:
        url (str): The URL to fetch JSON data from
        output_file (str): Name of the output file to save JSON data
    """
    
    # Set up Chrome options for headless browsing
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = None
    
    try:
        # Initialize the Chrome driver
        print("Starting headless browser...")
        driver = webdriver.Chrome(options=chrome_options)
        
        # Set page load timeout
        driver.set_page_load_timeout(30)
        
        # Navigate to the URL
        print(f"Navigating to: {url}")
        driver.get(url)
        
        # Wait a moment for the page to load completely
        time.sleep(2)
        
        # Get the page source (which should contain JSON data)
        page_content = driver.page_source
        
        # Try to extract JSON from the page
        # Method 1: Try to get text from <pre> tag (common for JSON APIs)
        try:
            pre_element = driver.find_element(By.TAG_NAME, "pre")
            json_text = pre_element.text
        except:
            # Method 2: Try to get text from <body> tag
            try:
                body_element = driver.find_element(By.TAG_NAME, "body")
                json_text = body_element.text
            except:
                # Method 3: Use page source directly
                json_text = page_content
        
        # Clean up the JSON text (remove HTML tags if any)
        if json_text.startswith('<!DOCTYPE html>') or json_text.startswith('<html'):
            # If we got HTML, try to extract JSON from it
            import re
            json_match = re.search(r'<pre[^>]*>(.*?)</pre>', json_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                # Try to find JSON-like content
                json_match = re.search(r'(\{.*\}|\[.*\])', json_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(1)
        
        # Validate if it's valid JSON
        try:
            json_data = json.loads(json_text)
            # Pretty print the JSON
            formatted_json = json.dumps(json_data, indent=2, ensure_ascii=False)
            print("✓ Valid JSON data retrieved")
        except json.JSONDecodeError:
            # If not valid JSON, save as is
            formatted_json = json_text
            print("⚠ Content retrieved (may not be valid JSON)")
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(formatted_json)
        
        print(f"✓ Data saved to: {output_file}")
        print(f"✓ Data size: {len(formatted_json)} characters")
        
        return True
        
    except Exception as e:
        print(f"✗ Error occurred: {str(e)}")
        return False
        
    finally:
        # Close the browser
        if driver:
            print("Closing browser...")
            driver.quit()
            print("✓ Browser closed")

# Example usage
if __name__ == "__main__":
    # Replace with your desired URL
    target_url = input("Enter the URL to fetch JSON from: ").strip()
    
    if not target_url:
        target_url = "https://jsonplaceholder.typicode.com/posts/1"  # Default example URL
        print(f"Using default URL: {target_url}")
    
    # Optional: specify output filename
    output_filename = input("Enter output filename (press Enter for 'json_data.txt'): ").strip()
    if not output_filename:
        output_filename = "json_data.txt"
    
    # Fetch the JSON data
    success = fetch_json_with_selenium(target_url, output_filename)
    
    if success:
        print("\n✓ Task completed successfully!")
    else:
        print("\n✗ Task failed!")