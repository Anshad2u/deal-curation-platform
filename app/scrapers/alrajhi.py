from typing import List, Dict
import requests
from bs4 import BeautifulSoup
from .base import BaseScraper

class AlrajhiScraper(BaseScraper):
    def __init__(self, source_id: int):
        super().__init__(
            source_id=source_id,
            source_name="Alrajhi Bank",
            source_url="https://www.alrajhibank.com.sa/en/Personal/Offers/CardsOffers"
        )
    
    def scrape(self) -> List[Dict]:
        try:
            response = requests.get(self.source_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'lxml')
            deals = []
            offer_cards = soup.find_all('div', class_='offer-card') or soup.find_all('div', class_='card')
            if not offer_cards:
                offer_cards = soup.find_all('article')
            
            for card in offer_cards:
                deal = self.parse_offer(card)
                if deal and deal.get('raw_title'):
                    deal = self.prepare_deal(deal)
                    deals.append(deal)
            
            if not deals:
                deals = self.parse_offers_alternative(soup)
            
            return deals
        except Exception as e:
            print(f"Error scraping Alrajhi Bank: {e}")
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
        discount_elem = element.find(text=lambda x: x and '%' in str(x))
        if discount_elem:
            deal['raw_discount'] = discount_elem.strip()
        date_elem = element.find('span', class_='date') or element.find(text=lambda x: x and any(month in str(x).lower() for month in ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']))
        if date_elem:
            deal['raw_validity'] = date_elem.strip() if isinstance(date_elem, str) else date_elem.get_text(strip=True)
        img_elem = element.find('img')
        if img_elem and img_elem.get('src'):
            deal['raw_image_url'] = img_elem['src']
        link_elem = element.find('a', href=True)
        if link_elem:
            href = link_elem['href']
            if not href.startswith('http'):
                href = 'https://www.alrajhibank.com.sa' + href
            deal['scraped_url'] = href
        return deal
    
    def parse_offers_alternative(self, soup) -> List[Dict]:
        deals = []
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href', '')
            if '/Offers/' in href and 'CardsOffers' in href:
                title = link.get_text(strip=True)
                if title and len(title) > 3:
                    deal = {
                        'raw_title': title,
                        'raw_merchant': title,
                        'scraped_url': 'https://www.alrajhibank.com.sa' + href if not href.startswith('http') else href
                    }
                    deal = self.prepare_deal(deal)
                    deals.append(deal)
        return deals
