#!/usr/bin/env python3
"""
Test script to verify Playwright Chromium installation and functionality.
Run this script to check if Chromium is properly installed and working.
"""

import asyncio
import sys
from playwright.async_api import async_playwright


async def test_chromium():
    """Test if Chromium is installed and can be launched."""
    print("Testing Playwright Chromium installation...")
    print("-" * 50)
    
    try:
        async with async_playwright() as p:
            print("✓ Playwright initialized successfully")
            
            # Try to launch Chromium
            print("\nAttempting to launch Chromium...")
            browser = await p.chromium.launch(headless=True)
            print("✓ Chromium browser launched successfully")
            
            # Create a page and navigate
            print("\nCreating a new page...")
            page = await browser.new_page()
            print("✓ New page created")
            
            # Navigate to a simple page
            print("\nNavigating to example.com...")
            await page.goto("https://example.com")
            print("✓ Navigation successful")
            
            # Get page title
            title = await page.title()
            print(f"✓ Page title: {title}")
            
            # Get page URL
            url = page.url
            print(f"✓ Current URL: {url}")
            
            # Close browser
            await browser.close()
            print("\n✓ Browser closed successfully")
            
            print("\n" + "=" * 50)
            print("✅ SUCCESS: Chromium is installed and working correctly!")
            print("=" * 50)
            return True
            
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {str(e)}")
        print("\n" + "=" * 50)
        print("❌ FAILED: Chromium installation or launch failed")
        print("=" * 50)
        print("\nTroubleshooting steps:")
        print("1. Install Chromium: playwright install chromium")
        print("2. Install all browsers: playwright install")
        print("3. Check Playwright version: pip show playwright")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_chromium())
    sys.exit(0 if success else 1)
