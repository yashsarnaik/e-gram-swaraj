#!/usr/bin/env python3
"""
Test script to verify undetected ChromeDriver integration
"""

import logging
from app import fetch_json_with_selenium
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_undetected_chrome():
    """Test undetected ChromeDriver functionality"""
    
    # Test URLs that are known to detect bots
    test_urls = [
        "https://httpbin.org/headers",  # Shows headers sent by browser
        "https://jsonplaceholder.typicode.com/posts/1",  # Simple JSON API
        "https://httpbin.org/user-agent",  # Shows user agent
    ]
    
    logger.info("=" * 60)
    logger.info("TESTING UNDETECTED CHROMEDRIVER")
    logger.info("=" * 60)
    
    # Show current configuration
    logger.info(f"USE_UNDETECTED_CHROME: {Config.USE_UNDETECTED_CHROME}")
    logger.info(f"CHROME_HEADLESS: {Config.CHROME_HEADLESS}")
    logger.info(f"UNDETECTED_CHROME_VERSION: {Config.UNDETECTED_CHROME_VERSION}")
    
    success_count = 0
    total_tests = len(test_urls)
    
    for i, url in enumerate(test_urls, 1):
        logger.info(f"\n--- Test {i}/{total_tests}: {url} ---")
        
        try:
            # Test with proxy
            logger.info("Testing WITH proxy...")
            result_with_proxy = fetch_json_with_selenium(
                url, 
                output_file=f"test_output_{i}_with_proxy.json",
                use_proxy=True
            )
            
            if result_with_proxy:
                logger.info("✓ SUCCESS with proxy")
                success_count += 1
            else:
                logger.error("✗ FAILED with proxy")
            
            # Test without proxy
            logger.info("Testing WITHOUT proxy...")
            result_without_proxy = fetch_json_with_selenium(
                url, 
                output_file=f"test_output_{i}_without_proxy.json",
                use_proxy=False
            )
            
            if result_without_proxy:
                logger.info("✓ SUCCESS without proxy")
            else:
                logger.error("✗ FAILED without proxy")
                
        except Exception as e:
            logger.error(f"✗ ERROR during test: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"TEST RESULTS: {success_count}/{total_tests} tests passed")
    logger.info("=" * 60)
    
    return success_count == total_tests

def test_regular_vs_undetected():
    """Compare regular ChromeDriver vs Undetected ChromeDriver"""
    
    logger.info("\n" + "=" * 60)
    logger.info("COMPARING REGULAR vs UNDETECTED CHROMEDRIVER")
    logger.info("=" * 60)
    
    test_url = "https://httpbin.org/headers"
    
    # Test with regular ChromeDriver
    logger.info("\n--- Testing with REGULAR ChromeDriver ---")
    Config.USE_UNDETECTED_CHROME = False
    
    try:
        result_regular = fetch_json_with_selenium(
            test_url,
            output_file="test_regular_chrome.json",
            use_proxy=False
        )
        logger.info(f"Regular ChromeDriver result: {'SUCCESS' if result_regular else 'FAILED'}")
    except Exception as e:
        logger.error(f"Regular ChromeDriver error: {e}")
    
    # Test with Undetected ChromeDriver
    logger.info("\n--- Testing with UNDETECTED ChromeDriver ---")
    Config.USE_UNDETECTED_CHROME = True
    
    try:
        result_undetected = fetch_json_with_selenium(
            test_url,
            output_file="test_undetected_chrome.json",
            use_proxy=False
        )
        logger.info(f"Undetected ChromeDriver result: {'SUCCESS' if result_undetected else 'FAILED'}")
    except Exception as e:
        logger.error(f"Undetected ChromeDriver error: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("COMPARISON COMPLETE")
    logger.info("Check the output files to compare headers and user agents")
    logger.info("=" * 60)

if __name__ == "__main__":
    logger.info("Starting Undetected ChromeDriver tests...")
    
    # Run basic functionality test
    basic_test_passed = test_undetected_chrome()
    
    # Run comparison test
    test_regular_vs_undetected()
    
    if basic_test_passed:
        logger.info("\n🎉 All tests passed! Undetected ChromeDriver is working correctly.")
    else:
        logger.warning("\n⚠️  Some tests failed. Check the logs above for details.")
