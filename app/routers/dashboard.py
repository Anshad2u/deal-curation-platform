from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db, RawDeal, StructuredDeal, Rating, Source
from app.models import DashboardStats
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: Session = Depends(get_db)):
    total_raw = db.query(RawDeal).count()
    new_deals = db.query(RawDeal).filter(RawDeal.status == 'new').count()
    total_structured = db.query(StructuredDeal).count()
    
    good_deals = db.query(Rating).filter(Rating.quality_score == 'good').count()
    total_rated = db.query(Rating).count()
    
    return DashboardStats(
        total_deals=total_raw,
        new_deals=new_deals,
        good_deals=good_deals,
        total_structured=total_structured,
        total_rated=total_rated
    )

@router.get("/activity")
async def get_recent_activity(db: Session = Depends(get_db)):
    recent_raw = db.query(RawDeal).order_by(RawDeal.scraped_at.desc()).limit(10).all()
    recent_structured = db.query(StructuredDeal).order_by(StructuredDeal.created_at.desc()).limit(10).all()
    
    activity = []
    for deal in recent_raw:
        activity.append({
            "type": "raw_deal",
            "title": deal.raw_title,
            "source": deal.source.name if deal.source else "Unknown",
            "timestamp": deal.scraped_at.isoformat()
        })
    
    for deal in recent_structured:
        activity.append({
            "type": "structured_deal",
            "title": deal.offer_title,
            "merchant": deal.merchant_name,
            "timestamp": deal.created_at.isoformat()
        })
    
    activity.sort(key=lambda x: x['timestamp'], reverse=True)
    return activity[:20]

@router.get("/sources-status")
async def get_sources_status(db: Session = Depends(get_db)):
    sources = db.query(Source).all()
    result = []
    for source in sources:
        deal_count = db.query(RawDeal).filter(RawDeal.source_id == source.id).count()
        result.append({
            "id": source.id,
            "name": source.name,
            "type": source.type,
            "last_scraped": source.last_scraped_at.isoformat() if source.last_scraped_at else None,
            "deal_count": deal_count,
            "is_active": source.is_active
        })
    return result
