#!/bin/bash

echo "Starting Deal Curation Platform..."
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "Installing Playwright browsers..."
playwright install chromium

echo ""
echo "Starting server on http://localhost:8000"
echo "Default login: admin / admin123"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
