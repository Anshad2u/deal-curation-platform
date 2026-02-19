"""
Riyad Bank scraper - Extract ALL offers from static HTML (Final)
"""
import sys
sys.path.insert(0, '/home/anshad/deal-curation-platform')

from datetime import datetime, date
import requests
import re
from bs4 import BeautifulSoup
import hashlib
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

def scrape_riyad_static():
    print("Fetching Riyad Bank offers from static HTML...")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    })
    
    url = "https://www.riyadbank.com/personal-banking/credit-cards/offers"
    
    try:
        r = session.get(url, timeout=30)
        print(f"  Status: {r.status_code}, Length: {len(r.text)}")
    except Exception as e:
        print(f"  Error fetching page: {e}")
        return []
    
    soup = BeautifulSoup(r.text, 'html.parser')
    
    all_deals = []
    
    # Find all discount elements first
    discount_elements = soup.find_all('span', class_='discount-percent-text')
    print(f"  Found {len(discount_elements)} discount elements")
    
    for discount_elem in discount_elements:
        discount = discount_elem.get_text(strip=True)
        
        # Skip non-discount values (like S..R amounts)
        if 'SAR' in discount or 'S..R' in discount or discount.replace('.', '').replace(' ', '').isalpha():
            if '%' not in discount:
                continue
        
        # Find the brand name by going up to find a container with rb-brand-name
        merchant = ""
        container = discount_elem
        for _ in range(15):
            container = container.parent
            if container is None:
                break
            
            brand = container.find(class_='rb-brand-name')
            if brand:
                merchant = brand.get_text(strip=True)
                break
        
        if not merchant or len(merchant) < 2:
            continue
        
        # Get validity from container text
        validity = ""
        if container:
            card_text = container.get_text()
            valid_match = re.search(r'[Vv]alid[^:]*:\s*([^\n]+?)(?=\s{2,}|$)', card_text)
            if valid_match:
                validity = valid_match.group(1).strip()[:100]
        
        # Get link
        offer_url = ""
        if container:
            link_elem = container.find('a', href=True)
            if link_elem:
                offer_url = link_elem.get('href', '')
                if offer_url and not offer_url.startswith('http'):
                    offer_url = f"https://www.riyadbank.com{offer_url}"
        
        # Determine category based on merchant name
        category = "other"
        lower_merchant = merchant.lower()
        if any(x in lower_merchant for x in ['restaurant', 'cafe', 'coffee', 'food', 'kitchen', 'grill', 'burger', 'pizza', 'sushi', 'baretto', 'chow', 'ruya', 'crust', 'soul', 'assam', 'roastery', 'labate', 'key caf']):
            category = "dining"
        elif any(x in lower_merchant for x in ['spa', 'beauty', 'salon', 'clinic', 'medical', 'dental', 'savin']):
            category = "lifestyle"
        elif any(x in lower_merchant for x in ['hotel', 'resort', 'travel', 'flight', 'airline', 'anantara', 'vacation']):
            category = "travel"
        elif any(x in lower_merchant for x in ['shop', 'store', 'fashion', 'mall', 'glam', 'moda', 'boutique']):
            category = "shopping"
        elif any(x in lower_merchant for x in ['gym', 'fitness', 'sport', 'round', 'health', 'garden', 'preschool']):
            category = "lifestyle"
        
        # Build offer description
        description = f"{discount} off at {merchant}" if '%' in discount else f"Special offer at {merchant}"
        
        all_deals.append({
            'merchant': merchant,
            'offer': description,
            'discount': discount,
            'validity': validity,
            'category': category,
            'source': 'Riyad Bank',
            'applicable_cards': 'Riyad Bank Credit Cards',
            'url': offer_url or url
        })
    
    # Deduplicate by merchant
    seen = set()
    unique = []
    for d in all_deals:
        h = d['merchant'].lower()
        if h not in seen:
            seen.add(h)
            unique.append(d)
    
    return unique

def save_to_db(deals, source_id):
    print(f"\nSaving {len(deals)} Riyad Bank deals...")
    
    db = SessionLocal()
    
    try:
        good_count = 0
        mediocre_count = 0
        
        for deal in deals:
            content_hash = generate_hash(deal['offer'], deal['merchant'])
            
            existing = db.query(RawDeal).filter(RawDeal.content_hash == content_hash).first()
            if existing:
                continue
            
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
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("RIYAD BANK STATIC HTML SCRAPER (FINAL)")
    print("=" * 60)
    
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
    source_id = riyad_source.id
    db.close()
    
    deals = scrape_riyad_static()
    
    print(f"\n{'='*60}")
    print(f"TOTAL RIYAD BANK DEALS: {len(deals)}")
    print(f"{'='*60}")
    
    if deals:
        print("\nSample deals:")
        for d in deals[:20]:
            print(f"  - {d['merchant']}: {d['discount']} ({d['category']})")
        save_to_db(deals, source_id)
    else:
        print("No deals found.")
