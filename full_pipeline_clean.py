"""
Clean pipeline - Scrape -> Structure -> Score -> Insert into DB
"""
import sys
import os
sys.path.insert(0, '/home/anshad/deal-curation-platform')

from datetime import datetime, date
from playwright.sync_api import sync_playwright
import time
import hashlib
import re
from app.database import SessionLocal, RawDeal, StructuredDeal, Rating, Source

def generate_hash(title, merchant, validity):
    normalized = f"{(title or '').lower().strip()}|{(merchant or '').lower().strip()}|{(validity or '').lower().strip()}"
    return hashlib.md5(normalized.encode()).hexdigest()

def parse_date(date_str):
    if not date_str:
        return None
    months = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
        'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12
    }
    try:
        date_str = date_str.replace(',', '').strip()
        parts = date_str.split()
        if len(parts) >= 3:
            day = ''
            month = ''
            year = ''
            for p in parts:
                if p.lower() in months:
                    month = months[p.lower()]
                elif p.isdigit() and len(p) == 4:
                    year = int(p)
                elif p.isdigit():
                    day = int(p)
            if day and month and year:
                return date(year, month, day)
    except:
        pass
    return None

def score_deal(merchant, offer, discount, category):
    score = 5
    reasons = []
    
    pct = 0
    if discount:
        match = re.search(r'(\d+)', discount)
        if match:
            pct = int(match.group(1))
            if pct >= 30:
                score += 3
                reasons.append(f"High discount ({pct}%)")
            elif pct >= 20:
                score += 2
                reasons.append(f"Good discount ({pct}%)")
            elif pct >= 10:
                score += 1
    
    premium_keywords = ['roka', 'mr chow', 'ruya', 'black tap', 'anantara', 'raffles', 
                        'turkish', 'hotel', 'resort', 'clinic', 'hospital']
    if any(kw in merchant.lower() for kw in premium_keywords):
        score += 2
        reasons.append("Premium/quality merchant")
    
    rare_categories = ['travel', 'health', 'automotive', 'education']
    if category.lower() in rare_categories:
        score += 1
        reasons.append("Rare category")
    
    lifestyle_keywords = ['spa', 'salon', 'fitness', 'wellness', 'beauty']
    if any(kw in merchant.lower() or kw in category.lower() for kw in lifestyle_keywords):
        score += 1
        reasons.append("Lifestyle deal")
    
    if pct == 0:
        score -= 1
    
    score = min(10, max(1, score))
    quality = 'good' if score >= 7 else ('mediocre' if score >= 5 else 'bad')
    
    return score, quality, "; ".join(reasons) if reasons else "Standard deal"

