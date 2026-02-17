from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db, Source
from app.models import Source as SourceModel
from app.scrapers.runner import ScraperRunner

router = APIRouter()

@router.get("/")
async def list_sources(db: Session = Depends(get_db)):
    sources = db.query(Source).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "type": s.type,
            "url": s.url,
            "is_active": s.is_active,
            "last_scraped": s.last_scraped_at.isoformat() if s.last_scraped_at else None
        }
        for s in sources
    ]

@router.get("/{source_id}")
async def get_source(source_id: int, db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        return {"error": "Source not found"}
    return {
        "id": source.id,
        "name": source.name,
        "type": source.type,
        "url": source.url,
        "is_active": source.is_active,
        "last_scraped": source.last_scraped_at.isoformat() if source.last_scraped_at else None
    }

@router.post("/{source_id}/scrape")
async def run_scrape(source_id: int, db: Session = Depends(get_db)):
    runner = ScraperRunner(db)
    result = runner.run_scraper(source_id)
    return result
