"""
Test scrapers and save raw output to files for manual LLM processing
"""
import json
import os
from datetime import datetime
from playwright.sync_api import sync_playwright
import time

OUTPUT_DIR = "/home/anshad/deal-curation-platform/scraped_output"

def save_output(filename, data):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved: {filepath}")
    return filepath

def scrape_alrajhi():
    print("\n=== SCRAPING ALRAJHI BANK ===")
    url = "https://www.alrajhibank.com.sa/en/Personal/Offers/CardsOffers"
    deals = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print(f"Navigating to {url}")
        page.goto(url, timeout=60000)
        time.sleep(5)
        page.wait_for_load_state('networkidle')
        
        # Take screenshot
        screenshot_path = os.path.join(OUTPUT_DIR, "alrajhi_screenshot.png")
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot saved: {screenshot_path}")
        
        # Get all text content
        body_text = page.inner_text('body')
        print(f"\nPage text length: {len(body_text)} chars")
        
        # Find offer links
        offer_links = page.query_selector_all('a[href*="/Offers/"]')
        print(f"Found {len(offer_links)} offer links")
        
        for link in offer_links:
            try:
                href = link.get_attribute('href')
                text = link.inner_text().strip()
                if href and text and len(text) > 5:
                    full_url = f"https://www.alrajhibank.com.sa{href}" if not href.startswith('http') else href
                    deals.append({
                        'title': text,
                        'url': full_url,
                        'source': 'Alrajhi Bank'
                    })
            except:
                pass
        
        # Try to get offer cards
        cards = page.query_selector_all('[class*="offer"], [class*="card"], [class*="deal"]')
        print(f"Found {len(cards)} potential offer elements")
        
        browser.close()
    
    data = {
        'source': 'Alrajhi Bank',
        'url': url,
        'scraped_at': datetime.now().isoformat(),
        'page_text': body_text,
        'deals': deals,
        'total_found': len(deals)
    }
    
    return save_output('alrajhi_raw.json', data)

def scrape_riyad():
    print("\n=== SCRAPING RIYAD BANK ===")
    url = "https://www.riyadbank.com/personal-banking/credit-cards/offers"
    deals = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print(f"Navigating to {url}")
        page.goto(url, timeout=60000)
        time.sleep(5)
        page.wait_for_load_state('networkidle')
        
        # Take screenshot
        screenshot_path = os.path.join(OUTPUT_DIR, "riyad_screenshot.png")
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot saved: {screenshot_path}")
        
        # Get all text content
        body_text = page.inner_text('body')
        print(f"\nPage text length: {len(body_text)} chars")
        
        # Try to click through tabs
        tabs = page.query_selector_all('[role="tab"], .tab, [class*="tab"]')
        print(f"Found {len(tabs)} tabs")
        
        for tab in tabs[:5]:  # Click first 5 tabs
            try:
                tab.click()
                time.sleep(2)
            except:
                pass
        
        # Get updated text
        body_text = page.inner_text('body')
        
        # Find offer elements
        offer_elements = page.query_selector_all('[class*="offer"], [class*="discount"], img[alt*="offer" i]')
        print(f"Found {len(offer_elements)} offer elements")
        
        for elem in offer_elements[:50]:
            try:
                text = elem.inner_text().strip()
                if text and len(text) > 10:
                    deals.append({
                        'text': text[:500],
                        'source': 'Riyad Bank'
                    })
            except:
                pass
        
        browser.close()
    
    data = {
        'source': 'Riyad Bank',
        'url': url,
        'scraped_at': datetime.now().isoformat(),
        'page_text': body_text,
        'deals': deals,
        'total_found': len(deals)
    }
    
    return save_output('riyad_raw.json', data)

