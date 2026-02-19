"""
Complete Riyad Bank scraper - All offers
"""
import sys
sys.path.insert(0, '/home/anshad/deal-curation-platform')

from datetime import datetime, date
from playwright.sync_api import sync_playwright
import time
import hashlib
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

def scrape_riyad_all():
    print("Scraping Riyad Bank - ALL OFFERS...")
    all_deals = []
    
    base_url = "https://www.riyadbank.com/personal-banking/credit-cards/offers"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            print(f"\n  Loading main page...")
            page.goto(base_url, timeout=120000, wait_until="domcontentloaded")
            time.sleep(8)
            
            body = page.inner_text('body')
            print(f"  Page loaded, searching for offer links...")
            
            offer_links = page.query_selector_all('a')
            
            links = set()
            for link in offer_links:
                try:
                    href = link.get_attribute('href')
                    text = link.inner_text().strip() if link.inner_text() else ""
                    if href and len(href) > 5 and len(href) < 80 and not any(x in href for x in ['personal-banking', 'credit-cards/offers', 'finance', 'accounts', 'contact', 'javascript', 'http']):
                        if text and len(text) > 2:
                            links.add((href, text))
                except:
                    pass
            
            print(f"  Found {len(links)} potential offer links")
            
            for i, (href, merchant) in enumerate(list(links)[:40], 1):
                try:
                    offer_url = f"https://www.riyadbank.com{href}" if href.startswith('/') else href
                    page.goto(offer_url, timeout=20000)
                    time.sleep(2)
                    
                    offer_body = page.inner_text('body')
                    
                    discount = ""
                    disc_match = re.search(r'(\d+)\s*%', offer_body)
                    if disc_match:
                        discount = disc_match.group(1) + '%'
                    
                    offer_text = ""
                    for line in offer_body.split('\n'):
                        if 'off' in line.lower() or 'discount' in line.lower():
                            if len(line) > 20:
                                offer_text = line[:200]
                                break
                    
                    if not offer_text:
                        offer_text = f"Special offer at {merchant}"
                    
                    validity = ""
                    for line in offer_body.split('\n'):
                        if 'valid' in line.lower() and any(m in line.lower() for m in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
                            validity = line[:100]
                            break
                    
                    category = "other"
                    lower_text = offer_body.lower()
                    if any(x in lower_text for x in ['restaurant', 'cafe', 'coffee', 'food', 'kitchen', 'grill']):
                        category = "dining"
                    elif any(x in lower_text for x in ['spa', 'beauty', 'salon', 'clinic']):
                        category = "lifestyle"
                    elif any(x in lower_text for x in ['hotel', 'resort', 'travel', 'airline']):
                        category = "travel"
                    elif any(x in lower_text for x in ['shop', 'store', 'fashion']):
                        category = "shopping"
                    
                    all_deals.append({
                        'merchant': merchant,
                        'offer': offer_text,
                        'discount': discount,
                        'validity': validity,
                        'category': category,
                        'source': 'Riyad Bank',
                        'applicable_cards': 'Riyad Bank Credit Cards',
                        'url': offer_url
                    })
                    
                    if i % 5 == 0:
                        print(f"    Processed {i}/{len(links)} offers...")
                        
                except Exception as e:
                    pass
            
        except Exception as e:
            print(f"  Error: {e}")
        
        browser.close()
    
    # Deduplicate
    seen = set()
    unique = []
    for d in all_deals:
        h = d['merchant'].lower()
        if h not in seen:
            seen.add(h)
            unique.append(d)
    
    return unique

def save_to_db(deals, source_id):
    print(f"\n  Saving {len(deals)} deals to database...")
    
    db = SessionLocal()
    
    try:
        good_count = 0
        mediocre_count = 0
        
        for deal in deals:
            content_hash = generate_hash(deal['offer'], deal['merchant'])
            
            raw_deal = RawDeal(
                source_id=source_id,
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
        
        print(f"  ✓ Saved: {good_count} good, {mediocre_count} mediocre")
        
    except Exception as e:
        print(f"  ERROR: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Check if Riyad Bank source exists
    db = SessionLocal()
    riyad_source = db.query(Source).filter(Source.name == "Riyad Bank").first()
    if not riyad_source:
        riyad_source = Source(
            name="Riyad Bank",
            type="website",
            url="https://www.riyadbank.com/personal-banking/credit-cards/offers",
            is_active=True
        )
        db.add(riyad_source)
        db.commit()
    db.close()
    
    deals = scrape_riyad_all()
    print(f"\n{'='*60}")
    print(f"TOTAL RIYAD BANK DEALS: {len(deals)}")
    print(f"{'='*60}")
    
    if deals:
        # Get fresh source ID
        db = SessionLocal()
        riyad_source = db.query(Source).filter(Source.name == "Riyad Bank").first()
        source_id = riyad_source.id
        db.close()
        
        save_to_db(deals, source_id)
