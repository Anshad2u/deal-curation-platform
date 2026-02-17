# Deployment Architecture

## Current Setup (Recommended)

### Backend (Linux Machine)
- FastAPI + SQLite + Scrapers
- Runs on: http://your-linux-ip:8000
- Keeps database persistent
- Scrapers work perfectly

### Frontend (Vercel)
- Static HTML/CSS/JS
- Connects to your Linux backend API
- Can be accessed from anywhere

## How It Works

```
┌─────────────────┐         API Requests        ┌──────────────────┐
│  Vercel         │  ─────────────────────────> │  Your Linux      │
│  (Frontend)     │  <─────────────────────────  │  (Backend)       │
│  HTML/CSS/JS    │                              │  FastAPI + SQLite│
└─────────────────┘                              └──────────────────┘
     Public URL                                        Local IP
  https://your-app.vercel.app                    http://your-ip:8000
```

## Steps

1. **Backend on Linux:**
   ```bash
   cd /home/anshad/deal-curation-platform
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

2. **Port Forward (if needed):**
   - Open port 8000 on your router
   - Or use ngrok for a public URL

3. **Frontend on Vercel:**
   - Deploy frontend/ folder to Vercel
   - Configure API_URL to point to your Linux machine

## Security Note

For production, you should:
1. Add CORS configuration
2. Use HTTPS (ngrok provides this)
3. Add API key authentication
4. Consider using a VPN instead of public exposure

## Alternative: Use ngrok (Easiest)

```bash
# Install ngrok
# Run backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# In another terminal
ngrok http 8000
```

This gives you a public HTTPS URL like:
`https://abc123.ngrok.io`

Point your Vercel frontend to this URL.
