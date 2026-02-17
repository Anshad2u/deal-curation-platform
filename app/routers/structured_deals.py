from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db, StructuredDeal, Rating
from app.models import StructuredDeal as StructuredDealModel, StructuredDealCreate
from datetime import datetime
import json

router = APIRouter()

@router.get("/")
async def list_deals(
    category: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(StructuredDeal)
    
    if category:
        query = query.filter(StructuredDeal.category == category)
    if search:
        query = query.filter(
            (StructuredDeal.merchant_name.ilike(f'%{search}%')) |
            (StructuredDeal.offer_title.ilike(f'%{search}%'))
        )
    
    total = query.count()
    deals = query.order_by(StructuredDeal.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "deals": [
            {
                "id": d.id,
                "merchant_name": d.merchant_name,
                "offer_title": d.offer_title,
                "description": d.description,
                "discount_value": d.discount_value,
                "discount_type": d.discount_type,
                "category": d.category,
                "valid_from": d.valid_from.isoformat() if d.valid_from else None,
                "valid_until": d.valid_until.isoformat() if d.valid_until else None,
                "location": d.location,
                "applicable_cards": d.applicable_cards,
                "terms_conditions": d.terms_conditions,
                "promo_code": d.promo_code,
                "image_url": d.image_url,
                "source_url": d.source_url,
                "is_active": d.is_active,
                "has_rating": d.rating is not None if hasattr(d, 'rating') else False,
                "created_at": d.created_at.isoformat()
            }
            for d in deals
        ]
    }

@router.get("/{deal_id}")
async def get_deal(deal_id: int, db: Session = Depends(get_db)):
    deal = db.query(StructuredDeal).filter(StructuredDeal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    return {
        "id": deal.id,
        "merchant_name": deal.merchant_name,
        "offer_title": deal.offer_title,
        "description": deal.description,
        "discount_value": deal.discount_value,
        "discount_type": deal.discount_type,
        "category": deal.category,
        "valid_from": deal.valid_from.isoformat() if deal.valid_from else None,
        "valid_until": deal.valid_until.isoformat() if deal.valid_until else None,
        "location": deal.location,
        "applicable_cards": deal.applicable_cards,
        "terms_conditions": deal.terms_conditions,
        "promo_code": deal.promo_code,
        "image_url": deal.image_url,
        "source_url": deal.source_url,
        "is_active": deal.is_active,
        "created_at": deal.created_at.isoformat(),
        "updated_at": deal.updated_at.isoformat()
    }

@router.put("/{deal_id}")
async def update_deal(
    deal_id: int,
    merchant_name: str = None,
    offer_title: str = None,
    description: str = None,
    discount_value: str = None,
    category: str = None,
    applicable_cards: str = None,
    terms_conditions: str = None,
    promo_code: str = None,
    is_active: bool = None,
    db: Session = Depends(get_db)
):
    deal = db.query(StructuredDeal).filter(StructuredDeal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    if merchant_name is not None:
        deal.merchant_name = merchant_name
    if offer_title is not None:
        deal.offer_title = offer_title
    if description is not None:
        deal.description = description
    if discount_value is not None:
        deal.discount_value = discount_value
    if category is not None:
        deal.category = category
    if applicable_cards is not None:
        deal.applicable_cards = applicable_cards
    if terms_conditions is not None:
        deal.terms_conditions = terms_conditions
    if promo_code is not None:
        deal.promo_code = promo_code
    if is_active is not None:
        deal.is_active = is_active
    
    deal.updated_at = datetime.utcnow()
    db.commit()
    
    return {"success": True, "message": "Deal updated"}

@router.delete("/{deal_id}")
async def delete_deal(deal_id: int, db: Session = Depends(get_db)):
    deal = db.query(StructuredDeal).filter(StructuredDeal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    db.delete(deal)
    db.commit()
    
    return {"success": True, "message": "Deal deleted"}

@router.post("/export")
async def export_deals(
    category: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(StructuredDeal)
    if category:
        query = query.filter(StructuredDeal.category == category)
    
    deals = query.all()
    
    return {
        "export_date": datetime.utcnow().isoformat(),
        "total": len(deals),
        "deals": [
            {
                "merchant_name": d.merchant_name,
                "offer_title": d.offer_title,
                "description": d.description,
                "discount_value": d.discount_value,
                "category": d.category,
                "valid_from": d.valid_from.isoformat() if d.valid_from else None,
                "valid_until": d.valid_until.isoformat() if d.valid_until else None,
                "applicable_cards": d.applicable_cards,
                "promo_code": d.promo_code
            }
            for d in deals
        ]
    }
