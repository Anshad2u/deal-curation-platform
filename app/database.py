from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, Date, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Source(Base):
    __tablename__ = "sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    url = Column(String, nullable=False)
    config_json = Column(Text)
    is_active = Column(Boolean, default=True)
    last_scraped_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    raw_deals = relationship("RawDeal", back_populates="source")

class RawDeal(Base):
    __tablename__ = "raw_deals"
    
    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"))
    raw_title = Column(String)
    raw_description = Column(Text)
    raw_discount = Column(String)
    raw_validity = Column(String)
    raw_merchant = Column(String)
    raw_image_url = Column(String)
    raw_terms = Column(Text)
    scraped_url = Column(String)
    scraped_html = Column(Text)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    content_hash = Column(String, index=True)
    status = Column(String, default="new")
    
    source = relationship("Source", back_populates="raw_deals")
    structured_deal = relationship("StructuredDeal", back_populates="raw_deal", uselist=False)
    batch_deals = relationship("BatchDeal", back_populates="raw_deal")

class StructuredDeal(Base):
    __tablename__ = "structured_deals"
    
    id = Column(Integer, primary_key=True, index=True)
    raw_deal_id = Column(Integer, ForeignKey("raw_deals.id"))
    merchant_name = Column(String, nullable=False)
    offer_title = Column(String, nullable=False)
    description = Column(Text)
    discount_value = Column(String)
    discount_type = Column(String)
    category = Column(String)
    valid_from = Column(Date)
    valid_until = Column(Date)
    location = Column(String)
    applicable_cards = Column(String)
    terms_conditions = Column(Text)
    promo_code = Column(String)
    image_url = Column(String)
    source_url = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    raw_deal = relationship("RawDeal", back_populates="structured_deal")
    rating = relationship("Rating", back_populates="deal", uselist=False)

class Rating(Base):
    __tablename__ = "ratings"
    
    id = Column(Integer, primary_key=True, index=True)
    deal_id = Column(Integer, ForeignKey("structured_deals.id"))
    quality_score = Column(String, nullable=False)
    reason = Column(Text)
    llm_score = Column(Integer)
    llm_reasoning = Column(Text)
    rated_at = Column(DateTime, default=datetime.utcnow)
    
    deal = relationship("StructuredDeal", back_populates="rating")

class ProcessingBatch(Base):
    __tablename__ = "processing_batches"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    status = Column(String, default="created")
    deals_count = Column(Integer)
    exported_at = Column(DateTime, default=datetime.utcnow)
    imported_at = Column(DateTime)
    notes = Column(Text)
    
    batch_deals = relationship("BatchDeal", back_populates="batch")

class BatchDeal(Base):
    __tablename__ = "batch_deals"
    
    batch_id = Column(Integer, ForeignKey("processing_batches.id"), primary_key=True)
    raw_deal_id = Column(Integer, ForeignKey("raw_deals.id"), primary_key=True)
    structured_deal_id = Column(Integer, ForeignKey("structured_deals.id"))
    
    batch = relationship("ProcessingBatch", back_populates="batch_deals")
    raw_deal = relationship("RawDeal", back_populates="batch_deals")
