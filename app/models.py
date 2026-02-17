from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class SourceBase(BaseModel):
    name: str
    type: str
    url: str
    config_json: Optional[str] = None
    is_active: bool = True

class SourceCreate(SourceBase):
    pass

class Source(SourceBase):
    id: int
    last_scraped_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class RawDealBase(BaseModel):
    raw_title: Optional[str]
    raw_description: Optional[str]
    raw_discount: Optional[str]
    raw_validity: Optional[str]
    raw_merchant: Optional[str]
    raw_image_url: Optional[str]
    raw_terms: Optional[str]
    scraped_url: Optional[str]

class RawDealCreate(RawDealBase):
    source_id: int
    content_hash: str

class RawDeal(RawDealBase):
    id: int
    source_id: int
    scraped_html: Optional[str]
    scraped_at: datetime
    content_hash: str
    status: str
    
    class Config:
        from_attributes = True

class StructuredDealBase(BaseModel):
    merchant_name: str
    offer_title: str
    description: Optional[str]
    discount_value: Optional[str]
    discount_type: Optional[str]
    category: Optional[str]
    valid_from: Optional[date]
    valid_until: Optional[date]
    location: Optional[str]
    applicable_cards: Optional[str]
    terms_conditions: Optional[str]
    promo_code: Optional[str]
    image_url: Optional[str]
    source_url: Optional[str]
    is_active: bool = True

class StructuredDealCreate(StructuredDealBase):
    raw_deal_id: int

class StructuredDeal(StructuredDealBase):
    id: int
    raw_deal_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class RatingBase(BaseModel):
    quality_score: str
    reason: Optional[str]
    llm_score: Optional[int]
    llm_reasoning: Optional[str]

class RatingCreate(RatingBase):
    deal_id: int

class Rating(RatingBase):
    id: int
    deal_id: int
    rated_at: datetime
    
    class Config:
        from_attributes = True

class ProcessingBatchBase(BaseModel):
    name: str
    notes: Optional[str]

class ProcessingBatchCreate(ProcessingBatchBase):
    pass

class ProcessingBatch(ProcessingBatchBase):
    id: int
    status: str
    deals_count: int
    exported_at: datetime
    imported_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class DashboardStats(BaseModel):
    total_deals: int
    new_deals: int
    good_deals: int
    total_structured: int
    total_rated: int

class ExportRequest(BaseModel):
    deal_ids: List[int]

class ImportDeal(BaseModel):
    temp_id: int
    merchant_name: str
    offer_title: str
    description: Optional[str]
    discount_value: Optional[str]
    discount_type: Optional[str]
    category: Optional[str]
    valid_from: Optional[str]
    valid_until: Optional[str]
    location: Optional[str]
    applicable_cards: Optional[str]
    terms_conditions: Optional[str]
    promo_code: Optional[str]

class ImportBatch(BaseModel):
    deals: List[ImportDeal]
