#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="requests")

import os
import time
import re
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

try:
    from webdriver_manager.chrome import ChromeDriverManager
    USE_MANAGER = True
except ImportError:
    USE_MANAGER = False

class SimpleHTMLParser:
    def __init__(self, url, headless=True, output_file=None):
        self.url = url
        self.domain = urlparse(url).netloc
        self.output_dir = "parsed_" + self.domain.replace('.', '_')
        self.output_file = output_file
        
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument("--headless=new")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        if USE_MANAGER:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            self.driver = webdriver.Chrome(options=chrome_options)
    
    def take_full_screenshot(self, screenshot_path=None):
        """Take full page screenshot"""
        print("\nTaking full page screenshot...")
        
        # Determine screenshot path
        if not screenshot_path:
            if self.output_file:
                base_path = os.path.splitext(self.output_file)[0]
            else:
                base_path = os.path.join(self.output_dir, 'screenshot')
            screenshot_path = f"{base_path}_fullpage.png"
        
        # Create directory if needed
        os.makedirs(os.path.dirname(os.path.abspath(screenshot_path)) or '.', exist_ok=True)
        
        # Get original window size
        original_size = self.driver.get_window_size()
        
        # Get page height
        page_height = self.driver.execute_script("return document.body.scrollHeight")
        page_width = self.driver.execute_script("return document.body.scrollWidth")
        
        # Set window size to full page
        self.driver.set_window_size(page_width, page_height)
        time.sleep(1)
        
        try:
            # Take full page screenshot
            self.driver.save_screenshot(screenshot_path)
            print(f"✓ Full page screenshot saved: {os.path.abspath(screenshot_path)}")
            print(f"  Image size: {page_width}x{page_height} pixels")
            
            # Restore original window size
            self.driver.set_window_size(original_size['width'], original_size['height'])
            
            return screenshot_path
        except Exception as e:
            print(f"✗ Failed to take full page screenshot: {e}")
            # Fallback: take viewport screenshot
            fallback_path = screenshot_path.replace('.png', '_viewport.png')
            self.driver.save_screenshot(fallback_path)
            print(f"  Saved viewport screenshot instead: {fallback_path}")
            return fallback_path
    
    def save_page(self, wait_time=5, take_screenshot=True):
        print(f"\nLoading: {self.url}")
        self.driver.get(self.url)
        time.sleep(wait_time)
        
        # Wait for dynamic content
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            print("Page loaded successfully")
        except:
            print("Warning: Page may not be fully loaded")
        
        # Scroll page to load all dynamic content
        print("Scrolling page to load all content...")
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        while True:
            # Scroll down
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Scroll up a bit to trigger any lazy loading
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight - 500);")
            time.sleep(1)
            
            # Check new height
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        # Scroll back to top
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # Take full page screenshot (if requested)
        screenshot_path = None
        if take_screenshot:
            screenshot_path = self.take_full_screenshot()
        
        html = self.driver.page_source
        
        # Filter lines with regex - keywords in Russian
        pattern = r'^.*?(?:нижних|верхних|нижнее|верхнее|место|вагон|схема).*?$'
        
        lines = html.split('\n')
        filtered_lines = []
        
        for line in lines:
            if re.search(pattern, line, re.IGNORECASE | re.UNICODE):
                filtered_lines.append(line)
        
        filtered_html = '\n'.join(filtered_lines)
        
        # Statistics
        original_lines = len(lines)
        filtered_lines_count = len(filtered_lines)
        
        print(f"\nFiltering lines...")
        print(f"Total lines: {original_lines:,}")
        print(f"Filtered lines: {filtered_lines_count:,}")
        print(f"Removed lines: {original_lines - filtered_lines_count:,}")
        
        if filtered_lines_count == 0:
            print("\nWARNING: No lines with keywords found!")
            print("Try increasing wait time or check if elements exist on page.")
        
        # Determine save path
        if self.output_file:
            file_path = self.output_file
            dir_path = os.path.dirname(os.path.abspath(file_path))
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
        else:
            os.makedirs(self.output_dir, exist_ok=True)
            file_path = os.path.join(self.output_dir, 'index.html')
        
        # Save result
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(filtered_html)
        
        print(f"\n✓ HTML saved: {os.path.abspath(file_path)}")
        print(f"  File size: {len(filtered_html):,} characters")
        
        # Show examples
        if filtered_lines_count > 0:
            print("\n📝 EXAMPLES OF FOUND LINES:")
            print("-" * 50)
            for i, line in enumerate(filtered_lines[:5], 1):
                clean_line = re.sub(r'<[^>]+>', '', line)
                clean_line = ' '.join(clean_line.split())
                if len(clean_line) > 100:
                    clean_line = clean_line[:100] + "..."
                if clean_line.strip():
                    print(f"{i}. {clean_line}")
        
        return file_path, screenshot_path
    
    def close(self):
        self.driver.quit()

def main():
    # ==================== SETTINGS ====================
    
    # URL to parse (CHANGE THIS)
    URL = "https://grandtrain.ru/search/2078001-2000000/11.07.2026/018%D0%99/"
    
    # Settings
    HEADLESS = True      # True - headless mode, False - show browser window
    WAIT_TIME = 5        # Wait time in seconds
    TAKE_SCREENSHOT = True  # Take full page screenshot
    
    # OUTPUT FILE PATH
    # Options:
    # 1. None - auto create folder parsed_domain/index.html
    # 2. "result.html" - save in current folder
    # 3. "results/my_parsed_data.html" - save in subfolder
    # 4. "/home/user/Documents/parsed.html" - absolute path
    OUTPUT_FILE = "/home/and/parser/parsed_grandtrain_ru/index.html"  # <--- CHANGE IF NEEDED
    
    # Examples:
    # OUTPUT_FILE = "result.html"
    # OUTPUT_FILE = "data/filtered_content.html"
    
    # ===================================================
    
    print("="*60)
    print("HTML PARSER WITH REGEX FILTER & FULL PAGE SCREENSHOT")
    print("="*60)
    print(f"URL: {URL}")
    print(f"Filter: lines containing Russian keywords (места, вагоны, схема)")
    if OUTPUT_FILE:
        print(f"Save to: {OUTPUT_FILE}")
    else:
        print("Save to: auto folder (parsed_domain/)")
    print(f"Screenshot: {'Yes (full page)' if TAKE_SCREENSHOT else 'No'}")
    print("-"*60)
    
    parser = SimpleHTMLParser(URL, HEADLESS, OUTPUT_FILE)
    try:
        html_file, screenshot_file = parser.save_page(WAIT_TIME, TAKE_SCREENSHOT)
        
        print("\n" + "="*60)
        print("✅ PARSING COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"📄 HTML file: {html_file}")
        if screenshot_file:
            print(f"📸 Full page screenshot: {screenshot_file}")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        parser.close()
    
    print("\nDone!")

if __name__ == "__main__":
    main()