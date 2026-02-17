from abc import ABC, abstractmethod
from typing import List, Dict
import hashlib

class BaseScraper(ABC):
    def __init__(self, source_id: int, source_name: str, source_url: str):
        self.source_id = source_id
        self.source_name = source_name
        self.source_url = source_url
    
    @abstractmethod
    def scrape(self) -> List[Dict]:
        pass
    
    def generate_hash(self, deal: Dict) -> str:
        normalized_title = (deal.get('raw_title') or '').lower().strip()
        normalized_merchant = (deal.get('raw_merchant') or '').lower().strip()
        normalized_validity = (deal.get('raw_validity') or '').lower().strip()
        combined = f"{normalized_title}|{normalized_merchant}|{normalized_validity}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def prepare_deal(self, deal: Dict) -> Dict:
        deal['source_id'] = self.source_id
        deal['content_hash'] = self.generate_hash(deal)
        if 'scraped_url' not in deal:
            deal['scraped_url'] = self.source_url
        return deal
