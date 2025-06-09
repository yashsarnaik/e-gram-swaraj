# app.py

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import json
import time
import re

def fetch_json_with_selenium(url, output_file="json_data.txt"):
    """
    Opens a headless browser, fetches JSON data from URL, and saves to file.

    Args:
        url (str): The URL to fetch JSON data from
        output_file (str): Name of the output file to save JSON data
    """

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
