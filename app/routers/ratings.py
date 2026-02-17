from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db, StructuredDeal, Rating
from app.models import RatingCreate
from datetime import datetime

router = APIRouter()

@router.get("/pending")
async def get_pending_ratings(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    deals = db.query(StructuredDeal).outerjoin(Rating).filter(
        Rating.id.is_(None),
        StructuredDeal.is_active == True
    ).limit(limit).all()
    
    return {
        "total": len(deals),
        "deals": [
            {
                "id": d.id,
                "merchant_name": d.merchant_name,
                "offer_title": d.offer_title,
                "description": d.description,
                "discount_value": d.discount_value,
                "category": d.category,
                "valid_until": d.valid_until.isoformat() if d.valid_until else None,
                "applicable_cards": d.applicable_cards
            }
            for d in deals
        ]
    }

@router.post("/deals/{deal_id}/rate")
async def rate_deal(
    deal_id: int,
    quality_score: str,
    reason: Optional[str] = None,
    llm_score: Optional[int] = None,
    llm_reasoning: Optional[str] = None,
    db: Session = Depends(get_db)
):
    deal = db.query(StructuredDeal).filter(StructuredDeal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    if quality_score not in ['good', 'mediocre', 'bad']:
        raise HTTPException(status_code=400, detail="Quality score must be good, mediocre, or bad")
    
    existing_rating = db.query(Rating).filter(Rating.deal_id == deal_id).first()
    if existing_rating:
        existing_rating.quality_score = quality_score
        existing_rating.reason = reason
        existing_rating.llm_score = llm_score
        existing_rating.llm_reasoning = llm_reasoning
        existing_rating.rated_at = datetime.utcnow()
    else:
        rating = Rating(
            deal_id=deal_id,
            quality_score=quality_score,
            reason=reason,
            llm_score=llm_score,
            llm_reasoning=llm_reasoning
        )
        db.add(rating)
    
    db.commit()
    
    return {"success": True, "message": "Rating saved"}

@router.get("/stats")
async def get_rating_stats(db: Session = Depends(get_db)):
    total_good = db.query(Rating).filter(Rating.quality_score == 'good').count()
    total_mediocre = db.query(Rating).filter(Rating.quality_score == 'mediocre').count()
    total_bad = db.query(Rating).filter(Rating.quality_score == 'bad').count()
    total_rated = total_good + total_mediocre + total_bad
    
    return {
        "total_rated": total_rated,
        "good": total_good,
        "mediocre": total_mediocre,
        "bad": total_bad,
        "percentages": {
            "good": round((total_good / total_rated * 100) if total_rated > 0 else 0, 1),
            "mediocre": round((total_mediocre / total_rated * 100) if total_rated > 0 else 0, 1),
            "bad": round((total_bad / total_rated * 100) if total_rated > 0 else 0, 1)
        }
    }

@router.get("/deals/{deal_id}/rating")
async def get_deal_rating(deal_id: int, db: Session = Depends(get_db)):
    rating = db.query(Rating).filter(Rating.deal_id == deal_id).first()
    
    if not rating:
        return {"has_rating": False}
    
    return {
        "has_rating": True,
        "quality_score": rating.quality_score,
        "reason": rating.reason,
        "llm_score": rating.llm_score,
        "llm_reasoning": rating.llm_reasoning,
        "rated_at": rating.rated_at.isoformat()
    }
