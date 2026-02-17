"""
Full pipeline: Scrape -> Structure -> Score -> Insert into DB
"""
import sys
import os
sys.path.insert(0, '/home/anshad/deal-curation-platform')

from datetime import datetime
from playwright.sync_api import sync_playwright
import time
import hashlib
from app.database import SessionLocal, RawDeal, StructuredDeal, Rating, Source

def generate_hash(title, merchant, validity):
    normalized = f"{(title or '').lower().strip()}|{(merchant or '').lower().strip()}|{(validity or '').lower().strip()}"
    return hashlib.md5(normalized.encode()).hexdigest()

def parse_date(date_str):
    if not date_str:
        return None
    date_str = date_str.strip()
    months = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
        'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12
    }
    try:
        parts = date_str.replace(',', '').split()
        if len(parts) >= 3:
            day = int(parts[1] if parts[0] in months else parts[0])
            month_str = parts[0] if parts[0] in months else parts[1]
            month = months.get(month_str.lower(), 1)
            year = int(parts[-1])
            return f"{year}-{month:02d}-{day:02d}"
    except:
        pass
    return None

def score_deal(merchant, offer, discount, category):
    score = 5
    reasons = []
    
    if discount:
        try:
            pct = int(discount.replace('%', '').replace('off', '').strip())
            if pct >= 30:
                score += 3
                reasons.append(f"High discount ({pct}%)")
            elif pct >= 20:
                score += 2
                reasons.append(f"Good discount ({pct}%)")
            elif pct >= 10:
                score += 1
        except:
            pass
    
    premium_merchants = ['roka', 'mr chow', 'ruya', 'black tap', 'anantara', 'raffles', 'turkish airline']
    if any(p in merchant.lower() for p in premium_merchants):
        score += 2
        reasons.append("Premium brand")
    
    lifestyle_merchants = ['clinic', 'spa', 'salon', 'fitness', 'pilates', 'hotel', 'resort']
    if any(l in merchant.lower() or l in category.lower() for l in lifestyle_merchants):
        score += 1
        reasons.append("Lifestyle deal")
    
    rare_categories = ['travel', 'health', 'automotive', 'education']
    if category.lower() in rare_categories:
        score += 1
        reasons.append("Rare category")
    
    score = min(10, max(1, score))
    quality = 'good' if score >= 7 else ('mediocre' if score >= 4 else 'bad')
    
    return score, quality, "; ".join(reasons) if reasons else "Standard deal"

def scrape_alrajhi_full():
    print("Scraping Alrajhi Bank...")
    deals = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.alrajhibank.com.sa/en/Personal/Offers/CardsOffers", timeout=60000)
        time.sleep(5)
        page.wait_for_load_state('networkidle')
        
        body_text = page.inner_text('body')
        lines = [l.strip() for l in body_text.split('\n') if l.strip()]
        
        i = 0
        while i < len(lines):
            line = lines[i]
            if 'OFF' in line.upper() or '%' in line:
                merchant = ""
                offer_text = line
                validity = ""
                
                for j in range(max(0, i-3), i):
                    prev = lines[j]
                    if prev and not any(x in prev.lower() for x in ['skip', 'sign', 'personal', 'business', 'accounts', 'cards', 'finance']):
                        merchant = prev
                        break
                
                for j in range(i+1, min(len(lines), i+5)):
                    next_line = lines[j]
                    if any(m in next_line.lower() for m in ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']):
                        validity = next_line
                        break
                
                if not merchant:
                    merchant = line.split()[0] if line.split() else "Unknown"
                
                discount = ""
                if '%' in line:
                    for word in line.split():
                        if '%' in word:
                            discount = word
                            break
                
                deals.append({
                    'merchant': merchant.strip(),
                    'offer': offer_text.strip(),
                    'discount': discount.strip(),
                    'validity': validity.strip(),
                    'category': 'dining',
                    'source': 'Alrajhi Bank',
                    'applicable_cards': 'Alrajhi Bank Cards'
                })
            i += 1
        
        browser.close()
    
    return deals

def scrape_sab_full():
    print("Scraping SAB Bank...")
    deals = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.sab.com/en/personal/compare-credit-cards/credit-card-special-offers/all-offers/", timeout=60000)
        time.sleep(5)
        page.wait_for_load_state('networkidle')
        
        body_text = page.inner_text('body')
        lines = [l.strip() for l in body_text.split('\n') if l.strip()]
        
        current_category = ""
        i = 0
        while i < len(lines):
            line = lines[i]
            
            if line.lower() in ['shopping', 'dining & groceries', 'travel', 'lifestyle', 'entertainment', 'health', 'automotive']:
                current_category = line
                i += 1
                continue
            
            if 'off' in line.lower() or '%' in line:
                merchant = ""
                offer_text = line
                validity = ""
                
                for j in range(max(0, i-3), i):
                    prev = lines[j]
                    if prev and prev.lower() not in ['all', 'dining & groceries', 'shopping', 'travel', 'lifestyle', 'browse by category', 'browse by country']:
                        if '- KSA' in prev or any(c.isupper() for c in prev[:3]):
                            merchant = prev.replace('- KSA', '').strip()
                            break
                
                if not merchant:
                    merchant = current_category
                
                for j in range(i+1, min(len(lines), i+8)):
                    next_line = lines[j]
                    if any(m in next_line.lower() for m in ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']):
                        validity = next_line
                        break
                
                discount = ""
                if '%' in line:
                    import re
                    match = re.search(r'(\d+%)', line)
                    if match:
                        discount = match.group(1)
                
                applicable = "SAB Credit Cards"
                for j in range(i, min(len(lines), i+10)):
                    if 'mada' in lines[j].lower():
                        applicable = "SAB Credit Cards & Mada Cards"
                        break
                
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
                    'merchant': merchant.strip(),
                    'offer': offer_text.strip(),
                    'discount': discount.strip(),
                    'validity': validity.strip(),
                    'category': cat_map.get(current_category.lower(), 'other'),
                    'source': 'SAB Bank',
                    'applicable_cards': applicable
                })
            
            i += 1
        
        browser.close()
    
    return deals

