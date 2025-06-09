from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import json
import time

def fetch_json_with_selenium(url, output_file="json_data.txt"):
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    import json, time, re

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    try:
        print("Starting headless browser...")
        service = Service(ChromeDriverManager().install())
        print(f"Using ChromeDriver from: {service.path}")
        driver = webdriver.Chrome(service=service, options=chrome_options)

        driver.set_page_load_timeout(30)
        print(f"Navigating to: {url}")
        driver.get(url)
        time.sleep(2)

        try:
            pre_element = driver.find_element(By.TAG_NAME, "pre")
            json_text = pre_element.text
        except:
            try:
                body_element = driver.find_element(By.TAG_NAME, "body")
                json_text = body_element.text
            except:
                json_text = driver.page_source

        if json_text.startswith('<!DOCTYPE html>') or json_text.startswith('<html'):
            json_match = re.search(r'<pre[^>]*>(.*?)</pre>', json_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                json_match = re.search(r'(\{.*\}|\[.*\])', json_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(1)

        try:
            json_data = json.loads(json_text)
            formatted_json = json.dumps(json_data, indent=2, ensure_ascii=False)
            print("✓ Valid JSON data retrieved")
        except json.JSONDecodeError:
            formatted_json = json_text
            print("⚠ Content retrieved (may not be valid JSON)")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(formatted_json)

        print(f"✓ Data saved to: {output_file}")
        return True

    except Exception as e:
        print(f"✗ Error occurred: {e}")
        return False
    finally:
        try:
            driver.quit()
            print("✓ Browser closed")
        except:
            pass


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