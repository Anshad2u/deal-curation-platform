# Deal Curation Platform

A web-based dashboard to scrape, curate, and rate deals from multiple sources (bank websites, Telegram). Features manual LLM processing workflow and quality rating system.

## Features

- **Multi-source Scraping**: Scrape deals from Alrajhi Bank, Riyad Bank, SAB Bank (more can be added)
- **Raw Deals Queue**: View and manage unstructured scraped data
- **LLM Processing Workflow**: Export deals to JSON, process with ChatGPT/Claude, import structured data
- **Deal Database**: Search and filter structured deals
- **Rating System**: Rate deals as Good/Mediocre/Bad with reasons
- **Deduplication**: Automatic detection of duplicate deals
- **Dashboard**: Overview of all deals and statistics

## Tech Stack

- **Backend**: Python 3.8+ with FastAPI
- **Database**: SQLite
- **Frontend**: Vanilla JavaScript, HTML, CSS
- **Scraping**: requests, BeautifulSoup, Playwright

## Installation

### 1. Clone or Navigate to Project

```bash
cd /home/anshad/deal-curation-platform
```

### 2. Create Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Playwright Browsers (for JS-heavy sites)

```bash
playwright install
```

## Running the Application

### Start the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Access the Dashboard

Open your browser and go to: **http://localhost:8000**

### Default Login Credentials

- **Username**: `admin`
- **Password**: `admin123`

**⚠️ Important**: Change the default password after first login!

## Usage Guide

### 1. Dashboard

The dashboard shows:
- Total raw deals scraped
- New deals waiting to be processed
- Good quality deals
- Total structured deals
- Recent activity

### 2. Scrapers Management

1. Go to **Scrapers** page
2. Click **🔍 Scrape** button next to any source
3. Wait for scraping to complete (may take 10-60 seconds)
4. View results showing new deals and duplicates

**Available Scrapers:**
- Alrajhi Bank
- Riyad Bank (uses Playwright for JS-heavy site)
- SAB Bank

### 3. Raw Deals Queue

1. Go to **Raw Deals** page
2. Filter by status (New, Processing, Processed, Duplicate)
3. Select deals using checkboxes
4. Click **📤 Export Selected** to download JSON
5. Mark deals as duplicate if needed

### 4. LLM Processing Workflow

This is a manual workflow where you use ChatGPT or Claude to structure the data:

#### Step 1: Export
1. Go to **LLM Processing** page
2. Select deals with status "New"
3. Enter a batch name (optional)
4. Click **📤 Export for LLM**
5. A JSON file will download

#### Step 2: Process with LLM
1. Open the LLM Processing page
2. Copy the **LLM Prompt Template** shown on the page
3. Open ChatGPT, Claude, or any LLM
4. Paste the prompt + your exported JSON
5. The LLM will return structured JSON

#### Step 3: Import
1. Copy the structured JSON from the LLM
2. Paste it into the "Paste structured JSON" textarea
3. Enter the batch ID from step 1
4. Click **📥 Import Structured Deals**
5. Deals are now in your structured database!

### 5. Deal Database

1. Go to **Deal Database** page
2. Search by merchant name or offer title
3. Filter by category (dining, shopping, travel, etc.)
4. Export deals to JSON

### 6. Rate Deals

1. Go to **Rate Deals** page
2. See deals that haven't been rated yet
3. Click **Good**, **Mediocre**, or **Bad**
4. Optionally add a reason for your rating
5. Click **Skip** to move to next deal without rating

**Rating Criteria:**
- **Good**: High value discount, popular merchant, long validity, exclusive deal
- **Mediocre**: Average discount, common merchant, short validity
- **Bad**: Low value, restrictive terms, poor merchant

## Project Structure

