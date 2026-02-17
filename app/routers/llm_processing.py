from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db, RawDeal, StructuredDeal, ProcessingBatch, BatchDeal
from app.models import ImportBatch
from datetime import datetime
from typing import List
import json
import os

router = APIRouter()

EXPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'exports')

@router.post("/batches")
async def create_batch(
    raw_deal_ids: List[int],
    name: str = None,
    db: Session = Depends(get_db)
):
    deals = db.query(RawDeal).filter(RawDeal.id.in_(raw_deal_ids)).all()
    
    if not deals:
        raise HTTPException(status_code=400, detail="No deals found")
    
    batch_name = name or f"Batch {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
    
    batch = ProcessingBatch(
        name=batch_name,
        status='created',
        deals_count=len(deals)
    )
    db.add(batch)
    db.flush()
    
    for deal in deals:
        batch_deal = BatchDeal(
            batch_id=batch.id,
            raw_deal_id=deal.id
        )
        db.add(batch_deal)
        deal.status = 'processing'
    
    db.commit()
    
    return {
        "batch_id": batch.id,
        "name": batch.name,
        "deals_count": batch.deals_count
    }

@router.get("/batches")
async def list_batches(db: Session = Depends(get_db)):
    batches = db.query(ProcessingBatch).order_by(ProcessingBatch.exported_at.desc()).all()
    return [
        {
            "id": b.id,
            "name": b.name,
            "status": b.status,
            "deals_count": b.deals_count,
            "exported_at": b.exported_at.isoformat(),
            "imported_at": b.imported_at.isoformat() if b.imported_at else None
        }
        for b in batches
    ]

@router.get("/batches/{batch_id}")
async def get_batch(batch_id: int, db: Session = Depends(get_db)):
    batch = db.query(ProcessingBatch).filter(ProcessingBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    batch_deals = db.query(BatchDeal).filter(BatchDeal.batch_id == batch_id).all()
    raw_deal_ids = [bd.raw_deal_id for bd in batch_deals]
    raw_deals = db.query(RawDeal).filter(RawDeal.id.in_(raw_deal_ids)).all()
    
    export_data = {
        "batch_id": batch_id,
        "export_date": batch.exported_at.isoformat(),
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
            for idx, d in enumerate(raw_deals, 1)
        ]
    }
    
    return export_data

@router.post("/batches/{batch_id}/import")
async def import_batch(
    batch_id: int,
    import_data: ImportBatch,
    db: Session = Depends(get_db)
):
    batch = db.query(ProcessingBatch).filter(ProcessingBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    batch_deals = db.query(BatchDeal).filter(BatchDeal.batch_id == batch_id).all()
    raw_deal_map = {bd.raw_deal_id: bd for bd in batch_deals}
    
    imported_count = 0
    for deal_data in import_data.deals:
        batch_deal = list(raw_deal_map.values())[deal_data.temp_id - 1] if deal_data.temp_id <= len(batch_deals) else None
        
        if not batch_deal:
            continue
        
        valid_from = None
        if deal_data.valid_from:
            try:
                valid_from = datetime.strptime(deal_data.valid_from, '%Y-%m-%d').date()
            except:
                pass
        
        valid_until = None
        if deal_data.valid_until:
            try:
                valid_until = datetime.strptime(deal_data.valid_until, '%Y-%m-%d').date()
            except:
                pass
        
        structured_deal = StructuredDeal(
            raw_deal_id=batch_deal.raw_deal_id,
            merchant_name=deal_data.merchant_name,
            offer_title=deal_data.offer_title,
            description=deal_data.description,
            discount_value=deal_data.discount_value,
            discount_type=deal_data.discount_type,
            category=deal_data.category,
            valid_from=valid_from,
            valid_until=valid_until,
            location=deal_data.location,
            applicable_cards=deal_data.applicable_cards,
            terms_conditions=deal_data.terms_conditions,
            promo_code=deal_data.promo_code,
            is_active=True
        )
        db.add(structured_deal)
        db.flush()
        
        batch_deal.structured_deal_id = structured_deal.id
        
        raw_deal = db.query(RawDeal).filter(RawDeal.id == batch_deal.raw_deal_id).first()
        if raw_deal:
            raw_deal.status = 'processed'
        
        imported_count += 1
    
    batch.status = 'completed'
    batch.imported_at = datetime.utcnow()
    db.commit()
    
    return {
        "success": True,
        "imported_count": imported_count
    }
