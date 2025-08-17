#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, 'src')

from ferc_scraper.config import get_settings
from ferc_scraper.selenium_client import SeleniumHTTPClient
from ferc_scraper.parser import parse_list_page

def test_selenium_scraper():
    """Test the Selenium-based FERC scraper"""
    
    # Set environment variables for testing
    os.environ['MAX_PAGES'] = '1'
    os.environ['FETCH_DETAILS'] = 'false'
    os.environ['SCRAPER_MODE'] = 'dbindex'
    
    # Get settings
    settings = get_settings()
    print(f"Testing Selenium scraper with settings:")
    print(f"  Base URL: {settings.base_url}")
    print(f"  Scraper Mode: {settings.scraper_mode}")
    print(f"  Timeout: {settings.request_timeout_seconds} seconds")
    
    try:
        # Test Selenium client
        print(f"\nInitializing Selenium client...")
        with SeleniumHTTPClient(headless=True, timeout=settings.request_timeout_seconds) as selenium_client:
            print(f"Fetching: {settings.base_url}")
            
            # Fetch the page
            content = selenium_client.get_page_with_retry(settings.base_url, max_retries=2)
            
            if content:
                print(f"✅ Successfully fetched page!")
                print(f"   Content length: {len(content)} characters")
                
                # Check if we got actual content (not Cloudflare challenge)
                if "just a moment" in content.lower():
                    print("❌ Still getting Cloudflare challenge page")
                    return False
                    
                if len(content) < 1000:
                    print("❌ Content too short, might be blocked")
                    return False
                
                # Parse the content
                items = parse_list_page(content, settings.base_url)
                print(f"\n✅ Found {len(items)} database items:")
                
                for i, item in enumerate(items[:5]):  # Show first 5 items
                    print(f"  {i+1}. {item.title}")
                    print(f"     URL: {item.url}")
                    print(f"     ID: {item.document_id}")
                    if item.published_at:
                        print(f"     Date: {item.published_at}")
                    print()
                
                if len(items) > 5:
                    print(f"... and {len(items) - 5} more items")
                    
                return len(items) > 0
                
            else:
                print("❌ Failed to fetch page content")
                return False
                
    except Exception as e:
        print(f"❌ Error testing Selenium scraper: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testing Selenium-based FERC Scraper")
    print("=" * 50)
    
    success = test_selenium_scraper()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Selenium scraper test PASSED!")
        print("   The scraper can successfully bypass Cloudflare protection.")
    else:
        print("❌ Selenium scraper test FAILED!")
        print("   Check the error messages above for details.")
    
    print("\nTest completed.")