from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
import os

from app.config import SOURCES, SECRET_KEY
from app.database import create_tables, get_db, SessionLocal, Source
from app.auth import create_default_user, get_current_user
from app.models import User

from app.routers import dashboard, scrapers, raw_deals, llm_processing, structured_deals, ratings, auth

app = FastAPI(title="Deal Curation Platform")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(scrapers.router, prefix="/api/sources", tags=["scrapers"])
app.include_router(raw_deals.router, prefix="/api/raw-deals", tags=["raw-deals"])
app.include_router(llm_processing.router, prefix="/api/llm", tags=["llm"])
app.include_router(structured_deals.router, prefix="/api/deals", tags=["deals"])
app.include_router(ratings.router, prefix="/api/ratings", tags=["ratings"])

@app.on_event("startup")
async def startup_event():
    create_tables()
    db = SessionLocal()
    try:
        create_default_user(db)
        for source_key, source_data in SOURCES.items():
            existing = db.query(Source).filter(Source.name == source_data["name"]).first()
            if not existing:
                source = Source(**source_data)
                db.add(source)
        db.commit()
        print("Database initialized and sources seeded")
    finally:
        db.close()

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return RedirectResponse(url="/dashboard")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

@app.get("/scrapers", response_class=HTMLResponse)
async def scrapers_page(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("scrapers.html", {"request": request, "user": user})

@app.get("/raw-deals", response_class=HTMLResponse)
async def raw_deals_page(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("raw-deals.html", {"request": request, "user": user})

@app.get("/llm-processing", response_class=HTMLResponse)
async def llm_processing_page(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("llm-processing.html", {"request": request, "user": user})

@app.get("/deals", response_class=HTMLResponse)
async def deals_page(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("structured-deals.html", {"request": request, "user": user})

@app.get("/rate", response_class=HTMLResponse)
async def rate_page(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("ratings.html", {"request": request, "user": user})
