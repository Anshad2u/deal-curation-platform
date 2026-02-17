from typing import List, Dict
import requests
from bs4 import BeautifulSoup
from .base import BaseScraper

class SABBankScraper(BaseScraper):
    def __init__(self, source_id: int):
        super().__init__(
            source_id=source_id,
            source_name="SAB Bank",
            source_url="https://www.sab.com/en/personal/compare-credit-cards/credit-card-special-offers/all-offers/"
        )
    
    def scrape(self) -> List[Dict]:
        try:
            response = requests.get(self.source_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'lxml')
            deals = []
            offer_cards = soup.find_all('div', class_=['offer', 'card', 'special-offer'])
            
            if not offer_cards:
                offer_cards = soup.find_all('article') or soup.find_all('li', class_='offer')
            
            for card in offer_cards:
                deal = self.parse_offer(card)
                if deal and deal.get('raw_title'):
                    deal = self.prepare_deal(deal)
                    deals.append(deal)
            
            if not deals:
                deals = self.parse_offers_generic(soup)
            
            return deals
        except Exception as e:
            print(f"Error scraping SAB Bank: {e}")
            return []
    
    def parse_offer(self, element) -> Dict:
        deal = {}
        title_elem = element.find(['h2', 'h3', 'h4']) or element.find('a', class_='title')
        if title_elem:
            deal['raw_title'] = title_elem.get_text(strip=True)
        merchant_elem = element.find(['h5', 'h6'], class_='merchant') or element.find('span', class_='brand')
        if merchant_elem:
            deal['raw_merchant'] = merchant_elem.get_text(strip=True)
        elif title_elem:
            deal['raw_merchant'] = title_elem.get_text(strip=True)
        desc_elem = element.find('p') or element.find('div', class_='description')
        if desc_elem:
            deal['raw_description'] = desc_elem.get_text(strip=True)
        discount_text = element.find(text=lambda x: x and ('%' in str(x) or 'off' in str(x).lower()))
        if discount_text:
            deal['raw_discount'] = discount_text.strip()
        date_elem = element.find('span', class_='date') or element.find(text=lambda x: x and 'valid' in str(x).lower())
        if date_elem:
            deal['raw_validity'] = date_elem.strip() if isinstance(date_elem, str) else date_elem.get_text(strip=True)
        img_elem = element.find('img')
        if img_elem and img_elem.get('src'):
            deal['raw_image_url'] = img_elem['src']
        link_elem = element.find('a', href=True)
        if link_elem:
            href = link_elem['href']
            if not href.startswith('http'):
                href = 'https://www.sab.com' + href
            deal['scraped_url'] = href
        
        return deal
    
    def parse_offers_generic(self, soup) -> List[Dict]:
        deals = []
        sections = soup.find_all('section')
        for section in sections:
            headings = section.find_all(['h2', 'h3', 'h4'])
            for heading in headings:
                title = heading.get_text(strip=True)
                if title and len(title) > 5 and ('offer' in title.lower() or 'discount' in title.lower() or '%' in title):
                    deal = {
                        'raw_title': title,
                        'raw_merchant': title,
                    }
                    parent = heading.find_parent()
                    if parent:
                        desc = parent.find('p')
                        if desc:
                            deal['raw_description'] = desc.get_text(strip=True)
                    deal = self.prepare_deal(deal)
                    deals.append(deal)
        
        return deals