def scrape_sab():
    print("\n=== SCRAPING SAB BANK ===")
    url = "https://www.sab.com/en/personal/compare-credit-cards/credit-card-special-offers/all-offers/"
    deals = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print(f"Navigating to {url}")
        page.goto(url, timeout=60000)
        time.sleep(5)
        page.wait_for_load_state('networkidle')
        
        # Take screenshot
        screenshot_path = os.path.join(OUTPUT_DIR, "sab_screenshot.png")
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot saved: {screenshot_path}")
        
        # Get all text content
        body_text = page.inner_text('body')
        print(f"\nPage text length: {len(body_text)} chars")
        
        # Find offer elements
        offer_elements = page.query_selector_all('[class*="offer"], [class*="deal"], img[src*="offer" i]')
        print(f"Found {len(offer_elements)} offer elements")
        
        for elem in offer_elements[:50]:
            try:
                text = elem.inner_text().strip()
                if text and len(text) > 10:
                    deals.append({
                        'text': text[:500],
                        'source': 'SAB Bank'
                    })
            except:
                pass
        
        # Get all images
        images = page.query_selector_all('img')
        image_urls = []
        for img in images:
            src = img.get_attribute('src')
            alt = img.get_attribute('alt') or ''
            if src and ('offer' in src.lower() or 'offer' in alt.lower() or 'deal' in alt.lower()):
                full_url = src if src.startswith('http') else f"https://www.sab.com{src}"
                image_urls.append({
                    'url': full_url,
                    'alt': alt
                })
        
        browser.close()
    
    data = {
        'source': 'SAB Bank',
        'url': url,
        'scraped_at': datetime.now().isoformat(),
        'page_text': body_text,
        'deals': deals,
        'images': image_urls,
        'total_found': len(deals)
    }
    
    return save_output('sab_raw.json', data)

def create_combined_text():
    """Create a single text file with all scraped content for LLM processing"""
    print("\n=== CREATING COMBINED TEXT FILE ===")
    
    combined = []
    combined.append("=" * 80)
    combined.append("DEAL CURATION PLATFORM - SCRAPED CONTENT")
    combined.append(f"Scraped at: {datetime.now().isoformat()}")
    combined.append("=" * 80)
    
    for filename in ['alrajhi_raw.json', 'riyad_raw.json', 'sab_raw.json']:
        filepath = os.path.join(OUTPUT_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            combined.append(f"\n{'='*80}")
            combined.append(f"SOURCE: {data['source']}")
            combined.append(f"URL: {data['url']}")
            combined.append(f"{'='*80}")
            combined.append(f"\n--- PAGE TEXT ---\n")
            combined.append(data.get('page_text', 'N/A'))
            
            if data.get('deals'):
                combined.append(f"\n--- DEALS FOUND ({len(data['deals'])}) ---\n")
                for i, deal in enumerate(data['deals'], 1):
                    combined.append(f"\nDeal {i}:")
                    for k, v in deal.items():
                        combined.append(f"  {k}: {v}")
    
    text_content = '\n'.join(combined)
    text_path = os.path.join(OUTPUT_DIR, 'all_scraped_content.txt')
    with open(text_path, 'w', encoding='utf-8') as f:
        f.write(text_content)
    
    print(f"Combined text saved: {text_path}")
    print(f"Total length: {len(text_content)} characters")
    
    return text_path

if __name__ == "__main__":
    print("Starting scraper test...")
    
    # Scrape all sources
    alrajhi_file = scrape_alrajhi()
    riyad_file = scrape_riyad()
    sab_file = scrape_sab()
    
    # Create combined text file
    combined_file = create_combined_text()
    
    print("\n" + "="*80)
    print("SCRAPING COMPLETE!")
    print("="*80)
    print(f"\nOutput files saved to: {OUTPUT_DIR}")
    print("\nFiles created:")
    print(f"  1. {alrajhi_file}")
    print(f"  2. {riyad_file}")
    print(f"  3. {sab_file}")
    print(f"  4. {combined_file}")
    print(f"  5. {OUTPUT_DIR}/alrajhi_screenshot.png")
    print(f"  6. {OUTPUT_DIR}/riyad_screenshot.png")
    print(f"  7. {OUTPUT_DIR}/sab_screenshot.png")
    print("\nNEXT STEP:")
    print("  Open 'all_scraped_content.txt' and copy to ChatGPT/Claude")
    print("  Ask the LLM to convert to structured deal format")
