from typing import Dict, List
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import RawDeal, Source
from app.scrapers.alrajhi import AlrajhiScraper
from app.scrapers.riyad import RiyadBankScraper
from app.scrapers.sab import SABBankScraper

class ScraperRunner:
    def __init__(self, db: Session):
        self.db = db
    
    def get_scraper(self, source: Source):
        scrapers = {
            "Alrajhi Bank": AlrajhiScraper,
            "Riyad Bank": RiyadBankScraper,
            "SAB Bank": SABBankScraper
        }
        scraper_class = scrapers.get(source.name)
        if scraper_class:
            return scraper_class(source.id)
        return None
    
    def run_scraper(self, source_id: int) -> Dict:
        source = self.db.query(Source).filter(Source.id == source_id).first()
        if not source:
            return {"success": False, "error": "Source not found"}
        
        scraper = self.get_scraper(source)
        if not scraper:
            return {"success": False, "error": f"No scraper for {source.name}"}
        
        try:
            deals_data = scraper.scrape()
            
            new_count = 0
            duplicate_count = 0
            error_count = 0
            
            for deal_data in deals_data:
                content_hash = deal_data.get('content_hash')
                existing = self.db.query(RawDeal).filter(
                    RawDeal.content_hash == content_hash
                ).first()
                
                if existing:
                    duplicate_count += 1
                    continue
                
                raw_deal = RawDeal(
                    source_id=source.id,
                    raw_title=deal_data.get('raw_title'),
                    raw_description=deal_data.get('raw_description'),
                    raw_discount=deal_data.get('raw_discount'),
                    raw_validity=deal_data.get('raw_validity'),
                    raw_merchant=deal_data.get('raw_merchant'),
                    raw_image_url=deal_data.get('raw_image_url'),
                    raw_terms=deal_data.get('raw_terms'),
                    scraped_url=deal_data.get('scraped_url'),
                    content_hash=content_hash,
                    status='new'
                )
                self.db.add(raw_deal)
                new_count += 1
            
            source.last_scraped_at = datetime.utcnow()
            self.db.commit()
            
            return {
                "success": True,
                "source": source.name,
                "total_found": len(deals_data),
                "new_deals": new_count,
                "duplicates": duplicate_count
            }
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}