```
deal-curation-platform/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── database.py          # SQLite models and connection
│   ├── models.py            # Pydantic schemas
│   ├── auth.py              # Authentication logic
│   ├── config.py            # Configuration settings
│   ├── scrapers/
│   │   ├── base.py          # Base scraper class
│   │   ├── alrajhi.py       # Alrajhi Bank scraper
│   │   ├── riyad.py         # Riyad Bank scraper
│   │   ├── sab.py           # SAB Bank scraper
│   │   └── runner.py        # Scraper execution service
│   ├── routers/
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── dashboard.py     # Dashboard API
│   │   ├── scrapers.py      # Scraper control API
│   │   ├── raw_deals.py     # Raw deals CRUD
│   │   ├── llm_processing.py # LLM workflow API
│   │   ├── structured_deals.py # Structured deals API
│   │   └── ratings.py       # Rating system API
│   └── services/
├── static/
│   ├── css/style.css        # Application styles
│   └── js/                  # Frontend JavaScript
├── templates/
│   ├── base.html            # Base template
│   ├── login.html           # Login page
│   ├── dashboard.html       # Dashboard page
│   ├── scrapers.html        # Scrapers management
│   ├── raw-deals.html       # Raw deals queue
│   ├── llm-processing.html  # LLM workflow
│   ├── structured-deals.html # Deal database
│   └── ratings.html         # Rating interface
├── data/
│   └── deals.db             # SQLite database (auto-created)
├── exports/                  # Export files directory
├── requirements.txt
└── README.md
```

## Database Schema

### Tables:

1. **users** - User accounts
2. **sources** - Deal sources (banks, Telegram channels)
3. **raw_deals** - Unstructured scraped data
4. **structured_deals** - Clean, processed deals
5. **ratings** - User quality ratings
6. **processing_batches** - LLM processing batches
7. **batch_deals** - Junction table for batches

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login and get JWT token

### Dashboard
- `GET /api/dashboard/stats` - Get dashboard statistics
- `GET /api/dashboard/sources-status` - Get sources status

### Scrapers
- `GET /api/sources` - List all sources
- `POST /api/sources/{id}/scrape` - Run scraper

### Raw Deals
- `GET /api/raw-deals` - List raw deals
- `POST /api/raw-deals/export` - Export deals to JSON
- `POST /api/raw-deals/{id}/duplicate` - Mark as duplicate

### LLM Processing
- `POST /api/llm/batches` - Create export batch
- `GET /api/llm/batches/{id}` - Get batch details
- `POST /api/llm/batches/{id}/import` - Import structured deals

### Structured Deals
- `GET /api/deals` - List structured deals
- `PUT /api/deals/{id}` - Update deal
- `DELETE /api/deals/{id}` - Delete deal
- `POST /api/deals/export` - Export deals

### Ratings
- `GET /api/ratings/pending` - Get deals needing rating
- `POST /api/ratings/deals/{id}/rate` - Submit rating
- `GET /api/ratings/stats` - Get rating statistics

## Adding New Scrapers

1. Create a new file in `app/scrapers/` (e.g., `newbank.py`)
2. Extend the `BaseScraper` class
3. Implement the `scrape()` method
4. Register the scraper in `app/scrapers/runner.py`
5. Add the source to `app/config.py` SOURCES dict

Example scraper:

```python
from .base import BaseScraper
import requests
from bs4 import BeautifulSoup

class NewBankScraper(BaseScraper):
    def __init__(self, source_id: int):
        super().__init__(
            source_id=source_id,
            source_name="New Bank",
            source_url="https://newbank.com/offers"
        )
    
    def scrape(self) -> List[Dict]:
        response = requests.get(self.source_url)
        soup = BeautifulSoup(response.content, 'lxml')
        deals = []
        
        # Parse deals here...
        
        return deals
```

## Configuration

Edit `app/config.py` to customize:
- Categories
- Discount types
- Quality scores
- LLM prompt template
- Source URLs

## Troubleshooting

### Scrapers not working?
- Check internet connection
- Some sites may block scraping - try adding delays
- Playwright browsers need to be installed: `playwright install`

### Login not working?
- Make sure database was created (check `data/deals.db` exists)
- Try deleting the database and restarting the app

### Import fails?
- Ensure JSON is valid (use a JSON validator)
- Check that all required fields are present
- Make sure batch ID matches

## Future Enhancements

- [ ] Telegram scraper integration
- [ ] OpenRouter API integration for automated LLM processing
- [ ] Machine learning model for auto-rating deals
- [ ] Email notifications for new deals
- [ ] Deal comparison feature
- [ ] Mobile responsive design improvements
- [ ] Export to CSV format
- [ ] Scheduled automatic scraping

## Support

For issues or feature requests, check the project documentation or create an issue in the project repository.

## License

This project is for personal use. Please respect the terms of service of the websites you scrape.

---

**Built with ❤️ for deal hunters**
