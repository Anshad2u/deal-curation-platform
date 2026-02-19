"""
Complete SAB Bank scraper - All categories and all pages
"""
import sys
sys.path.insert(0, '/home/anshad/deal-curation-platform')

import hashlib
from datetime import datetime, date
from playwright.sync_api import sync_playwright
import time
import re
from app.database import SessionLocal, RawDeal, StructuredDeal, Rating, Source
from app.config import score_deal

def generate_hash(title, merchant):
    normalized = f"{(title or '').lower().strip()}|{(merchant or '').lower().strip()}"
    return hashlib.md5(normalized.encode()).hexdigest()

def parse_date(date_str):
    if not date_str:
        return None
    months = {
        'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
        'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6, 'july': 7, 'jul': 7,
        'august': 8, 'aug': 8, 'september': 9, 'sep': 9, 'october': 10, 'oct': 10,
        'november': 11, 'nov': 11, 'december': 12, 'dec': 12
    }
    try:
        date_str = date_str.replace(',', '').replace('.', '').strip()
        parts = date_str.split()
        day = 0
        month = 0
        year = 2026
        
        for p in parts:
            p_lower = p.lower()
            if p_lower in months:
                month = months[p_lower]
            elif p.isdigit():
                if len(p) == 4:
                    year = int(p)
                else:
                    day = int(p)
        
        if day and month:
            return date(year, month, min(day, 28))
    except:
        pass
    return None

def scrape_sab_all_pages():
    """Scrape SAB Bank with pagination - ALL pages"""
    print("\nScraping SAB Bank - ALL CATEGORIES & PAGES...")
    all_deals = []
    
    base_url = "https://www.sab.com/en/personal/compare-credit-cards/credit-card-special-offers/all-offers/"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Categories
        categories = [
            ('All', 'other'),
            ('Dining & Groceries', 'dining'),
            ('Travel', 'travel'),
            ('Lifestyle', 'lifestyle'),
            ('Shopping', 'shopping')
        ]
        
        for cat_name, cat_key in categories:
            print(f"\n  Category: {cat_name}")
            
            try:
                page.goto(base_url, timeout=60000)
                time.sleep(3)
                
                # Click category if not "All"
                if cat_name != 'All':
                    try:
                        cat_btn = page.query_selector(f'text="{cat_name}"')
                        if cat_btn:
                            cat_btn.click()
                            time.sleep(3)
                    except:
                        pass
                
                # Paginate through all pages
                page_num = 1
                max_pages = 35  # Safety limit
                
                while page_num <= max_pages:
                    # Wait for content
                    time.sleep(2)
                    page.wait_for_load_state('networkidle')
                    
                    # Get deals on current page
                    body = page.inner_text('body')
                    lines = [l.strip() for l in body.split('\n') if l.strip()]
                    
                    page_deals = 0
                    i = 0
                    
                    while i < len(lines):
                        line = lines[i]
                        
                        # Look for merchant pattern
                        if '- KSA' in line or (line and line == line.upper() and 5 < len(line) < 60):
                            merchant = line.replace('- KSA', '').strip()
                            
                            offer = ""
                            discount = ""
                            validity = ""
                            applicable = "SAB Credit Cards"
                            
                            # Find offer text
                            for j in range(i+1, min(len(lines), i+8)):
                                check = lines[j]
                                if 'off' in check.lower() or '%' in check:
                                    offer = check
                                    match = re.search(r'(\d+%)', check)
                                    if match:
                                        discount = match.group(1)
                                    break
                            
                            # Find applicable cards
                            for j in range(i+1, min(len(lines), i+12)):
                                if 'mada' in lines[j].lower():
                                    applicable = "SAB Credit Cards & Mada Cards"
                                    break
                            
                            # Find validity
                            for j in range(i+1, min(len(lines), i+12)):
                                check = lines[j]
                                if any(m in check.lower() for m in ['january', 'february', 'march', 'april', 
                                                                    'may', 'june', 'july', 'august', 
                                                                    'september', 'october', 'november', 'december']):
                                    validity = check
                                    break
                            
                            if merchant and offer:
                                all_deals.append({
                                    'merchant': merchant,
                                    'offer': offer,
                                    'discount': discount,
                                    'validity': validity,
                                    'category': cat_key,
                                    'source': 'SAB Bank',
                                    'applicable_cards': applicable,
                                    'url': base_url
                                })
                                page_deals += 1
                        
                        i += 1
                    
                    print(f"    Page {page_num}: {page_deals} deals (Total: {len(all_deals)})")
                    
                    # Try to go to next page
                    try:
                        next_btn = page.query_selector('text="Next"')
                        if next_btn:
                            # Check if it's disabled
                            is_disabled = next_btn.evaluate('el => el.disabled || el.classList.contains("disabled")')
                            if is_disabled:
                                break
                            next_btn.click()
                            page_num += 1
                        else:
                            break
                    except:
                        break
                    
                    if page_num > max_pages:
                        print("    Reached max page limit")
                        break
                        
            except Exception as e:
                print(f"    Error: {str(e)[:50]}")
        
        browser.close()
    
    # Deduplicate
    seen = set()
    unique = []
    for d in all_deals:
        h = d['merchant'].lower() + d['offer'].lower()[:50]
        if h not in seen:
            seen.add(h)
            unique.append(d)
    
    return unique

def save_to_db(deals):
    print(f"\nSaving {len(deals)} deals to database...")
    
    db = SessionLocal()
    
    try:
        sab_source = db.query(Source).filter(Source.name == "SAB Bank").first()
        
        good_count = 0
        mediocre_count = 0
        
        for deal in deals:
            import hashlib
            content_hash = hashlib.md5(f"{deal['offer']}|{deal['merchant']}".encode()).hexdigest()
            
            raw_deal = RawDeal(
                source_id=sab_source.id,
                raw_title=deal['offer'],
                raw_description=deal['offer'],
                raw_discount=deal.get('discount', ''),
                raw_validity=deal.get('validity', ''),
                raw_merchant=deal['merchant'],
                content_hash=content_hash,
                status='processed',
                scraped_url=deal.get('url', '')
            )
            db.add(raw_deal)
            db.flush()
            
            valid_until = parse_date(deal.get('validity'))
            discount_type = 'percentage' if '%' in str(deal.get('discount', '')) else 'other'
            
            score, quality, reason = score_deal(
                deal['merchant'],
                deal.get('discount', ''),
                deal.get('category', 'other')
            )
            
            structured_deal = StructuredDeal(
                raw_deal_id=raw_deal.id,
                merchant_name=deal['merchant'],
                offer_title=deal['offer'][:200],
                description=deal['offer'],
                discount_value=deal.get('discount', ''),
                discount_type=discount_type,
                category=deal.get('category', 'other'),
                valid_until=valid_until,
                applicable_cards=deal.get('applicable_cards', 'All Cards'),
                source_url=deal.get('url', ''),
                is_active=True
            )
            db.add(structured_deal)
            db.flush()
            
            rating = Rating(
                deal_id=structured_deal.id,
                quality_score=quality,
                reason=reason,
                llm_score=score,
                llm_reasoning=reason
            )
            db.add(rating)
            
            if quality == 'good':
                good_count += 1
            else:
                mediocre_count += 1
        
        db.commit()
        
        print(f"✓ Saved: {good_count} good, {mediocre_count} mediocre")
        
    except Exception as e:
        print(f"ERROR: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    deals = scrape_sab_all_pages()
    print(f"\n{'='*60}")
    print(f"TOTAL SAB DEALS: {len(deals)}")
    print(f"{'='*60}")
    
    if deals:
        save_to_db(deals)
