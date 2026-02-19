"""
Re-score all existing deals with new popular-brand-focused logic
"""
import sys
sys.path.insert(0, '/home/anshad/deal-curation-platform')

from app.database import SessionLocal, StructuredDeal, Rating
from app.config import score_deal

def rescore_all():
    db = SessionLocal()
    
    deals = db.query(StructuredDeal).all()
    print(f"Re-scoring {len(deals)} deals...")
    
    good_count = 0
    mediocre_count = 0
    bad_count = 0
    
    for deal in deals:
        score, quality, reason = score_deal(
            deal.merchant_name,
            deal.discount_value,
            deal.category
        )
        
        rating = db.query(Rating).filter(Rating.deal_id == deal.id).first()
        if rating:
            rating.llm_score = score
            rating.quality_score = quality
            rating.reason = reason
            rating.llm_reasoning = reason
        else:
            rating = Rating(
                deal_id=deal.id,
                quality_score=quality,
                reason=reason,
                llm_score=score,
                llm_reasoning=reason
            )
            db.add(rating)
        
        if quality == 'good':
            good_count += 1
        elif quality == 'mediocre':
            mediocre_count += 1
        else:
            bad_count += 1
        
        print(f"  {deal.merchant_name[:40]:<40} {deal.discount_value or 'N/A':<8} -> {score}/10 {quality}")
    
    db.commit()
    db.close()
    
    print(f"\n{'='*60}")
    print("RE-SCORING COMPLETE!")
    print(f"{'='*60}")
    print(f"Good: {good_count}")
    print(f"Mediocre: {mediocre_count}")
    print(f"Bad: {bad_count}")

if __name__ == "__main__":
    rescore_all()