def scrape_alrajhi():
    print("Scraping Alrajhi Bank...")
    deals = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.alrajhibank.com.sa/en/Personal/Offers/CardsOffers", timeout=60000)
        time.sleep(5)
        page.wait_for_load_state('networkidle')
        
        offer_cards = page.query_selector_all('a[href*="/Offers/CardsOffers/"]')
        
        seen = set()
        for card in offer_cards:
            try:
                href = card.get_attribute('href')
                if not href or href in seen:
                    continue
                seen.add(href)
                
                parent = card.evaluate_handle('el => el.closest("div")')
                text = parent.inner_text() if parent else ""
                
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                
                merchant = ""
                offer = ""
                discount = ""
                validity = ""
                
                for line in lines:
                    if 'OFF' in line.upper() or '%' in line:
                        offer = line
                        match = re.search(r'(\d+%)', line)
                        if match:
                            discount = match.group(1)
                    elif any(m in line.lower() for m in ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']):
                        validity = line
                    elif len(line) > 3 and line.upper() == line and not merchant:
                        merchant = line
                    elif not merchant and line and 'read more' not in line.lower() and 'view offer' not in line.lower():
                        merchant = line.split()[0] if line.split() else ""
                
                if offer and discount:
                    deals.append({
                        'merchant': merchant or "Restaurant",
                        'offer': offer,
                        'discount': discount,
                        'validity': validity,
                        'category': 'dining',
                        'source': 'Alrajhi Bank',
                        'applicable_cards': 'Alrajhi Bank Cards',
                        'url': f"https://www.alrajhibank.com.sa{href}" if not href.startswith('http') else href
                    })
            except:
                continue
        
        browser.close()
    
    return deals

def scrape_sab():
    print("Scraping SAB Bank...")
    deals = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.sab.com/en/personal/compare-credit-cards/credit-card-special-offers/all-offers/", timeout=60000)
        time.sleep(5)
        page.wait_for_load_state('networkidle')
        
        body_text = page.inner_text('body')
        
        lines = body_text.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            if '- KSA' in line or (line and line.upper() == line and len(line) > 5 and len(line) < 60):
                merchant = line.replace('- KSA', '').strip()
                category = ""
                offer = ""
                discount = ""
                validity = ""
                applicable = "SAB Credit Cards"
                
                for j in range(max(0, i-5), i):
                    prev = lines[j].strip()
                    if prev.lower() in ['shopping', 'dining & groceries', 'travel', 'lifestyle', 'entertainment', 'health', 'automotive']:
                        category = prev
                        break
                
                for j in range(i+1, min(len(lines), i+10)):
                    next_line = lines[j].strip()
                    
                    if 'off' in next_line.lower() or '%' in next_line:
                        offer = next_line
                        match = re.search(r'(\d+%)', next_line)
                        if match:
                            discount = match.group(1)
                    
                    if any(m in next_line.lower() for m in ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']):
                        validity = next_line
                    
                    if 'mada' in next_line.lower():
                        applicable = "SAB Credit Cards & Mada Cards"
                
                if merchant and offer:
                    cat_map = {
                        'dining & groceries': 'dining',
                        'shopping': 'shopping',
                        'travel': 'travel',
                        'lifestyle': 'lifestyle',
                        'entertainment': 'entertainment',
                        'health': 'health',
                        'automotive': 'automotive'
                    }
                    
                    deals.append({
                        'merchant': merchant,
                        'offer': offer,
                        'discount': discount,
                        'validity': validity,
                        'category': cat_map.get(category.lower(), 'other'),
                        'source': 'SAB Bank',
                        'applicable_cards': applicable,
                        'url': 'https://www.sab.com/en/personal/compare-credit-cards/credit-card-special-offers/all-offers/'
                    })
            
            i += 1
        
        browser.close()
    
    return deals

def main():
    print("=" * 70)
    print("DEAL CURATION PIPELINE - Clean Run")
    print("=" * 70)
    
    all_deals = []
    
    alrajhi_deals = scrape_alrajhi()
    print(f"Alrajhi: {len(alrajhi_deals)} deals")
    all_deals.extend(alrajhi_deals)
    
    sab_deals = scrape_sab()
    print(f"SAB: {len(sab_deals)} deals")
    all_deals.extend(sab_deals)
    
    unique_deals = []
    seen_hashes = set()
    for deal in all_deals:
        h = generate_hash(deal['offer'], deal['merchant'], deal['validity'])
        if h not in seen_hashes:
            seen_hashes.add(h)
            unique_deals.append(deal)
    
    print(f"\nTotal unique deals: {len(unique_deals)}")
    
    db = SessionLocal()
    
    try:
        alrajhi_source = db.query(Source).filter(Source.name == "Alrajhi Bank").first()
        sab_source = db.query(Source).filter(Source.name == "SAB Bank").first()
        
        raw_count = 0
        structured_count = 0
        good_count = 0
        mediocre_count = 0
        bad_count = 0
        
        print("\n" + "-" * 70)
        print(f"{'Merchant':<35} {'Discount':<10} {'Score':<8} {'Quality':<10}")
        print("-" * 70)
        
        for i, deal in enumerate(unique_deals, 1):
            content_hash = generate_hash(deal['offer'], deal['merchant'], deal['validity'])
            
            source_id = alrajhi_source.id if deal['source'] == 'Alrajhi Bank' else sab_source.id
            
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
            raw_count += 1
            
            valid_until = parse_date(deal.get('validity'))
            
            discount_type = 'percentage' if '%' in deal.get('discount', '') else 'other'
            
            score, quality, reason = score_deal(
                deal['merchant'],
                deal['offer'],
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
            structured_count += 1
            
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
            elif quality == 'mediocre':
                mediocre_count += 1
            else:
                bad_count += 1
            
            print(f"{deal['merchant'][:35]:<35} {deal.get('discount', 'N/A'):<10} {score}/10     {quality:<10}")
        
        db.commit()
        
        print("\n" + "=" * 70)
        print("PIPELINE COMPLETE!")
        print("=" * 70)
        print(f"Raw deals: {raw_count}")
        print(f"Structured deals: {structured_count}")
        print(f"\nQuality Distribution:")
        print(f"  Good: {good_count}")
        print(f"  Mediocre: {mediocre_count}")
        print(f"  Bad: {bad_count}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
