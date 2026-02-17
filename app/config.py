import os
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'data', 'deals.db')}"

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-abc123xyz")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"

DEAL_CATEGORIES = [
    "dining",
    "shopping", 
    "travel",
    "lifestyle",
    "entertainment",
    "health",
    "automotive",
    "education",
    "other"
]

DISCOUNT_TYPES = [
    "percentage",
    "fixed_amount",
    "buy_x_get_y",
    "other"
]

QUALITY_SCORES = ["good", "mediocre", "bad"]

DEAL_STATUSES = ["new", "processing", "processed", "duplicate", "error"]

BATCH_STATUSES = ["created", "processing", "completed"]

SOURCES = {
    "alrajhi": {
        "name": "Alrajhi Bank",
        "type": "website",
        "url": "https://www.alrajhibank.com.sa/en/Personal/Offers/CardsOffers",
        "is_active": True
    },
    "riyad": {
        "name": "Riyad Bank",
        "type": "website", 
        "url": "https://www.riyadbank.com/personal-banking/credit-cards/offers",
        "is_active": True
    },
    "sab": {
        "name": "SAB Bank",
        "type": "website",
        "url": "https://www.sab.com/en/personal/compare-credit-cards/credit-card-special-offers/all-offers/",
        "is_active": True
    }
}

LLM_PROMPT_TEMPLATE = """You are a data extraction specialist. Convert the following unstructured deal data into a structured JSON format.

INPUT FORMAT:
An array of deals with these fields:
- temp_id: Unique identifier for this deal
- raw_title: Title text
- raw_description: Description text
- raw_merchant: Merchant name
- raw_validity: Validity period text
- source: Source name

OUTPUT FORMAT:
Return a JSON array with the same number of deals, each containing:
{{
  "temp_id": <same as input>,
  "merchant_name": "Clean merchant name",
  "offer_title": "Clean offer title",
  "description": "Full description",
  "discount_value": "e.g., 20% or SAR 50",
  "discount_type": "percentage|fixed_amount|buy_x_get_y|other",
  "category": "dining|shopping|travel|lifestyle|entertainment|health|automotive|education|other",
  "valid_from": "YYYY-MM-DD or null",
  "valid_until": "YYYY-MM-DD or null",
  "location": "Location if specified, or null",
  "applicable_cards": "e.g., All Credit Cards, Mada Cards, Specific Card Name",
  "terms_conditions": "Terms text or null",
  "promo_code": "Promo code if mentioned, or null"
}}

RULES:
1. Parse dates from text (e.g., "Valid until December 31, 2026" → "2026-12-31")
2. Extract discount value and type from description
3. Choose the most appropriate category
4. Keep null for fields not found in the text
5. Return ONLY valid JSON, no markdown

DEALS TO PROCESS:
{{deals_json}}
"""
