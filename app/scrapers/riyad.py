from typing import List, Dict
from playwright.sync_api import sync_playwright
from .base import BaseScraper
import time

class RiyadBankScraper(BaseScraper):
    def __init__(self, source_id: int):
        super().__init__(
            source_id=source_id,
            source_name="Riyad Bank",
            source_url="https://www.riyadbank.com/personal-banking/credit-cards/offers"
        )
    
    def scrape(self) -> List[Dict]:
        deals = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(self.source_url, timeout=60000)
                time.sleep(3)
                page.wait_for_load_state('networkidle')
                
                offer_elements = page.query_selector_all('.offer-card, .card-offer, [class*="offer"]')
                
                for elem in offer_elements[:50]:
                    deal = self.parse_offer(elem)
                    if deal and deal.get('raw_title'):
                        deal = self.prepare_deal(deal)
                        deals.append(deal)
                
                browser.close()
        except Exception as e:
            print(f"Error scraping Riyad Bank with Playwright: {e}")
            deals = self.scrape_fallback()
        
        return deals
    
    def parse_offer(self, element) -> Dict:
        deal = {}
        try:
            title_elem = element.query_selector('h2, h3, h4, .title, [class*="title"]')
            if title_elem:
                deal['raw_title'] = title_elem.inner_text().strip()
            merchant_elem = element.query_selector('.merchant, .brand, [class*="merchant"]')
            if merchant_elem:
                deal['raw_merchant'] = merchant_elem.inner_text().strip()
            elif title_elem:
                deal['raw_merchant'] = deal.get('raw_title', '')
            desc_elem = element.query_selector('p, .description, [class*="desc"]')
            if desc_elem:
                deal['raw_description'] = desc_elem.inner_text().strip()
            discount_elem = element.query_selector('[class*="discount"], [class*="off"]')
            if discount_elem:
                deal['raw_discount'] = discount_elem.inner_text().strip()
            date_elem = element.query_selector('[class*="valid"], [class*="date"], .validity')
            if date_elem:
                deal['raw_validity'] = date_elem.inner_text().strip()
            img_elem = element.query_selector('img')
            if img_elem:
                deal['raw_image_url'] = img_elem.get_attribute('src') or ''
        except Exception as e:
            pass
        
        return deal
    
    def scrape_fallback(self) -> List[Dict]:
        try:
            import requests
            from bs4 import BeautifulSoup
            
            response = requests.get(self.source_url, timeout=30)
            soup = BeautifulSoup(response.content, 'lxml')
            deals = []
            
            for card in soup.find_all('div', class_=['offer-card', 'card']):
                deal = {}
                title = card.find(['h2', 'h3', 'h4'])
                if title:
                    deal['raw_title'] = title.get_text(strip=True)
                    deal['raw_merchant'] = title.get_text(strip=True)
                    deal = self.prepare_deal(deal)
                    deals.append(deal)
            
            return deals
        except Exception as e:
            print(f"Fallback scraping also failed: {e}")
            return []
