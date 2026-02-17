from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db, RawDeal, Source
from app.models import ExportRequest
import json
from datetime import datetime
import uuid

router = APIRouter()

@router.get("/")
async def list_raw_deals(
    source_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(RawDeal)
    
    if source_id:
        query = query.filter(RawDeal.source_id == source_id)
    if status:
        query = query.filter(RawDeal.status == status)
    
    total = query.count()
    deals = query.order_by(RawDeal.scraped_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "deals": [
            {
                "id": d.id,
                "source_id": d.source_id,
                "source_name": d.source.name if d.source else None,
                "raw_title": d.raw_title,
                "raw_merchant": d.raw_merchant,
                "raw_discount": d.raw_discount,
                "raw_validity": d.raw_validity,
                "raw_description": d.raw_description,
                "raw_image_url": d.raw_image_url,
                "scraped_url": d.scraped_url,
                "status": d.status,
                "scraped_at": d.scraped_at.isoformat() if d.scraped_at else None
            }
            for d in deals
        ]
    }

@router.get("/{deal_id}")
async def get_raw_deal(deal_id: int, db: Session = Depends(get_db)):
    deal = db.query(RawDeal).filter(RawDeal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    return {
        "id": deal.id,
        "source_id": deal.source_id,
        "source_name": deal.source.name if deal.source else None,
        "raw_title": deal.raw_title,
        "raw_description": deal.raw_description,
        "raw_discount": deal.raw_discount,
        "raw_validity": deal.raw_validity,
        "raw_merchant": deal.raw_merchant,
        "raw_image_url": deal.raw_image_url,
        "raw_terms": deal.raw_terms,
        "scraped_url": deal.scraped_url,
        "scraped_html": deal.scraped_html,
        "status": deal.status,
        "content_hash": deal.content_hash,
        "scraped_at": deal.scraped_at.isoformat() if deal.scraped_at else None
    }

@router.post("/{deal_id}/duplicate")
async def mark_duplicate(deal_id: int, db: Session = Depends(get_db)):
    deal = db.query(RawDeal).filter(RawDeal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    deal.status = 'duplicate'
    db.commit()
    return {"success": True, "message": "Deal marked as duplicate"}

@router.post("/export")
async def export_deals(request: ExportRequest, db: Session = Depends(get_db)):
    deals = db.query(RawDeal).filter(RawDeal.id.in_(request.deal_ids)).all()
    
    export_data = {
        "batch_id": str(uuid.uuid4()),
        "export_date": datetime.utcnow().isoformat(),
        "deals": [
            {
                "temp_id": idx,
                "raw_title": d.raw_title,
                "raw_description": d.raw_description,
                "raw_merchant": d.raw_merchant,
                "raw_discount": d.raw_discount,
                "raw_validity": d.raw_validity,
                "raw_terms": d.raw_terms,
                "source": d.source.name if d.source else "Unknown"
            }
            for idx, d in enumerate(deals, 1)
        ]
    }
    
    for deal in deals:
        deal.status = 'processing'
    db.commit()
    
    return export_data
