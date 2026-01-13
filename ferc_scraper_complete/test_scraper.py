#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, 'src')

from ferc_scraper.config import get_settings
from ferc_scraper.http import build_session, retrying_fetch
from ferc_scraper.parser import parse_list_page

def test_ferc_scraper():
    """Test the FERC scraper functionality without database connection"""
    
    # Set environment variables for testing
    os.environ['MAX_PAGES'] = '1'
    os.environ['FETCH_DETAILS'] = 'false'
    os.environ['SCRAPER_MODE'] = 'dbindex'
    
    # Get settings
    settings = get_settings()
    print(f"Testing scraper with settings:")
    print(f"  Base URL: {settings.base_url}")
    print(f"  Scraper Mode: {settings.scraper_mode}")
    print(f"  Max Pages: {settings.max_pages}")
    print(f"  Fetch Details: {settings.fetch_details}")
    
    # Build session
    session = build_session(
        source_ip=settings.source_ip, 
        outbound_proxy_url=settings.outbound_proxy_url
    )
    
    try:
        # Fetch the FERC database download page
        print(f"\nFetching: {settings.base_url}")
        response = retrying_fetch(
            session, 
            settings.base_url, 
            timeout=settings.request_timeout_seconds, 
            max_attempts=settings.max_retries
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Content Length: {len(response.text)} characters")
        
        # Parse the page
        items = parse_list_page(response.text, settings.base_url)
        print(f"\nFound {len(items)} database items:")
        
        for i, item in enumerate(items[:10]):  # Show first 10 items
            print(f"  {i+1}. {item.title}")
            print(f"     URL: {item.url}")
            print(f"     ID: {item.document_id}")
            if item.published_at:
                print(f"     Date: {item.published_at}")
            print()
        
        if len(items) > 10:
            print(f"... and {len(items) - 10} more items")
            
        return len(items)
        
    except Exception as e:
        print(f"Error testing scraper: {e}")
        return 0

if __name__ == "__main__":
    count = test_ferc_scraper()
    print(f"\nTest completed. Found {count} items.")