def main():
    print("=" * 60)
    print("DEAL CURATION PIPELINE")
    print("=" * 60)
    
    all_deals = []
    all_deals.extend(scrape_alrajhi_full())
    all_deals.extend(scrape_sab_full())
    
    print(f"\nTotal deals scraped: {len(all_deals)}")
    
    db = SessionLocal()
    
    try:
        alrajhi_source = db.query(Source).filter(Source.name == "Alrajhi Bank").first()
        sab_source = db.query(Source).filter(Source.name == "SAB Bank").first()
        
        raw_count = 0
        structured_count = 0
        
        for i, deal in enumerate(all_deals, 1):
            content_hash = generate_hash(deal['merchant'], deal['merchant'], deal['validity'])
            
            existing = db.query(RawDeal).filter(RawDeal.content_hash == content_hash).first()
            if existing:
                continue
            
            source_id = alrajhi_source.id if deal['source'] == 'Alrajhi Bank' else sab_source.id
            
            raw_deal = RawDeal(
                source_id=source_id,
                raw_title=deal['offer'],
                raw_description=deal['offer'],
                raw_discount=deal['discount'],
                raw_validity=deal['validity'],
                raw_merchant=deal['merchant'],
                content_hash=content_hash,
                status='processed'
            )
            db.add(raw_deal)
            db.flush()
            raw_count += 1
            
            valid_from = None
            valid_until = parse_date(deal['validity'])
            
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
                offer_title=deal['offer'][:200] if len(deal['offer']) > 200 else deal['offer'],
                description=deal['offer'],
                discount_value=deal.get('discount', ''),
                discount_type=discount_type,
                category=deal.get('category', 'other'),
                valid_from=valid_from,
                valid_until=valid_until,
                applicable_cards=deal.get('applicable_cards', 'All Cards'),
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
                llm_reasoning=f"Auto-scored: {reason}"
            )
            db.add(rating)
            
            print(f"  [{i}/{len(all_deals)}] {deal['merchant'][:30]:30} | {deal.get('discount', 'N/A'):8} | Score: {score}/10 | {quality}")
        
        db.commit()
        
        print("\n" + "=" * 60)
        print("PIPELINE COMPLETE!")
        print("=" * 60)
        print(f"Raw deals inserted: {raw_count}")
        print(f"Structured deals: {structured_count}")
        print(f"Auto-rated: {structured_count}")
        
        good = db.query(Rating).filter(Rating.quality_score == 'good').count()
        mediocre = db.query(Rating).filter(Rating.quality_score == 'mediocre').count()
        bad = db.query(Rating).filter(Rating.quality_score == 'bad').count()
        
        print(f"\nQuality Distribution:")
        print(f"  Good: {good}")
        print(f"  Mediocre: {mediocre}")
        print(f"  Bad: {bad}")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
